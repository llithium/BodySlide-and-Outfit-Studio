"""Focused MO2 integration checks for the downloaded macOS apps."""

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from setup_macos import configure  # noqa: E402


class MO2SetupTest(unittest.TestCase):
    def test_uses_active_mo2_choices_and_output_mod(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            instance = root / "ModOrganizer/Skyrim Special Edition"
            profile = instance / "profiles/Test/modlist.txt"
            profile.parent.mkdir(parents=True)
            profile.write_text("+Bodyslide Output\n+Outfit Mod\n")
            mo2 = instance / "mods/Bodyslide Output"
            state = mo2 / "CalienteTools/BodySlide"
            state.mkdir(parents=True)
            (state / "BuildSelection.xml").write_text(
                '<BuildSelection><ZapChoice project="Test" zap="Gloves" choice="true"/>'
                '<OutputChoice path="meshes\\test" choice="Test"/></BuildSelection>'
            )
            (state / "BodySlide.xml").write_text(
                "<BodySlideConfig><SelectedOutfit>Test</SelectedOutfit></BodySlideConfig>"
            )
            project = instance / "mods/Outfit Mod/CalienteTools/BodySlide/SliderSets/Test.osp"
            project.parent.mkdir(parents=True)
            project.write_text("<SliderSetInfo/>")
            game_data = root / "Skyrim/Data"
            game_data.mkdir(parents=True)
            app = root / "BodySlide macOS.app"
            macos = app / "Contents/MacOS"
            macos.mkdir(parents=True)
            (macos / "BodySlide").touch()
            settings = root / "BodySlide macOS Settings"
            settings.mkdir()
            (settings / "Config.xml").write_bytes((Path(__file__).resolve().parents[1] / "Config.xml").read_bytes())
            (settings / "BuildSelection.xml").write_text("<BuildSelection/>")
            (settings / "BodySlide.xml").write_text("<BodySlideConfig/>")
            studio = root / "Outfit Studio macOS.app/Contents/MacOS"
            studio.mkdir(parents=True)
            (studio / "OutfitStudio").touch()

            configure(app, profile, game_data)

            self.assertEqual((settings / "BuildSelection.xml").resolve(), (state / "BuildSelection.xml").resolve())
            self.assertEqual((settings / "BodySlide.xml").resolve(), (state / "BodySlide.xml").resolve())
            self.assertEqual(len(ET.parse(settings / "BuildSelection.xml").getroot()), 2)
            backup = next((root / "BodySlide macOS Backups").iterdir())
            self.assertEqual((backup / "MO2-BuildSelection.xml").read_bytes(), (state / "BuildSelection.xml").read_bytes())
            self.assertEqual((backup / "MO2-BodySlide.xml").read_bytes(), (state / "BodySlide.xml").read_bytes())
            config = ET.parse(settings / "Config.xml").getroot()
            self.assertEqual(Path(config.findtext("OutputDataPath").rstrip("/")), mo2)
            project_view = root / "BodySlide macOS Projects/SliderSets/Test.osp"
            self.assertEqual(project_view.resolve(), project.resolve())

            choices = (state / "BuildSelection.xml").read_bytes()
            profile.write_text("-Bodyslide Output\n+Outfit Mod\n")
            configure(app, profile, game_data)
            self.assertFalse((settings / "BuildSelection.xml").is_symlink())
            self.assertFalse((settings / "BodySlide.xml").is_symlink())
            self.assertEqual((state / "BuildSelection.xml").read_bytes(), choices)
            fallback_config = ET.parse(settings / "Config.xml").getroot()
            self.assertEqual(
                Path(fallback_config.findtext("OutputDataPath").rstrip("/")),
                root / "BodySlide macOS Output",
            )


if __name__ == "__main__":
    unittest.main()
