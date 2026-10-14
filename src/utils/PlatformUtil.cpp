/*
BodySlide and Outfit Studio
See the included LICENSE file
*/

#include "PlatformUtil.h"

#include <filesystem>

namespace {
std::string backslash_to_slash(const std::string& s) {
	std::string sc(s);
	size_t len = sc.length();
	for (size_t i = 0; i < len; ++i)
		if (sc[i] == '\\')
			sc[i] = '/';
	return sc;
}
} // namespace

namespace PlatformUtil {
#ifdef _WINDOWS
// ACP wide to multibyte
std::string WideToMultiByteACP(const std::wstring& wstr) {
	if (wstr.empty())
		return std::string();

	int size_needed = WideCharToMultiByte(CP_ACP, 0, &wstr[0], (int)wstr.size(), nullptr, 0, nullptr, nullptr);
	std::string strTo(size_needed, 0);
	WideCharToMultiByte(CP_ACP, 0, &wstr[0], (int)wstr.size(), &strTo[0], size_needed, nullptr, nullptr);
	return strTo;
}

// UTF-8 multibyte to wide
std::wstring MultiByteToWideUTF8(const std::string& str) {
	if (str.empty())
		return std::wstring();

	int size_needed = MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), nullptr, 0);
	std::wstring wstrTo(size_needed, 0);
	MultiByteToWideChar(CP_UTF8, 0, &str[0], (int)str.size(), &wstrTo[0], size_needed);
	return wstrTo;
}
#endif

void OpenFileStream(std::fstream& file, const std::string& fileName, std::ios_base::openmode mode) {
#ifdef _WINDOWS
	// Convert to std::wstring on Windows only
	file.open(MultiByteToWideUTF8(fileName).c_str(), mode);
#else
	std::string fn_nobs = backslash_to_slash(fileName);
	file.open(fn_nobs.c_str(), mode);
#endif
}

bool FileExists(const std::string& fileName) {
	std::fstream file;
	PlatformUtil::OpenFileStream(file, fileName, std::ios::in | std::ios::binary);

	if (!file)
		return false;

	return true;
}

std::string GetUserSettingsPath(const std::string& appDir, const std::string& fileName) {
	std::filesystem::path directory(appDir);
#ifdef __APPLE__
	if (directory.filename() == "MacOS" && directory.parent_path().filename() == "Contents" &&
		directory.parent_path().parent_path().extension() == ".app") {
		return (directory.parent_path().parent_path().parent_path() / "BodySlide macOS Settings" / fileName).string();
	}
#endif
	return (directory / fileName).string();
}

// Provide std::wstring function for Windows
#ifdef _WINDOWS
void OpenFileStream(std::fstream& file, const std::wstring& fileName, unsigned int mode) {
	file.open(fileName.c_str(), mode);
}

bool FileExists(const std::wstring& fileName) {
	std::fstream file;
	PlatformUtil::OpenFileStream(file, fileName, std::ios::in | std::ios::binary);

	if (!file)
		return false;

	return true;
}
#endif
} // namespace PlatformUtil
