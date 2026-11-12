"""Find orphaned and under-protected block volumes from an inventory export.

Block volumes keep billing after the instance they served is gone. This
module reads a static JSON inventory (state, attachment, size, age, backup
policy, tags) and flags volumes that are likely waste or risk. All analysis
is offline; no OCI calls.
"""

from dataclasses import dataclass

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# Illustrative unit price used ONLY to rank waste between candidates.
# Not a real OCI price; see README.
GB_MONTHLY_USD = 0.0255
ORPHAN_DAYS = 7


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    subject: str
    message: str


def _monthly_cost(size_gbs):
    return round(size_gbs * GB_MONTHLY_USD, 2)


def analyze_inventory(document):
    volumes = document.get("volumes")
    if not isinstance(volumes, list):
        raise ValueError("document must contain a top-level 'volumes' list")
    findings = []
    for vol in volumes:
        name = vol.get("name")
        if not name:
            raise ValueError("volume entry missing 'name'")
        state = vol.get("state", "AVAILABLE").upper()
        size = float(vol.get("size_gbs", 50))
        days = int(vol.get("days_in_state", 0))
        kind = vol.get("kind", "block").lower()

        if state == "AVAILABLE":
            if days >= ORPHAN_DAYS and kind != "boot":
                findings.append(Finding("ORPH001", "HIGH", name,
                    f"unattached {size:g} GB {kind} volume for {days} days; illustrative waste ${_monthly_cost(size):.2f}/month - back up and terminate, or reattach"))
            if kind == "boot":
                findings.append(Finding("ORPH002", "MEDIUM", name,
                    "detached boot volume kept after its instance; keep only if the image or data is still needed"))
        if not vol.get("backup_policy"):
            findings.append(Finding("ORPH003", "MEDIUM", name,
                "no backup policy assigned; a volume failure loses this data"))
        if not (vol.get("tags") or {}):
            findings.append(Finding("ORPH004", "LOW", name,
                "no tags; owner and environment unknown, which is how orphans accumulate"))
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.rule_id, f.subject, f.message))
