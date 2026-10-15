#!/usr/bin/env python3
"""Connect the downloaded macOS apps to a CrossOver MO2 profile."""

from __future__ import annotations

import argparse
from datetime import datetime
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from package_macos import active_mods, link_game_data, link_profile_projects, set_config_value


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


def find_output_mod(profile: Path, requested: Path | None) -> Path | None:
    enabled = [mod for mod in active_mods(profile) if mod.is_dir()]
    if requested:
        match = next((mod for mod in enabled if mod.resolve() == requested.resolve()), None)
        if match is None:
            raise ValueError(f"Output mod is not enabled in this profile: {requested}")
        return match
    preferred = [mod for mod in enabled if mod.name.casefold().replace(" ", "") == "bodyslideoutput"]
    if preferred:
        return preferred[0]
    with_choices = [
        mod for mod in enabled
        if (mod / "CalienteTools/BodySlide/BuildSelection.xml").is_file()
    ]
    if len(with_choices) > 1:
        names = ", ".join(mod.name for mod in with_choices)
        raise ValueError(f"Several enabled mods contain BodySlide choices ({names}). Use --output-mod.")
    return with_choices[0] if with_choices else None


def bind_state_file(app_file: Path, mo2_file: Path, backup: Path) -> None:
    if app_file.is_symlink() and app_file.resolve() == mo2_file.resolve():
        return
    mo2_file.parent.mkdir(parents=True, exist_ok=True)
    if not mo2_file.exists():
        shutil.copy2(app_file, mo2_file)
    if app_file.exists() or app_file.is_symlink():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(app_file, backup)
    replacement = app_file.with_name(app_file.name + ".new-link")
    replacement.symlink_to(mo2_file)
    os.replace(replacement, app_file)


def unbind_state_file(app_file: Path, backup: Path) -> None:
    if not app_file.is_symlink():
        return
    if not app_file.is_file():
        raise ValueError(f"Previous MO2 choice file is unavailable: {app_file}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(app_file, backup)
    replacement = app_file.with_name(app_file.name + ".local-copy")
    shutil.copy2(app_file, replacement)
    os.replace(replacement, app_file)


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


def configure(
    app: Path,
    profile: Path,
    game_data: Path,
    output_mod: Path | None = None,
    settings_dir: Path | None = None,
) -> None:
    if not (app / "Contents/MacOS/BodySlide").is_file():
        raise ValueError(f"BodySlide app is missing: {app}")
    studio = app.parent / "Outfit Studio macOS.app"
    if not (studio / "Contents/MacOS/OutfitStudio").is_file():
        raise ValueError(f"Outfit Studio app is missing: {studio}")
    projects = app.parent / f"{app.stem} Projects"
    data_view = app.parent / f"{app.stem} Data"
    output = app.parent / f"{app.stem} Output"
    connected_mod = find_output_mod(profile, output_mod)
    if connected_mod is None:
        output.mkdir(exist_ok=True)
        print("No enabled BodySlide output mod found; builds will stay in the separate output folder.")
    else:
        output = connected_mod
    roots, files = replace_view(projects, lambda staging: link_profile_projects(profile, staging))
    links = replace_view(data_view, lambda staging: link_game_data(profile, game_data, staging))

    packaged_settings = app.parent / "BodySlide macOS Settings"
    if not packaged_settings.is_dir():
        packaged_settings = app / "Contents/MacOS"  # Earlier releases kept settings inside the app.
    settings = settings_dir or Path.home() / "Library/Application Support/BodySlide macOS"
    settings.mkdir(parents=True, exist_ok=True)
    for name in ("Config.xml", "BodySlide.xml", "OutfitStudio.xml", "BuildSelection.xml"):
        destination = settings / name
        if not destination.exists() and not destination.is_symlink():
            source = packaged_settings / name
            if source.is_file():
                shutil.copy2(source, destination)
    config = settings / "Config.xml"
    backup_dir = app.parent / "BodySlide macOS Backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_dir.mkdir(parents=True)
    shutil.copy2(config, backup_dir / "Config.xml")
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
    if connected_mod:
        state = connected_mod / "CalienteTools/BodySlide"
        for name in ("BodySlide.xml", "BuildSelection.xml"):
            if (state / name).is_file():
                shutil.copy2(state / name, backup_dir / f"MO2-{name}")
            bind_state_file(settings / name, state / name, backup_dir / name)
    else:
        for name in ("BodySlide.xml", "BuildSelection.xml"):
            unbind_state_file(settings / name, backup_dir / name)
    print(f"Connected {profile.parent.name} to BodySlide and Outfit Studio.")
    print(f"Found {files} project files from {roots} mods and linked {links} game files.")
    print(f"Build choices and meshes use {output}" if connected_mod else f"Built meshes will go to {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[1] / "BodySlide macOS.app")
    parser.add_argument("--profile", type=Path, help="MO2 profile modlist.txt")
    parser.add_argument("--game-data", type=Path, help="Skyrim Special Edition Data folder")
    parser.add_argument("--output-mod", type=Path, help="Enabled MO2 mod to hold build choices and meshes")
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
    configure(args.app.resolve(), profile.resolve(), game_data.resolve(), args.output_mod)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
