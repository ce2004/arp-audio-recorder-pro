# Audio Recorder Pro

Audio Recorder Pro is a standalone, lightweight audio recording application built with Python and PyQt6. It is designed from the ground up to be fully accessible for screen reader users (like NVDA or JAWS) while remaining powerful enough for advanced audio capture workflows.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Getting Started (For Users)](#getting-started-for-users)
4. [Using the Auto-Updater](#using-the-auto-updater)
5. [Running from Source (For Developers)](#running-from-source-for-developers)
6. [Building the Executable](#building-the-executable)

---

## Overview

Unlike many visual-first audio workstations that are difficult to navigate using keyboards and screen readers, Audio Recorder Pro relies on standard operating system UI components. Every button, slider, and list in this application can be reached with the `Tab` key, and state changes are audibly communicated.

## Features

- **Fully Accessible UI:** Built specifically with screen-reader compatibility in mind.
- **Customizable Audio Settings:** Adjust sample rates, bit depths, and channel configurations to suit your hardware.
- **Auto-Split Capabilities:** Automatically divide long recordings into separate files based on time limits.
- **Audio Cues:** Plays sounds for starting, stopping, and pausing recordings to provide physical feedback without looking at the screen.
- **Background Auto-Updater:** The application checks GitHub for updates, installs them seamlessly without leaving the app, and provides an audio-based progress bar during downloads.

---

## Getting Started (For Users)

You don't need to install Python or know how to code to use Audio Recorder Pro. 

1. Go to the [Releases page](https://github.com/ce2004/arp-audio-recorder-pro/releases) of this repository.
2. Under the latest version, download the file named `Audio Recorder Pro.zip`.
3. Extract the contents of the ZIP file to a folder on your computer (e.g., your Desktop or Documents folder). 
   - *Important:* Do not just run the application from inside the ZIP file. Extract it first.
4. Inside the extracted folder, run `Audio Recorder Pro.exe`. 

**Note on the `sounds` folder:** 
The application relies on the included `sounds` folder to play start/stop cues. Keep the `sounds` folder in the same directory as the executable.

---

## Using the Auto-Updater

Audio Recorder Pro includes a fully automated, accessible update system. 

When you open the application, it will quickly check this GitHub repository to see if a newer version exists. If one is found, a prompt will appear before the main application opens.

1. The prompt will state your current version and the new version.
2. Press `Tab` to navigate through the dialog.
3. You will encounter a list of Release Notes explaining what has changed in the new version. Use your up and down arrow keys to read them.
4. If you wish to update, tab to **Update Now** and press `Space` or `Enter`.

### During the Update
- NVDA will announce: *"Press space for progress."*
- You will hear a steady rhythmic ticking. As the download progresses, the pitch of the ticking will increase steadily.
- Pressing `Space` during the download will pause the ticking momentarily, and your screen reader will announce the current percentage, download speed, and estimated time remaining.
- Once complete, the application will automatically replace its own files and restart into the new version.

---

## Running from Source (For Developers)

If you prefer to run the application directly from the Python source code instead of using the compiled executable, follow these steps:

### Prerequisites
- Python 3.10 or higher.
- `git` installed on your system.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ce2004/arp-audio-recorder-pro.git
   cd arp-audio-recorder-pro
   ```

2. **Set up a virtual environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

---

## Building the Executable

If you are modifying the code and want to compile your own `.exe` file, you can do so using PyInstaller. 

Run the following command in the root directory:
```bash
pyinstaller --windowed --name "Audio Recorder Pro" app.py
```

This will create a `dist/Audio Recorder Pro` folder containing the executable and its required internal files. You will need to manually copy the `sounds` directory into this output folder for the application to function correctly. 
*(Note: If you push your changes to GitHub, the automated GitHub Actions workflow will handle this packaging process for you.)*
