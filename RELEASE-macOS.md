Native Apple Silicon BodySlide and Outfit Studio with direct CrossOver/MO2 integration.

Version 0.2.5 makes Batch Build's initial checks match Windows BodySlide: visible outfits start checked, while competing variants are cleared using saved output choices. The `BuildSelection - Selected` group remains available as a filter, but no longer overrides the initial checks. The Select None, Select All, and Invert Selection menu now belongs to the batch dialog, so its commands work while that dialog is open. Run **Set Up.command** after updating to remove the older selection override from the app's settings.

Download `BodySlide-macOS-arm64.zip`, extract it to a writable folder, and run **Set Up.command**. Setup finds the selected Skyrim Special Edition MO2 profile. It reads enabled projects and textures from MO2 and, when an enabled `Bodyslide Output` mod exists, shares that mod's selected outfit, preset, zap choices, and build choices. Built meshes go directly into the same output mod. Setup saves rollback copies of the choice files and app configuration beside the apps.

Close Windows BodySlide before opening the native app so they do not write the shared choice files at the same time. Run setup again after changing the selected profile, enabled mods, or priority. If no enabled BodySlide output mod is found, the apps retain a separate review-output folder.

The apps contain their runtime libraries; Homebrew and a local build are not needed. This release is ad hoc signed and not Apple notarized, so macOS may require **System Settings → Privacy & Security → Open Anyway** on first launch.

See `README-macOS.md` in the download for details and limitations.
