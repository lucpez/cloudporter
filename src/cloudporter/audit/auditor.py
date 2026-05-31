from dataclasses import dataclass
from typing import Literal

from cloudporter.manifest.schema import ComputeResource, DatabaseResource, Manifest


@dataclass
class Finding:
    id: str
    level: Literal["error", "warning"]
    message: str
    detail: str
    resource: str | None = None
    resource_type: str | None = None


def audit(manifest: Manifest) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest.resources:
        findings.append(
            Finding(
                id="empty-manifest",
                level="error",
                message="empty manifest",
                detail="No resources are defined. There is nothing to deploy or audit.",
            )
        )
        return findings

    compute = [r for r in manifest.resources if isinstance(r, ComputeResource)]
    databases = [r for r in manifest.resources if isinstance(r, DatabaseResource)]

    if databases and not compute:
        for db in databases:
            findings.append(
                Finding(
                    id="database-without-compute-layer",
                    level="warning",
                    message="database without compute layer",
                    detail=(
                        f"{db.name} is a database resource but no compute resource "
                        "exists to act as an application tier. In a real deployment, "
                        "the database may be reachable without going through an "
                        "application layer."
                    ),
                    resource=db.name,
                    resource_type=db.type,
                )
            )

    return findings
