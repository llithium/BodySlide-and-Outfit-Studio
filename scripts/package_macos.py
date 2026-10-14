#!/usr/bin/env python3
"""Package local macOS binaries and, optionally, a read-through MO2 project view."""

import argparse
import os
import plistlib
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator


PROJECT_DIRS = (
    "SliderSets",
    "ShapeData",
    "SliderPresets",
    "SliderGroups",
    "SliderCategories",
    "RefTemplates",
    "PoseData",
)
LOOSE_DATA_DIRS = ("textures", "meshes", "materials")
MACOS_VERSION = "0.2.0"


def linked_libraries(binary: Path) -> list[str]:
    output = subprocess.check_output(("otool", "-L", str(binary)), text=True)
    return [line.strip().split(" (")[0] for line in output.splitlines()[1:]]


def bundle_libraries(app: Path) -> None:
    """Copy non-system Mach-O dependencies and point every load at the bundle."""
    macos = app / "Contents" / "MacOS"
    frameworks = app / "Contents" / "Frameworks"
    frameworks.mkdir()
    binaries = [path for path in macos.iterdir() if path.is_file() and os.access(path, os.X_OK)]
    pending = binaries.copy()
    libraries: dict[Path, Path] = {}
    origins = {binary: binary for binary in binaries}
    dependencies: dict[Path, list[tuple[str, str | None]]] = {}
    while pending:
        binary = pending.pop()
        dependencies[binary] = []
        for dependency in linked_libraries(binary):
            if dependency.startswith(("/System/", "/usr/lib/")):
                dependencies[binary].append((dependency, None))
                continue
            if dependency.startswith("/"):
                source = Path(dependency)
            elif dependency.startswith(("@rpath/", "@loader_path/")):
                source = origins[binary].parent / Path(dependency).name
            else:
                raise ValueError(f"unresolved library in {binary}: {dependency}")
            if not source.is_file():
                raise FileNotFoundError(source)
            resolved = source.resolve()
            target = libraries.get(resolved)
            if target is None:
                target = frameworks / source.name
                if target.exists():
                    raise ValueError(f"conflicting libraries named {source.name}")
                shutil.copy2(source, target)
                target.chmod(target.stat().st_mode | stat.S_IWUSR)
                libraries[resolved] = target
                origins[target] = source
                pending.append(target)
            dependencies[binary].append((dependency, target.name))

    for binary, original_paths in dependencies.items():
        if binary.parent == frameworks:
            subprocess.run(("install_name_tool", "-id", f"@loader_path/{binary.name}", str(binary)), check=True)
        for index, (original, library_name) in enumerate(original_paths):
            if library_name is None or (binary.parent == frameworks and index == 0):
                continue
            replacement = (
                f"@loader_path/{library_name}"
                if binary.parent == frameworks
                else f"@executable_path/../Frameworks/{library_name}"
            )
            subprocess.run(("install_name_tool", "-change", original, replacement, str(binary)), check=True)
        # Sign the Mach-O outside the .app so codesign does not inspect game resources.
        with tempfile.TemporaryDirectory() as temporary:
            detached = Path(temporary) / binary.name
            shutil.copy2(binary, detached)
            subprocess.run(("codesign", "--force", "--sign", "-", str(detached)), check=True, stdout=subprocess.DEVNULL)
            shutil.copy2(detached, binary)
    print(f"Bundled {len(libraries)} libraries into {app}")


def active_mods(modlist: Path) -> Iterator[Path]:
    mods = modlist.parents[2] / "mods"
    for line in modlist.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("+"):
            yield mods / line[1:]


def link_file(source: Path, target: Path) -> bool:
    if target.exists() or target.is_symlink():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source)
    return True


def link_profile_projects(modlist: Path, destination: Path) -> tuple[int, int]:
    roots = 0
    files = 0
    # MO2 lists the highest priority mod first. Keep its file on collisions.
    for mod in active_mods(modlist):
        root = mod / "CalienteTools" / "BodySlide"
        if not root.is_dir():
            continue
        roots += 1
        for dirname in PROJECT_DIRS:
            source = root / dirname
            if not source.is_dir():
                continue
            for file in source.rglob("*"):
                if not file.is_file():
                    continue
                target = destination / dirname / file.relative_to(source)
                if target.exists() or target.is_symlink():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(file)
                files += 1
    return roots, files


