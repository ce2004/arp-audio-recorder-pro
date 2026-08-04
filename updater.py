import os
import sys
import urllib.request
import json
import subprocess

# We will set this to your GitHub username and repository later
GITHUB_REPO = "ce2004/arp-audio-recorder-pro"  
CURRENT_VERSION = "v1.0.2"

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        latest_version = data['tag_name']
        if latest_version != CURRENT_VERSION:
            download_url = None
            # Find the attached .exe file in the latest release
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            if download_url:
                return latest_version, download_url
    except Exception as e:
        print("Failed to check for updates:", e)
    return None, None

def apply_update(download_url):
    try:
        # Only update if running as a compiled .exe
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            temp_exe = exe_path + ".new"
            old_exe = exe_path + ".old"
            
            print(f"Downloading update from {download_url}...")
            urllib.request.urlretrieve(download_url, temp_exe)
            
            # Windows trick: You can rename a running file, just not delete it.
            if os.path.exists(old_exe):
                try:
                    os.remove(old_exe)
                except:
                    pass
            os.rename(exe_path, old_exe)
            os.rename(temp_exe, exe_path)
            
            print("Update applied successfully! Restarting...")
            # Restart the app
            subprocess.Popen([exe_path] + sys.argv[1:])
            sys.exit(0)
    except Exception as e:
        print("Error applying update:", e)

def run_auto_updater():
    version, url = check_for_updates()
    if url:
        print(f"New version {version} found! Updating...")
        apply_update(url)

if __name__ == "__main__":
    run_auto_updater()
