import asyncio
import logging
from typing import Optional, List, Tuple

import typer
from rich.console import Console
from rich.logging import RichHandler

from talon.collectors.archive import ArchiveCollector
from talon.collectors.certs import CertCollector
from talon.collectors.dns import DnsCollector
from talon.collectors.github import GithubCollector
from talon.collectors.shodan import ShodanCollector
from talon.collectors.whois import WhoisCollector
from talon.core.scheduler import TalonScheduler
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
        console.rule(f"[bold cyan]Talon scan: {domain}")

        tasks: List[Tuple[str, any]] = []
        if config.collectors.dns.enabled:
            tasks.append(("dns", DnsCollector(config.collectors.dns).collect(domain)))
        if config.collectors.whois_enabled:
            tasks.append(("whois", WhoisCollector().collect(domain)))
        if config.collectors.certs_enabled:
            tasks.append(("certs", CertCollector(client).collect(domain)))
        if config.collectors.archive_enabled:
            tasks.append(("archive", ArchiveCollector(client, config.collectors.archive_limit).collect(domain)))
        if config.collectors.shodan_enabled:
            tasks.append(("shodan", ShodanCollector(config.collectors.shodan_api_key.get_secret_value()).collect(domain)))
        if config.collectors.github_enabled:
            tasks.append(("github", GithubCollector(config.collectors.github_api_key.get_secret_value(), config.collectors.github_dorks).collect(domain)))

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
def config_check(
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom config YAML"),
):
    """Validate and display the resolved configuration."""
    config = TalonConfig.load_config(config_path)
    console.print(config.model_dump())

@app.command()
def report(
    domain: str = typer.Argument(..., help="Domain to generate report for"),
    fmt: str = typer.Option("html", "--format", "-f", help="Report format (html, json, csv)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate a summary report of findings."""
    asyncio.run(_run_report(domain, fmt, output))

async def _run_report(domain: str, fmt: str, output: Optional[str]):
    config = TalonConfig.load_config()
    db = Database(config.storage.db_path)
    await db.init()
    findings = await db.get_findings(domain)

    if not findings:
        console.print(f"[yellow]No findings found for {domain}[/]")
        return

    from talon.reports.renderer import ReportRenderer
    renderer = ReportRenderer()

    from pathlib import Path
    out_path = Path(output).resolve() if output else None

    try:
        if fmt == "html":
            content = renderer.render_html(domain, findings)
            if out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w") as f:
                    f.write(content)
                console.print(f"[green]Report exported to {out_path}[/]")
            else:
                console.print(content)
        elif fmt == "json":
            content = renderer.render_json(findings)
            if out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w") as f:
                    f.write(content)
                console.print(f"[green]Report exported to {out_path}[/]")
            else:
                console.print(content)
        elif fmt == "csv":
            if not out_path:
                console.print("[red]Error: --output is required for CSV format[/]")
                raise typer.Exit(1)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            renderer.render_csv(findings, out_path)
            console.print(f"[green]Report exported to {out_path}[/]")
        else:
            console.print(f"[red]Unsupported format: {fmt}[/]")
            raise typer.Exit(1)
    except OSError as e:
        console.print(f"[red]Failed to write report: {e}[/]")
        raise typer.Exit(1)

@app.command()
def export(
    domain: str = typer.Argument(..., help="Domain to export findings for"),
    fmt: str = typer.Option("json", "--format", "-f", help="Export format (json, csv)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export findings from the database."""
    asyncio.run(_run_export(domain, fmt, output))

async def _run_export(domain: str, fmt: str, output: Optional[str]):
    config = TalonConfig.load_config()
    db = Database(config.storage.db_path)
    await db.init()
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
        from pathlib import Path
        out_path = Path(output).resolve()
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                f.write(output_content)
            console.print(f"[green]Exported to {out_path}[/]")
        except OSError as e:
            console.print(f"[red]Failed to write output: {e}[/]")
            raise typer.Exit(1)
    else:
        console.print(output_content)

if __name__ == "__main__":
    app()
