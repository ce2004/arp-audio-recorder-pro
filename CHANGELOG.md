Changelog

All notable changes to ARP Audio Recorder Pro will be documented in this file.

v1.0.12 - 2026-08-04
Fixed:
- Removed a leftover win10toast import statement that caused the compiled application to crash on startup.

---

v1.0.11 - 2026-08-04
Changed:
- Forced a minor version bump to verify that the auto-updater correctly prompts the user for new updates.

---

v1.0.10 - 2026-08-04
Fixed:
- Migrated notifications from win10toast to native QSystemTrayIcon to fix a bug where notifications failed to appear in the compiled executable.
- Fixed the internal file-path logic so audio cues (start/stop) correctly locate the sounds folder when the application is compiled and running as an executable.

---

v1.0.9 - 2026-08-04
Added:
- Added a professional and fully accessible README without markdown number-signs.
- Packaged the README directly into the download.
Changed:
- Cleaned up the development environment.

---

v1.0.8 - 2026-08-04
Added:
- Created a formal Changelog.

Changed:
- Executable and Release ZIP are now properly named Audio Recorder Pro.exe and Audio Recorder Pro.zip.
- Removed all temporary testing scripts from the repository.

---

v1.0.7 - 2026-08-04
Changed:
- The updater now explicitly announces "Press space for progress" via NVDA immediately after clicking "Update Now" to let the user know they can track the download.

---

v1.0.6 - 2026-08-04
Changed:
- Changed the updater dialog buttons from "Yes/No" to "Update Now" and "Don't Update" for clearer instructions.

---

v1.0.5 - 2026-08-04
Added:
- An interactive PyQt6 update prompt that announces "Update Available" before the application starts.
- Native NVDA integration to announce release notes directly inside the updater dialog.
- The user can tab through the dialog to hear the changes, and decide whether to update.
- Download progress triggers an exponential pitch audio progress bar mimicking NVDA's native progress indicator.
- Hitting Space during download interrupts speech to read out exact speed and ETA statistics.

---

v1.0.4 - 2026-08-04
Changed:
- Switched PyInstaller distribution from onefile to a standard folder layout. This removes the temp-folder extraction bottleneck, making the app open instantly.
- The GitHub action now correctly copies the sounds folder into the distribution folder and zips it all up.
- Upgraded updater.py logic to securely extract zip files, bypassing Windows locked-file restrictions by appending .old to actively running DLLs.

---

v1.0.3 - 2026-08-04
Added:
- Added a README.md to introduce the project, explain features, and guide developers.
- First iteration of the ZIP extractor auto-updater logic.

---

v1.0.2 - 2026-08-04
Fixed:
- Fixed an infinite loop bug where the app failed to recognize its new version number after updating.

---

v1.0.1 - 2026-08-04
Fixed:
- Fixed GitHub repository URL routing in the updater logic after a repository rename.

---

v1.0.0 - 2026-08-04
Added:
- Initial release featuring the core recording functionality and the base automated update integration.
