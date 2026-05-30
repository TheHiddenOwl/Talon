import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from jinja2 import Environment, PackageLoader, select_autoescape
from talon.storage.database import Finding

class ReportRenderer:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("talon", "reports/templates"),
            autoescape=select_autoescape(["html", "xml"])
        )

    def render_html(self, domain: str, findings: List[Finding]) -> str:
        template = self.env.get_template("report.html")
        return template.render(
            domain=domain,
            findings=findings,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
        )

    def render_json(self, findings: List[Finding]) -> str:
        data = []
        for f in findings:
            data.append({
                "collector": f.collector,
                "data": f.data,
                "created_at": f.created_at.isoformat(),
                "status_code": f.status_code,
                "duration_ms": f.duration_ms
            })
        return json.dumps(data, indent=2)

    def render_csv(self, findings: List[Finding], output_path: Path):
        if not findings:
            return

        keys = ["domain", "collector", "created_at", "status_code", "duration_ms", "data"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for finding in findings:
                writer.writerow({
                    "domain": finding.domain,
                    "collector": finding.collector,
                    "created_at": finding.created_at.isoformat(),
                    "status_code": finding.status_code,
                    "duration_ms": finding.duration_ms,
                    "data": json.dumps(finding.data)
                })
