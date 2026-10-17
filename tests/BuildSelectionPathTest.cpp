#include "../src/components/BuildSelection.h"

#include <iostream>

int main(int argc, char** argv) {
	if (argc != 2)
		return 2;

	BuildSelectionFile file(argv[1]);
	if (file.GetError())
		return 3;

	BuildSelection selection;
	file.Get(selection);
	const std::string nativePath = "meshes/actors/character/character assets/femalebody";
	if (selection.GetOutputChoice(nativePath) != "CBBE 3BBB Body Amazing") {
		std::cerr << "Native path did not find the Windows-saved output choice\n";
		return 1;
	}

	selection.SetOutputChoice(nativePath, "Updated body");
	file.UpdateOutputChoices(selection);
	if (!file.Save())
		return 4;

	tinyxml2::XMLDocument saved;
	if (saved.LoadFile(argv[1]) != tinyxml2::XML_SUCCESS)
		return 5;
	auto* choice = saved.FirstChildElement("BuildSelection")->FirstChildElement("OutputChoice");
	if (!choice || choice->NextSiblingElement("OutputChoice") ||
		std::string(choice->Attribute("path")) != "meshes\\actors\\character\\character assets\\femalebody" ||
		std::string(choice->Attribute("choice")) != "Updated body") {
		std::cerr << "Updating the choice duplicated or changed its Windows path\n";
		return 1;
	}

	file.RemoveOutputChoice(nativePath);
	if (!file.Save())
		return 6;
	if (saved.LoadFile(argv[1]) != tinyxml2::XML_SUCCESS)
		return 7;
	if (saved.FirstChildElement("BuildSelection")->FirstChildElement("OutputChoice")) {
		std::cerr << "Native path did not remove the Windows-saved choice\n";
		return 1;
	}

	return 0;
}
