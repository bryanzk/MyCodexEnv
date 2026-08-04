from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARE = ROOT / "scripts" / "compare_dhf_core_snapshot.py"
PACKET_VALIDATOR = ROOT / "scripts" / "validate_dhf_packet.py"
REQUIREMENTS_VALIDATOR = ROOT / "scripts" / "harness_requirements.py"
REQUIREMENTS = ROOT / "docs" / "plans" / "2026-06-15-dhf-independent-core-requirements.md"
SCHEMA = ROOT / "codex" / "runtime" / "dhf-packet.schema.json"
PIN = ROOT / "docs" / "dhf-core-pin.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DhfIndependentCorePrerequisitesTest(unittest.TestCase):
    def test_requirements_artifact_validates(self) -> None:
        result = run(str(REQUIREMENTS_VALIDATOR), "validate", str(REQUIREMENTS))
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(result.stdout.strip(), "valid")

    def test_packet_validator_accepts_schema_example(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "packet.json"
            packet.write_text(json.dumps(schema["examples"][0]), encoding="utf-8")
            result = run(str(PACKET_VALIDATOR), str(packet), "--schema", str(SCHEMA), "--json")

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "valid")
        self.assertTrue(payload["ok"])

    def test_packet_validator_rejects_invalid_and_sensitive_fields(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        invalid = dict(schema["examples"][0])
        invalid["phase"] = "finished"
        invalid["secret"] = "must-not-enter-a-packet"
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / "invalid.json"
            packet.write_text(json.dumps(invalid), encoding="utf-8")
            result = run(str(PACKET_VALIDATOR), str(packet), "--schema", str(SCHEMA), "--json")

        self.assertEqual(result.returncode, 1, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        paths = {item["path"] for item in payload["errors"]}
        self.assertIn("$.phase", paths)
        self.assertIn("$.secret", paths)
        self.assertNotIn("must-not-enter-a-packet", result.stdout)

    def test_snapshot_compare_match_drift_and_fail_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            consumer = tmp_path / "consumer"
            source.mkdir()
            consumer.mkdir()
            source_file = source / "runtime" / "contract.json"
            consumer_file = consumer / "codex" / "runtime" / "contract.json"
            source_file.parent.mkdir(parents=True)
            consumer_file.parent.mkdir(parents=True)
            content = b'{"version":1}\n'
            source_file.write_bytes(content)
            consumer_file.write_bytes(content)
            manifest = tmp_path / "pin.json"
            manifest.write_text(
                json.dumps(
                    {
                        "manifest_version": 1,
                        "consumer": "FixtureConsumer",
                        "pin": {
                            "kind": "bootstrap_snapshot",
                            "release": None,
                            "source_revision": None,
                            "packet_schema_version": 1,
                        },
                        "files": [
                            {
                                "source": "runtime/contract.json",
                                "consumer": "codex/runtime/contract.json",
                                "sha256": digest(content),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            matched = run(
                str(COMPARE),
                "--source", str(source),
                "--consumer", str(consumer),
                "--manifest", str(manifest),
                "--json",
            )
            self.assertEqual(matched.returncode, 0, matched.stderr or matched.stdout)
            self.assertEqual(json.loads(matched.stdout)["status"], "match")

            source_file.write_text('{"version":2}\n', encoding="utf-8")
            drifted = run(
                str(COMPARE),
                "--source", str(source),
                "--consumer", str(consumer),
                "--manifest", str(manifest),
                "--json",
            )
            self.assertEqual(drifted.returncode, 1, drifted.stderr or drifted.stdout)
            self.assertEqual(json.loads(drifted.stdout)["status"], "drift")

            source_file.unlink()
            failed_closed = run(
                str(COMPARE),
                "--source", str(source),
                "--consumer", str(consumer),
                "--manifest", str(manifest),
                "--json",
            )
            self.assertEqual(failed_closed.returncode, 2, failed_closed.stderr or failed_closed.stdout)
            failure = json.loads(failed_closed.stdout)
            self.assertEqual(failure["status"], "error")
            self.assertIn("missing_source", {item["code"] for item in failure["errors"]})

    def test_bootstrap_pin_matches_reference_consumer(self) -> None:
        manifest = json.loads(PIN.read_text(encoding="utf-8"))
        self.assertEqual(manifest["pin"]["kind"], "bootstrap_snapshot")
        self.assertIsNone(manifest["pin"]["release"])
        self.assertIsNone(manifest["pin"]["source_revision"])
        self.assertGreater(len(manifest["files"]), 0)

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            for item in manifest["files"]:
                consumer_file = ROOT / item["consumer"]
                content = consumer_file.read_bytes()
                self.assertEqual(digest(content), item["sha256"], item["consumer"])
                source_file = source / item["source"]
                source_file.parent.mkdir(parents=True, exist_ok=True)
                source_file.write_bytes(content)
            result = run(
                str(COMPARE),
                "--source", str(source),
                "--consumer", str(ROOT),
                "--manifest", str(PIN),
                "--json",
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "match")
        self.assertEqual(payload["summary"]["matched"], len(manifest["files"]))

    def test_snapshot_compare_rejects_unsafe_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            consumer = tmp_path / "consumer"
            source.mkdir()
            consumer.mkdir()
            manifest = tmp_path / "pin.json"
            manifest.write_text(
                json.dumps(
                    {
                        "manifest_version": 1,
                        "consumer": "FixtureConsumer",
                        "pin": {"kind": "release", "release": "dhf-core-v2026.08.01.1", "source_revision": "a" * 40, "packet_schema_version": 1},
                        "files": [{"source": "../escape", "consumer": "safe", "sha256": "0" * 64}],
                    }
                ),
                encoding="utf-8",
            )
            result = run(
                str(COMPARE),
                "--source", str(source),
                "--consumer", str(consumer),
                "--manifest", str(manifest),
                "--json",
            )

        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertIn("unsafe_path", {item["code"] for item in payload["errors"]})


if __name__ == "__main__":
    unittest.main()
