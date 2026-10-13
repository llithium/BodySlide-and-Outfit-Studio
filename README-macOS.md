# BodySlide and Outfit Studio for macOS

This independent Apple Silicon build uses the Mac's OpenGL driver for the preview. It has been tested on an Apple M4 with a CBBE body and an enabled Skyrim Special Edition MO2 outfit. BC7 textures are decoded using the vendored [bcdec](https://github.com/iOrange/bcdec) library. The upstream project is [BodySlide and Outfit Studio](https://github.com/ousnius/BodySlide-and-Outfit-Studio).

## Download and connect to CrossOver

1. Download `BodySlide-macOS-arm64.zip` from this fork's macOS release and extract it to a writable folder. Keep the extracted apps and their sibling folders together.
2. Double-click **Set Up.command**. It finds CrossOver bottles, reads MO2's selected profile, and builds a native view of that profile's enabled BodySlide projects and game assets. If it finds more than one selected profile or game installation, it asks which to use.
3. Open **BodySlide macOS.app** or **Outfit Studio macOS.app**. The apps do not need CrossOver to render their windows. Keep the CrossOver drive mounted so they can read linked mod files.

The first opening may require **System Settings → Privacy & Security → Open Anyway** because this release is ad hoc signed, not Apple notarized. It does not require Homebrew or a local build. If `Set Up.command` is blocked, right-click it and choose **Open**.

Built meshes go to `BodySlide macOS Output` beside the apps. Inspect those files before adding them as an MO2 mod. The setup does not alter the CrossOver game Data, MO2 mods, or the existing `Bodyslide Output` mod. Run **Set Up.command** again after changing MO2's selected profile, enabled mods, or mod priority.

The profile view copies small project definitions and presets. Large `ShapeData` files, meshes, textures, and archives remain linked to their original locations. Editing linked ShapeData in Outfit Studio can change the original mod file. The game view covers loose meshes, textures, materials, and root-level archives; it does not reproduce every MO2 virtual filesystem behavior, so some assets may still be missing. The apps use absolute paths after setup, so rerun setup if you move the extracted folder.

For manual setup, run `python3 scripts/setup_macos.py --profile /path/to/modlist.txt --game-data /path/to/Skyrim/Data` from the extracted folder. The script also accepts `--app` to configure a different BodySlide app location.

## Build from source

Install build dependencies with Homebrew:

```sh
brew install cmake ninja wxwidgets glew pkgconf directx-headers git-lfs
git lfs install --local
git lfs pull
cmake -S . -B build/macos -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DBSOS_ENABLE_FBXSDK=OFF -DBSOS_ENABLE_BULLET=OFF -DBSOS_ENABLE_OPENEXR=OFF
cmake --build build/macos --target BodySlide OutfitStudio --parallel
python3 scripts/package_macos.py --build-dir build/macos \
  --app 'dist/BodySlide-macOS-arm64/BodySlide macOS.app'
python3 scripts/verify_macos_package.py dist/BodySlide-macOS-arm64
```

The FBX SDK, Bullet physics preview, and OpenEXR support are disabled. The macOS apps still support BodySlide outfit preview and mesh building.
