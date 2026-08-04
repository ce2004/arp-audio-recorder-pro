import os
import sys
import urllib.request
import json
import subprocess
import zipfile
import shutil

# We will set this to your GitHub username and repository later
GITHUB_REPO = "ce2004/arp-audio-recorder-pro"  
CURRENT_VERSION = "v1.0.4"

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        latest_version = data['tag_name']
        if latest_version != CURRENT_VERSION:
            download_url = None
            # Find the attached .zip file in the latest release
            for asset in data.get('assets', []):
                if asset['name'].endswith('.zip'):
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
            app_dir = os.path.dirname(exe_path)
            temp_zip = os.path.join(app_dir, "update.zip")
            extract_dir = os.path.join(app_dir, "update_extract")
            old_exe = exe_path + ".old"
            
            print(f"Downloading update from {download_url}...")
            urllib.request.urlretrieve(download_url, temp_zip)
            
            # Extract the zip
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Windows trick: You can rename running files and folders, just not delete them.
            for item in os.listdir(extract_dir):
                s = os.path.join(extract_dir, item)
                d = os.path.join(app_dir, item)
                old_d = d + ".old"
                
                # If an old version of this exists, rename it out of the way
                if os.path.exists(d):
                    if os.path.exists(old_d):
                        try:
                            if os.path.isdir(old_d): shutil.rmtree(old_d)
                            else: os.remove(old_d)
                        except:
                            pass
                    try:
                        os.rename(d, old_d)
                    except:
                        pass
                
                # Now move the new item in place
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            
            # Clean up temp files
            os.remove(temp_zip)
            shutil.rmtree(extract_dir)
            
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
