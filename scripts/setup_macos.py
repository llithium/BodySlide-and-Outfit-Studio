#!/usr/bin/env python3
"""Connect the downloaded macOS apps to a CrossOver MO2 profile."""

import argparse
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from package_macos import link_game_data, link_profile_projects, set_config_value


def crossover_bottles() -> list[Path]:
    roots = [Path.home() / "Library/Application Support/CrossOver/Bottles"]
    roots.extend(volume / "CrossOver/Bottles" for volume in Path("/Volumes").glob("*"))
    return [bottle for root in roots if root.is_dir() for bottle in root.iterdir() if bottle.is_dir()]


def find_profiles() -> list[tuple[Path, Path, bool]]:
    choices: list[tuple[Path, Path, bool]] = []
    for bottle in crossover_bottles():
        users = bottle / "drive_c/users"
        if not users.is_dir():
            continue
        for user in users.iterdir():
            instances = user / "AppData/Local/ModOrganizer"
            if not instances.is_dir():
                continue
            for instance in instances.iterdir():
                selected = None
                settings = instance / "ModOrganizer.ini"
                if settings.is_file():
                    for line in settings.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                        if line.startswith("selected_profile=@ByteArray(") and line.endswith(")"):
                            selected = line.removeprefix("selected_profile=@ByteArray(")[:-1]
                            break
                profiles = instance / "profiles"
                if profiles.is_dir():
                    for profile in profiles.iterdir():
                        modlist = profile / "modlist.txt"
                        if modlist.is_file():
                            choices.append((modlist, bottle, profile.name == selected))
    return sorted(choices, key=lambda item: (not item[2], str(item[0])))


def choose(items: list[Path], description: str) -> Path:
    if not items:
        raise ValueError(f"No {description} found. Provide its path on the command line.")
    if len(items) == 1:
        return items[0]
    print(f"Choose {description}:")
    for number, item in enumerate(items, 1):
        print(f"  {number}. {item}")
    while True:
        answer = input("Number: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]


def game_data_dirs(bottle: Path) -> list[Path]:
    drive = bottle / "drive_c"
    candidates = [
        drive / "Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition/Data",
        drive / "Program Files/Steam/steamapps/common/Skyrim Special Edition/Data",
    ]
    return [path for path in candidates if path.is_dir()]


def replace_view(target: Path, build) -> int | tuple[int, int]:
    """Build beside the previous view, then replace it after a successful scan."""
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    backup = target.parent / f".{target.name}-previous"
    if backup.exists():
        shutil.rmtree(staging)
        raise ValueError(f"Previous setup backup exists: {backup}")
    try:
        result = build(staging)
        if target.exists():
            target.rename(backup)
        staging.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
        return result
    except Exception:
        if backup.exists() and not target.exists():
            backup.rename(target)
        if staging.exists():
            shutil.rmtree(staging)
        raise


def configure(app: Path, profile: Path, game_data: Path) -> None:
    if not (app / "Contents/MacOS/BodySlide").is_file():
        raise ValueError(f"BodySlide app is missing: {app}")
    studio = app.parent / "Outfit Studio macOS.app"
    if not (studio / "Contents/MacOS/OutfitStudio").is_file():
        raise ValueError(f"Outfit Studio app is missing: {studio}")
    projects = app.parent / f"{app.stem} Projects"
    data_view = app.parent / f"{app.stem} Data"
    output = app.parent / f"{app.stem} Output"
    output.mkdir(exist_ok=True)
    roots, files = replace_view(projects, lambda staging: link_profile_projects(profile, staging))
    links = replace_view(data_view, lambda staging: link_game_data(profile, game_data, staging))

    config = app / "Contents/MacOS/Config.xml"
    tree = ET.parse(config)
    root = tree.getroot()
    values = {
        "TargetGame": "4",
        "GameDataPath": str(data_view) + "/",
        "GameDataPaths/SkyrimSpecialEdition": str(data_view) + "/",
        "ProjectPath": str(projects),
        "OutputDataPath": str(output) + "/",
        "Anim/DefaultSkeletonReference": "res/skeleton_female_sse.nif",
        "Anim/SkeletonRootName": "NPC Root [Root]",
    }
    for key, value in values.items():
        set_config_value(root, key, value)
    temporary_config = config.with_suffix(".xml.tmp")
    tree.write(temporary_config, encoding="utf-8", xml_declaration=True)
    os.replace(temporary_config, config)
    print(f"Connected {profile.parent.name} to BodySlide and Outfit Studio.")
    print(f"Found {files} project files from {roots} mods and linked {links} game files.")
    print(f"Built meshes will go to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[1] / "BodySlide macOS.app")
    parser.add_argument("--profile", type=Path, help="MO2 profile modlist.txt")
    parser.add_argument("--game-data", type=Path, help="Skyrim Special Edition Data folder")
    args = parser.parse_args()
    profiles = find_profiles() if not args.profile else []
    selected = [item[0] for item in profiles if item[2]]
    profile = args.profile or (selected[0] if len(selected) == 1 else choose([item[0] for item in profiles], "CrossOver MO2 profile"))
    if not profile.is_file():
        parser.error(f"profile not found: {profile}")
    bottle = next((item[1] for item in profiles if item[0] == profile), None)
    if bottle is None:
        bottle = next((candidate for candidate in crossover_bottles() if candidate in profile.parents), None)
    game_data = args.game_data or choose(game_data_dirs(bottle) if bottle else [], "Skyrim Special Edition Data folder")
    if not game_data.is_dir():
        parser.error(f"game data not found: {game_data}")
    configure(args.app.resolve(), profile.resolve(), game_data.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
