#!/usr/bin/env python3
"""Fail a release build if its apps still rely on Homebrew paths."""

import argparse
from pathlib import Path

from package_macos import linked_libraries


def verify(root: Path) -> None:
    for app_name, executable in (
        ("BodySlide macOS.app", "BodySlide"),
        ("Outfit Studio macOS.app", "OutfitStudio"),
    ):
        app = root / app_name
        macos = app / "Contents/MacOS"
        frameworks = app / "Contents/Frameworks"
        binary = macos / executable
        assert binary.is_file(), binary
        assert (macos / "res/skeleton_female_sse.nif").stat().st_size > 1000
        for file in (binary, *frameworks.glob("*.dylib")):
            for library in linked_libraries(file):
                assert not library.startswith(("/opt/homebrew/", "/usr/local/")), (file, library)
                if library.startswith("@executable_path/../Frameworks/") or library.startswith("@loader_path/"):
                    assert (frameworks / Path(library).name).is_file(), (file, library)
    assert (root / "Set Up.command").is_file()
    assert (root / "scripts/setup_macos.py").is_file()
    print("Both apps contain their runtime libraries and setup files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    verify(parser.parse_args().root)
