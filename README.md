# ARP Audio Recorder Pro

Welcome to **ARP Audio Recorder Pro**! 

This is an advanced, accessible audio recording application built with Python and PyQt6. It features an automated update system, allowing the app to seamlessly stay up to date without requiring manual downloads.

## Features
* **High-Quality Recording:** Customizable sample rates, bit depths, and channel configurations.
* **Auto-Split & Management:** Automatically split recordings based on time limits and keep your files organized.
* **Notifications:** Built-in Windows toast notifications for start/stop, errors, and device disconnections.
* **Auto-Updates:** Automatically checks GitHub for new releases and updates itself.

## Installation

Download the latest `.zip` release from the [Releases page](https://github.com/ce2004/arp-audio-recorder-pro/releases). Extract the folder and run `app.exe`. 

> **Note:** Make sure to keep the `sounds/` folder in the same directory as `app.exe` so the application can load its audio cues!

## For Developers

### Building from Source
1. Clone this repository:
   ```bash
   git clone https://github.com/ce2004/arp-audio-recorder-pro.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

### Releasing a New Version
To release a new version through the automated update system:
1. Update `CURRENT_VERSION` inside `updater.py` (e.g., to `v1.0.3`).
2. Commit your changes and create a git tag matching the version.
3. Push to GitHub! The GitHub Actions workflow will automatically build the `.zip` file and publish the release.
