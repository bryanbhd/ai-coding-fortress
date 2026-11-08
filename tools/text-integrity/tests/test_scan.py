from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import scan


class ScanRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp_dir.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test"],
            check=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _track(self, name: str, content: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", name], check=True)

    def test_clean_text_has_no_signal(self) -> None:
        self._track("src/example.py", "print('ordinary text')\n")

        report = scan.scan_repository(self.root)

        self.assertEqual(report["files_scanned"], 1)
        self.assertEqual(report["files_with_signals"], [])
        self.assertEqual(report["high_risk_signal_count"], 0)
        self.assertEqual(report["keyed_model_watermarks"], "UNVERIFIABLE_WITHOUT_PROVIDER_KEYS")

    def test_high_risk_bidi_control_is_reported_without_character(self) -> None:
        self._track("src/example.py", "value = 'visible' " + chr(0x202E) + "\n")

        report = scan.scan_repository(self.root)
        completed = subprocess.run(
            [
                sys.executable,
                str(scan.HERE / "scan.py"),
                "--root",
                str(self.root),
                "--fail-high",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(report["high_risk_signal_count"], 1)
        finding = report["files_with_signals"][0]["channels"][0]
        self.assertEqual(finding["severity"], "HIGH")
        self.assertEqual(finding["codepoint"], "U+202E")
        self.assertNotIn(chr(0x202E), repr(report))
        self.assertEqual(completed.returncode, 1)
        self.assertNotIn(chr(0x202E), completed.stdout + completed.stderr)

    def test_untracked_files_are_not_scanned(self) -> None:
        (self.root / "untracked.py").write_text(chr(0x202E), encoding="utf-8")

        report = scan.scan_repository(self.root)

        self.assertEqual(report["files_scanned"], 0)
        self.assertEqual(report["high_risk_signal_count"], 0)

    def test_medium_signal_does_not_count_as_high(self) -> None:
        self._track("docs/example.md", "visible" + chr(0x200B) + "text\n")

        report = scan.scan_repository(self.root)
        completed = subprocess.run(
            [
                sys.executable,
                str(scan.HERE / "scan.py"),
                "--root",
                str(self.root),
                "--fail-high",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(report["high_risk_signal_count"], 0)
        self.assertEqual(
            report["files_with_signals"][0]["channels"][0]["severity"], "MEDIUM"
        )
        self.assertEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
