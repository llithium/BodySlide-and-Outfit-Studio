/*
BodySlide and Outfit Studio
See the included LICENSE file
*/

#include "ProjectUtil.h"
#include "ConfigurationManager.h"
#include "StringStuff.h"

#include <wx/dir.h>

extern ConfigurationManager Config;

std::string ProjectUtil::GetProjectPath() {
	std::string projectPath = Config["ProjectPath"];
	std::string appDir = Config["AppDir"];
	std::string gameDataPath = Config["GameDataPath"];

	// An explicit project path takes precedence over bundled data.
	if (!projectPath.empty() && wxDir::Exists(projectPath))
		return projectPath;

	if (wxDir::Exists(appDir + PathSepStr + "SliderSets"))
		return appDir;

	std::vector<std::string> pathsToCheck{
		gameDataPath + PathSepStr + "CalienteTools" + PathSepStr + "BodySlide",
		gameDataPath + PathSepStr + "Tools" + PathSepStr + "BodySlide"};

	// Return first existing path
	for (const auto& path : pathsToCheck) {
		if (wxDir::Exists(path)) {
			return path;
		}
	}

	// If no path exists, return projectPath if configured, otherwise AppDir
	return !projectPath.empty() ? projectPath : appDir;
}