def link_game_data(modlist: Path, game_data: Path, destination: Path) -> int:
    links = 0
    for mod in active_mods(modlist):
        for dirname in LOOSE_DATA_DIRS:
            source = mod / dirname
            if source.is_dir():
                for file in source.rglob("*"):
                    if file.is_file():
                        links += link_file(file, destination / dirname / file.relative_to(source))
        for pattern in ("*.bsa", "*.ba2"):
            for archive in mod.glob(pattern):
                links += link_file(archive, destination / archive.name)
    for entry in game_data.iterdir():
        if entry.name.lower() in LOOSE_DATA_DIRS and entry.is_dir():
            for file in entry.rglob("*"):
                if file.is_file():
                    links += link_file(file, destination / entry.name / file.relative_to(entry))
        elif not (destination / entry.name).exists():
            links += link_file(entry, destination / entry.name)
    return links


def set_config_value(root: ET.Element, key: str, value: str) -> None:
    element = root.find(key)
    if element is None:
        raise ValueError(f"Config.xml is missing {key}")
    element.text = value


def write_info_plist(app: Path, executable: str, name: str, identifier: str) -> None:
    info = {
        "CFBundleExecutable": executable,
        "CFBundleIdentifier": identifier,
        "CFBundleName": name,
        "CFBundleDisplayName": name,
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1",
        "CFBundleShortVersionString": MACOS_VERSION,
        "NSHighResolutionCapable": True,
    }
    with (app / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump(info, stream)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--profile", type=Path, help="MO2 profile modlist.txt")
    parser.add_argument("--game-data", type=Path, help="Skyrim Special Edition Data directory")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    app = args.app.resolve()
    build = args.build_dir.resolve()
    if app.exists():
        parser.error(f"destination already exists: {app}")
    for name in ("BodySlide", "OutfitStudio"):
        if not (build / name).is_file():
            parser.error(f"build is missing {name}: {build}")
    if args.profile and not args.profile.is_file():
        parser.error(f"profile not found: {args.profile}")
    if args.game_data and not args.game_data.is_dir():
        parser.error(f"game data directory not found: {args.game_data}")
    if bool(args.profile) != bool(args.game_data):
        parser.error("--profile and --game-data must be provided together")

    profile = args.profile.resolve() if args.profile else None
    game_data = args.game_data.resolve() if args.game_data else None
    projects = app.parent / f"{app.stem} Projects"
    data_view = app.parent / f"{app.stem} Data"
    studio_app = app.parent / "Outfit Studio macOS.app"
    if studio_app.exists():
        parser.error(f"destination already exists: {studio_app}")
    if profile and projects.exists():
        parser.error(f"project view already exists: {projects}")
    if profile and game_data and data_view.exists():
        parser.error(f"game data view already exists: {data_view}")

    macos = app / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    for name in ("BodySlide", "OutfitStudio"):
        shutil.copy2(build / name, macos / name)
    for name in ("Config.xml", "BodySlide.xml", "OutfitStudio.xml", "BuildSelection.xml", "RefTemplates.xml"):
        shutil.copy2(repo / name, macos / name)
    output = app.parent / f"{app.stem} Output"
    output.mkdir(exist_ok=True)
    config = macos / "Config.xml"
    tree = ET.parse(config)
    set_config_value(tree.getroot(), "OutputDataPath", str(output) + "/")
    tree.write(config, encoding="utf-8", xml_declaration=True)
    for name in ("res", "lang"):
        shutil.copytree(repo / name, macos / name)

    write_info_plist(app, "BodySlide", "BodySlide macOS", "org.ousnius.bodyslide.mac-build")

    studio_macos = studio_app / "Contents" / "MacOS"
    studio_macos.mkdir(parents=True)
    shutil.copy2(build / "OutfitStudio", studio_macos / "OutfitStudio")
    shutil.copy2(repo / "OutfitStudio.xml", studio_macos / "OutfitStudio.xml")
    for name in ("Config.xml", "RefTemplates.xml", "res", "lang"):
        source = macos / name
        (studio_macos / name).symlink_to(os.path.relpath(source, studio_macos))
    write_info_plist(studio_app, "OutfitStudio", "Outfit Studio macOS", "org.ousnius.outfitstudio.mac-build")
    bundle_libraries(app)
    bundle_libraries(studio_app)
    release_scripts = app.parent / "scripts"
    release_scripts.mkdir(exist_ok=True)
    for name in ("package_macos.py", "setup_macos.py"):
        shutil.copy2(repo / "scripts" / name, release_scripts / name)
    shutil.copy2(repo / "scripts/Set Up.command", app.parent / "Set Up.command")
    (app.parent / "Set Up.command").chmod(0o755)
    shutil.copy2(repo / "README-macOS.md", app.parent / "README-macOS.md")
    shutil.copy2(repo / "LICENSE", app.parent / "LICENSE")
    if profile and game_data:
        from setup_macos import configure
        configure(app, profile, game_data)
    else:
        print(f"Build output is isolated in {output} until setup is run")
    print(f"Packaged {app}")
    print(f"Packaged {studio_app}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
