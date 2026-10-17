"""Exercise native lookups against a Windows-authored MO2 choice file."""

import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "darwin", "macOS compiler and wxWidgets required")
class BuildSelectionPathTest(unittest.TestCase):
    def test_native_path_preserves_windows_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            xml = folder / "BuildSelection.xml"
            xml.write_text(
                '<BuildSelection><OutputChoice '
                'path="meshes\\actors\\character\\character assets\\femalebody" '
                'choice="CBBE 3BBB Body Amazing"/></BuildSelection>'
            )
            executable = folder / "build-selection-path-test"
            flags = shlex.split(subprocess.check_output(["wx-config", "--cxxflags"], text=True))
            subprocess.run(
                [
                    "clang++", "-std=c++17", f"-I{REPO / 'lib/TinyXML-2'}", *flags,
                    str(REPO / "tests/BuildSelectionPathTest.cpp"),
                    str(REPO / "src/components/BuildSelection.cpp"),
                    str(REPO / "src/utils/StringStuff.cpp"),
                    str(REPO / "lib/TinyXML-2/tinyxml2.cpp"),
                    "-o", str(executable),
                ],
                check=True,
            )
            subprocess.run([str(executable), str(xml)], check=True)


if __name__ == "__main__":
    unittest.main()
