"""Run with python3 -m unittest discover -s test/Providers -v."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ProviderTest(unittest.TestCase):
    def test_generated_born_and_virtual_with_fake_provider(self):
        with tempfile.TemporaryDirectory(prefix="madisqe-provider-") as directory:
            workspace = Path(directory)
            for name in ("tpl", "src", "input"):
                (workspace / name).symlink_to(ROOT / name, target_is_directory=True)
            config = workspace / "process.input"
            config.write_text(
                "INITIAL STATE = p,p\n"
                "FINAL STATE = Z,jb,jb\n"
                "RADIATIVE = j\n"
                "MODEL FILE = StandardModel\n"
                f"PATH = {workspace}\n"
                "STAGE = 3\n"
                "VERBOSE = 0\n"
            )
            generated = self.run_checked(
                [sys.executable, str(ROOT / "Madisqe.py"), "--core-only", str(config)],
                workspace,
            )
            process = workspace / "pp_Zjbjbj"
            channel = process / "Virtual" / "gg_Zbbbar"
            self.assertTrue((process / "Code" / "Real.h").is_file(), generated.stdout)
            self.assertTrue((process / "Code" / "Virtual.h").is_file())
            self.assertFalse((process / "NLOX_Process").exists())
            self.assertFalse((process / "Code" / "NLOX_OLP.h").exists())
            self.assertFalse((process / "Code" / "RECOLA_OLP.h").exists())

            compiler = os.environ.get("CXX", "g++")
            if shutil.which(compiler) is None:
                self.skipTest(f"C++ compiler {compiler!r} is unavailable")
            executable = workspace / "fixed-point"
            self.run_checked(
                [
                    compiler, "-std=gnu++11",
                    "-I", str(process / "Code"),
                    "-I", str(ROOT / "src"),
                    "-I", str(channel),
                    str(Path(__file__).with_name("FixedPoint.cpp")),
                    str(channel / "gg_Zbbbar_Virtual.cpp"),
                    str(process / "Model.cpp"),
                    "-o", str(executable),
                ],
                workspace,
            )
            self.run_checked([str(executable)], workspace)

    def run_checked(self, command, cwd):
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result
