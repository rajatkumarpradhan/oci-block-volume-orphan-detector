# oci-block-volume-orphan-detector

**Custom portfolio tool (no built-in OCI services wired in).** Offline detector that reads a synthetic OCI Block Volume inventory export and flags volumes that are likely waste or risk.

Problem it solves: block volumes keep billing after the instance they served is terminated. This tool turns an inventory snapshot into a ranked clean-up list - orphans to terminate, detached boot volumes to review, volumes without backups, untagged volumes - locally and in CI, without touching a tenancy.

## What it is

- Reads a static JSON inventory: per-volume kind (block/boot), state, size, days in current state, backup policy, tags.
- Four rules (ORPH001-ORPH004) with severity-ranked findings and an exit code suitable for CI gates.
- Runs 100% locally. No OCI SDK, no credentials, no network calls.
- 15 unit tests, all executed locally and in CI on Python 3.10/3.11/3.12.

## What it is NOT (honest limits)

- The waste figures use one **illustrative unit price** ($0.0255/GB/month) purely to rank candidates. It is not OCI pricing; performance tiers, VPUs and regional pricing are not modeled.
- The input schema is a simplified inventory, not the OCI Block Volume API response; it does not enumerate volumes from OCI. "Days in state" is an input field, not derived from live state history.
- A volume detached for 7+ days is a *candidate*, not proof of waste - planned maintenance and restore staging look identical in an inventory snapshot.
- Cross-region replicas and volume groups are not modeled.

## Rules

| Rule | Severity | Finding |
| --- | --- | --- |
| ORPH001 | HIGH | Block volume unattached for 7+ days; illustrative monthly waste |
| ORPH002 | MEDIUM | Detached boot volume kept after its instance |
| ORPH003 | MEDIUM | No backup policy assigned |
| ORPH004 | LOW | No tags; owner and environment unknown |

Exit code 2 when any ORPH001 fires; 1 on unreadable or malformed input; 0 otherwise.

## Run

Requires Python 3.10+, no third-party dependencies.

```sh
PYTHONPATH=src python3 -m oci_block_volume_orphan_detector samples/messy-inventory.json
PYTHONPATH=src python3 -m oci_block_volume_orphan_detector samples/tidy-inventory.json
```

Or the end-to-end demo:

```sh
sh demo.sh
```

Expected demo output: the messy inventory flags the 500 GB volume detached for 45 days (HIGH, ~$12.75/month illustrative), the detached boot volume, two missing backup policies and the untagged orphan, and exits 2; the tidy inventory reports zero findings and exits 0.

## Test

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
