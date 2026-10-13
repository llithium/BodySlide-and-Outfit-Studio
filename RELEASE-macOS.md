Native Apple Silicon preview and mesh building for BodySlide and Outfit Studio. This is an independent macOS build of the upstream project.

Download `BodySlide-macOS-arm64.zip`, extract it to a writable folder, and run **Set Up.command**. The setup finds the selected Skyrim Special Edition MO2 profile in CrossOver and connects the apps to its enabled outfits and textures. Open **BodySlide macOS.app** afterward.

The apps contain their runtime libraries; Homebrew and a local build are not needed. The release is ad hoc signed and not Apple notarized. macOS may require opening the apps through **System Settings → Privacy & Security → Open Anyway** on first launch.

Built meshes are saved in `BodySlide macOS Output` beside the apps. Review them before adding them to MO2. Run setup again after changing the selected MO2 profile or mod order. Keep the CrossOver drive mounted while using the apps.

See `README-macOS.md` in the download for details and limitations.
