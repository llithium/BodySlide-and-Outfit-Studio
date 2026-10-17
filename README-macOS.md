# BodySlide and Outfit Studio for macOS

This independent Apple Silicon build uses the Mac's OpenGL driver for the preview. It has been tested on an Apple M4 with a CBBE body and an enabled Skyrim Special Edition MO2 outfit. BC7 textures are decoded using the vendored [bcdec](https://github.com/iOrange/bcdec) library. The upstream project is [BodySlide and Outfit Studio](https://github.com/ousnius/BodySlide-and-Outfit-Studio).

## Download and connect to CrossOver

1. Download `BodySlide-macOS-arm64.zip` from this fork's macOS release and extract it to a writable folder. Keep the extracted apps and their sibling folders together.
2. Double-click **Set Up.command**. It finds CrossOver bottles, reads MO2's selected profile, and builds a native view of that profile's enabled BodySlide projects and game assets. If it finds more than one selected profile or game installation, it asks which to use.
3. Open **BodySlide macOS.app** or **Outfit Studio macOS.app**. The apps do not need CrossOver to render their windows. Keep the CrossOver drive mounted so they can read linked mod files.

The first opening may require **System Settings → Privacy & Security → Open Anyway** because this release is ad hoc signed, not Apple notarized. It does not require Homebrew or a local build. If `Set Up.command` is blocked, right-click it and choose **Open**.

When the selected MO2 profile has an enabled `Bodyslide Output` mod, setup connects the app's selected outfit, preset, zap choices, and output choices directly to that mod's `BodySlide.xml` and `BuildSelection.xml`. Builds write meshes directly into that same MO2 mod. Saved output choices from Windows BodySlide also work in the native app. Batch Build starts with visible outfits checked, then clears competing variants according to those saved choices, matching Windows BodySlide. A `BuildSelection - Selected` group remains available as a filter, but does not silently change the default checks. App preferences and logs live in `~/Library/Application Support/BodySlide macOS`, which remains available even when macOS launches the downloaded app from a temporary translocation path. Setup saves rollback copies of the app configuration and both MO2 choice files in `BodySlide macOS Backups` beside the apps. Close the Windows BodySlide before opening the native one so the two processes do not overwrite each other's choices.

If no enabled output mod is found, builds stay in `BodySlide macOS Output` beside the apps and setup reports this. You can select an enabled output mod explicitly with `--output-mod`. Run **Set Up.command** again after changing MO2's selected profile, enabled mods, or mod priority. Setup does not alter the CrossOver game Data or existing generated meshes.

The profile view links project definitions, presets, and ShapeData to their original MO2 folders, so edits to those files can change the original mod. The game view links loose meshes, textures, materials, and root-level archives; it does not reproduce every MO2 virtual filesystem behavior, so some assets may still be missing. New presets saved into the merged project view are local until moved into an MO2 mod. The apps use absolute paths after setup, so rerun setup if you move the extracted folder.

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
