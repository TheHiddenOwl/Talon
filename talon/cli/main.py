import asyncio
import logging
from typing import Optional, List, Tuple

import typer
from rich.console import Console
from rich.logging import RichHandler

from talon.collectors.archive import ArchiveCollector
from talon.collectors.certs import CertCollector
from talon.collectors.dns import DnsCollector
from talon.collectors.whois import WhoisCollector
from talon.config import TalonConfig
from talon.storage.database import Database
from talon.transport.client import StealthClient
from talon.collectors.base import CollectorResult

app = typer.Typer(help="Talon — Stealthy async OSINT framework")
collect_app = typer.Typer(help="Run individual collectors")
app.add_typer(collect_app, name="collect")

console = Console()

def setup_logging(level: str, log_file: Optional[str]):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True), logging.FileHandler(log_file) if log_file else logging.NullHandler()]
    )

def check_scope(confirm_scope: bool):
    if not confirm_scope:
        console.print("[bold red]Error:[/] You must pass --confirm-scope to acknowledge you have authorization to scan this target.")
        raise typer.Exit(1)

async def _save_result(db: Database, domain: str, collector_name: str, result: CollectorResult):
    await db.save(
        domain=domain,
        collector=collector_name,
        data=result.data,
        raw_response=result.raw_response,
        status_code=result.status_code,
        duration_ms=result.duration_ms
    )

@app.command()
def scan(
    domain: str = typer.Argument(..., help="Target domain to scan"),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom config YAML"),
    confirm_scope: bool = typer.Option(False, "--confirm-scope", help="Confirm you have permission to scan this domain"),
):
    """Perform a full recon scan of a domain."""
    check_scope(confirm_scope)
    asyncio.run(_run_scan(domain, config_path))

async def _run_scan(domain: str, config_path: Optional[str]):
    config = TalonConfig.load_config(config_path)
    setup_logging(config.logging.level, config.logging.file)

    db = Database(config.storage.db_path)
    await db.init()

    async with StealthClient(config) as client:
        cfg = config.collectors
        console.rule(f"[bold cyan]Talon scan: {domain}")

        tasks: List[Tuple[str, any]] = []
        if cfg.dns.enabled:
            tasks.append(("dns", DnsCollector(cfg.dns).collect(domain)))
        if cfg.whois_enabled:
            tasks.append(("whois", WhoisCollector().collect(domain)))
        if cfg.certs_enabled:
            tasks.append(("certs", CertCollector(client).collect(domain)))
        if cfg.archive_enabled:
            tasks.append(("archive", ArchiveCollector(client, cfg.archive_limit).collect(domain)))

        for name, coro in tasks:
            with console.status(f"[cyan]Running {name} collector..."):
                result: CollectorResult = await coro
                await _save_result(db, domain, name, result)

            count = len(result.data) if isinstance(result.data, list) else 1
            console.print(f"[green]✓[/] {name}: {count} findings")

    console.rule("[bold green]Scan complete")

@collect_app.command("dns")
def collect_dns(
    domain: str = typer.Argument(..., help="Target domain"),
    confirm_scope: bool = typer.Option(False, "--confirm-scope", help="Confirm authorization"),
):
    check_scope(confirm_scope)
    async def run():
        config = TalonConfig.load_config()
        db = Database(config.storage.db_path)
        await db.init()
        collector = DnsCollector(config.collectors.dns)
        result = await collector.collect(domain)
        await _save_result(db, domain, "dns", result)
        console.print(result.data)
    asyncio.run(run())

@collect_app.command("whois")
def collect_whois(
    domain: str = typer.Argument(..., help="Target domain"),
    confirm_scope: bool = typer.Option(False, "--confirm-scope", help="Confirm authorization"),
):
    check_scope(confirm_scope)
    async def run():
        config = TalonConfig.load_config()
        db = Database(config.storage.db_path)
        await db.init()
        collector = WhoisCollector()
        result = await collector.collect(domain)
        await _save_result(db, domain, "whois", result)
        console.print(result.data)
    asyncio.run(run())

@collect_app.command("certs")
def collect_certs(
    domain: str = typer.Argument(..., help="Target domain"),
    confirm_scope: bool = typer.Option(False, "--confirm-scope", help="Confirm authorization"),
):
    check_scope(confirm_scope)
    async def run():
        config = TalonConfig.load_config()
        db = Database(config.storage.db_path)
        await db.init()
        async with StealthClient(config) as client:
            collector = CertCollector(client)
            result = await collector.collect(domain)
            await _save_result(db, domain, "certs", result)
            console.print(result.data)
    asyncio.run(run())

@collect_app.command("archive")
def collect_archive(
    domain: str = typer.Argument(..., help="Target domain"),
    confirm_scope: bool = typer.Option(False, "--confirm-scope", help="Confirm authorization"),
):
    check_scope(confirm_scope)
    async def run():
        config = TalonConfig.load_config()
        db = Database(config.storage.db_path)
        await db.init()
        async with StealthClient(config) as client:
            collector = ArchiveCollector(client, config.collectors.archive_limit)
            result = await collector.collect(domain)
            await _save_result(db, domain, "archive", result)
            console.print(result.data)
    asyncio.run(run())

@app.command()
def export(
    domain: str = typer.Argument(..., help="Domain to export findings for"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, csv)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export findings from the database."""
    asyncio.run(_run_export(domain, format, output))

async def _run_export(domain: str, format: str, output: Optional[str]):
    config = TalonConfig.load_config()
    db = Database(config.storage.db_path)
    findings = await db.get_findings(domain)

    if not findings:
        console.print(f"[yellow]No findings found for {domain}[/]")
        return

    import json
    data = []
    for f in findings:
        data.append({
            "collector": f.collector,
            "data": f.data,
            "created_at": f.created_at.isoformat(),
            "status_code": f.status_code,
            "duration_ms": f.duration_ms
        })

    output_content = json.dumps(data, indent=2)
    if output:
        with open(output, "w") as f:
            f.write(output_content)
        console.print(f"[green]Exported to {output}[/]")
    else:
        console.print(output_content)

if __name__ == "__main__":
    app()
