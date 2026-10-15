Native Apple Silicon BodySlide and Outfit Studio with direct CrossOver/MO2 integration.

Version 0.2.3 fixes the first-run Setup dialog appearing after setup on downloaded apps. macOS can launch a quarantined app from a temporary translocation path, hiding settings stored beside it. BodySlide and Outfit Studio now read preferences and logs from `~/Library/Application Support/BodySlide macOS`; running **Set Up.command** copies existing settings and reconnects MO2 choices there. The app bundles remain signed.

Download `BodySlide-macOS-arm64.zip`, extract it to a writable folder, and run **Set Up.command**. Setup finds the selected Skyrim Special Edition MO2 profile. It reads enabled projects and textures from MO2 and, when an enabled `Bodyslide Output` mod exists, shares that mod's selected outfit, preset, zap choices, and build choices. Built meshes go directly into the same output mod. Setup saves rollback copies of the choice files and app configuration beside the apps.

Close Windows BodySlide before opening the native app so they do not write the shared choice files at the same time. Run setup again after changing the selected profile, enabled mods, or priority. If no enabled BodySlide output mod is found, the apps retain a separate review-output folder.

The apps contain their runtime libraries; Homebrew and a local build are not needed. This release is ad hoc signed and not Apple notarized, so macOS may require **System Settings → Privacy & Security → Open Anyway** on first launch.

See `README-macOS.md` in the download for details and limitations.
