import unittest

from oci_block_volume_orphan_detector.orphan import analyze_inventory


def vol(name, kind="block", state="AVAILABLE", size=100, days=30, backup="gold", tags=None):
    return {"name": name, "kind": kind, "state": state, "size_gbs": size,
            "days_in_state": days, "backup_policy": backup, "tags": tags if tags is not None else {"env": "dev"}}


def ids(findings):
    return {f.rule_id for f in findings}


class TestOrphan(unittest.TestCase):
    def test_orph001_old_unattached_block_volume(self):
        findings = analyze_inventory({"volumes": [vol("v", size=200)]})
        orph001 = [f for f in findings if f.rule_id == "ORPH001"]
        self.assertEqual(len(orph001), 1)
        self.assertEqual(orph001[0].severity, "HIGH")
        self.assertIn("$5.10", orph001[0].message)  # 200 * 0.0255

    def test_orph001_needs_seven_days(self):
        self.assertNotIn("ORPH001", ids(analyze_inventory({"volumes": [vol("v", days=6)]})))

    def test_orph001_not_for_boot_volumes(self):
        self.assertNotIn("ORPH001", ids(analyze_inventory({"volumes": [vol("v", kind="boot", days=30)]})))

    def test_orph002_detached_boot_volume(self):
        self.assertIn("ORPH002", ids(analyze_inventory({"volumes": [vol("v", kind="boot", days=30)]})))

    def test_orph002_not_for_attached_boot(self):
        self.assertNotIn("ORPH002", ids(analyze_inventory({"volumes": [vol("v", kind="boot", state="ATTACHED")]})))

    def test_orph003_missing_backup_policy(self):
        self.assertIn("ORPH003", ids(analyze_inventory({"volumes": [vol("v", backup=None, state="ATTACHED", days=1)]})))

    def test_orph004_missing_tags(self):
        self.assertIn("ORPH004", ids(analyze_inventory({"volumes": [vol("v", tags={}, state="ATTACHED", days=1)]})))

    def test_clean_volume_has_no_findings(self):
        self.assertEqual(analyze_inventory({"volumes": [
            vol("v", state="ATTACHED", days=100, backup="gold", tags={"env": "prod"})]}), [])

    def test_findings_sorted_high_first(self):
        findings = analyze_inventory({"volumes": [
            vol("tidy", state="ATTACHED", days=1, backup=None, tags={}),
            vol("orphan", size=100)]})
        self.assertEqual(findings[0].severity, "HIGH")

    def test_missing_volumes_list_rejected(self):
        with self.assertRaises(ValueError):
            analyze_inventory({"items": []})

    def test_volume_missing_name_rejected(self):
        with self.assertRaises(ValueError):
            analyze_inventory({"volumes": [{"state": "AVAILABLE"}]})


if __name__ == "__main__":
    unittest.main()
