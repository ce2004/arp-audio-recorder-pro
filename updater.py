import os
import sys
import urllib.request
import json
import subprocess
import zipfile
import shutil
import time
import threading

try:
    from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
    from PyQt6.QtCore import Qt
except ImportError:
    pass

try:
    import numpy as np
    import soundcard as sc
    import keyboard
    import accessible_output2.outputs.auto
    HAS_ACCESSIBILITY = True
except ImportError:
    HAS_ACCESSIBILITY = False

GITHUB_REPO = "ce2004/arp-audio-recorder-pro"  
CURRENT_VERSION = "v1.0.45"

# Globals for download tracking
stop_beeping = False
current_progress = 0.0
current_speed_kb = 0
current_eta_s = 0
current_downloaded_bytes = 0
current_total_bytes = 0

if HAS_ACCESSIBILITY:
    speaker = accessible_output2.outputs.auto.Auto()
else:
    speaker = None

def beep_loop():

    try:
        snd_speaker = sc.default_speaker()
        fs = 44100
        while not stop_beeping:
            if current_progress > 0:
                freq = 400 * (2 ** (2 * current_progress))
                duration_ms = 50
                t = np.linspace(0, duration_ms/1000, int(fs * duration_ms/1000), False)
                wave = np.sin(freq * t * 2 * np.pi) * 0.3
                wave_stereo = np.column_stack((wave, wave))
                snd_speaker.play(wave_stereo, samplerate=fs)
                time.sleep(0.3)
            else:
                time.sleep(0.1)
    except Exception as e:
        print("Beep error:", e)

def announce_progress(e=None):
    if not speaker: return
    try:
        pct = int(current_progress * 100)
        mb_s = round(current_speed_kb / 1024, 1)
        dl_mb = round(current_downloaded_bytes / (1024*1024), 1)
        tot_mb = round(current_total_bytes / (1024*1024), 1)
        
        text = f"{pct} percent, {mb_s} megabytes per second. {dl_mb} of {tot_mb} megabytes. {current_eta_s} seconds remaining."
        speaker.speak(text, interrupt=True)
    except Exception:
        pass

try:
    _old_btn_key_press = QPushButton.keyPressEvent
    def new_btn_key_press(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            return
        _old_btn_key_press(self, event)
    QPushButton.keyPressEvent = new_btn_key_press
except NameError:
    pass

class UpdateDialog(QDialog):
    def __init__(self, current_ver, new_ver, release_notes):
        super().__init__()
        self.setWindowTitle("Update Available")
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(f"There's an update available. You will be upgrading from version {current_ver} to {new_ver}.")
        info_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(info_label)
        
        whats_new_label = QLabel("What's new:")
        whats_new_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(whats_new_label)
        
        self.changes_list = QListWidget()
        for line in release_notes.split('\n'):
            line = line.strip()
            # clean up markdown bullets
            if line.startswith("-") or line.startswith("*"):
                line = line[1:].strip()
            if line:
                self.changes_list.addItem(line)
        layout.addWidget(self.changes_list)
        
        btn_layout = QHBoxLayout()
        self.btn_yes = QPushButton("Update Now")
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no = QPushButton("Don't Update")
        self.btn_no.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_yes)
        btn_layout.addWidget(self.btn_no)
        layout.addLayout(btn_layout)
        
        self.setTabOrder(info_label, whats_new_label)
        self.setTabOrder(whats_new_label, self.changes_list)
        self.setTabOrder(self.changes_list, self.btn_yes)
        self.setTabOrder(self.btn_yes, self.btn_no)

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            releases = json.loads(response.read().decode())
            
        if not releases:
            return None, None, None, None
            
        latest_release = releases[0]
        latest_version = latest_release['tag_name']
        
        def parse_ver(v):
            return tuple(int(x) for x in v.lstrip('v').split('.'))
        
        try:
            if parse_ver(CURRENT_VERSION) >= parse_ver(latest_version):
                return None, None, None, None
        except Exception:
            if latest_version == CURRENT_VERSION:
                return None, None, None, None
            
        release_notes_parts = []
        for release in releases:
            version = release.get('tag_name', '')
            if version == CURRENT_VERSION:
                break
                
            body = release.get('body', '').strip()
            if body:
                release_notes_parts.append(f"Changes in {version}:")
                for line in body.split('\n'):
                    cleaned_line = line.replace('#', '').replace('*', '').strip()
                    if cleaned_line:
                        release_notes_parts.append(cleaned_line)
                release_notes_parts.append("")
                
        release_notes = "\n".join(release_notes_parts).strip()
        if not release_notes:
            release_notes = latest_release.get('body', '')
            
        download_url = None
        sha_url = None
        for asset in latest_release.get('assets', []):
            if asset['name'].lower().endswith('.zip') and download_url is None:
                download_url = asset['browser_download_url']
            elif asset['name'] == 'sha256sum.txt':
                sha_url = asset['browser_download_url']
        
        if download_url:
            return latest_version, download_url, release_notes, sha_url
    except Exception as e:
        print("Failed to check for updates:", e)
    return None, None, None, None

def cleanup_old_updates():
    import threading
    def _cleanup_task():
        app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        import shutil
        import re
        import time
        import json
        
        for _ in range(30):
            all_clean = True
            try:
                manifest_path = os.path.join(app_dir, '.update_manifest.json')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as f:
                        paths = json.load(f)
                    for path in paths:
                        try:
                            if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
                            else: os.remove(path)
                        except: pass
                        if os.path.exists(path): all_clean = False
                    if all_clean:
                        try: os.remove(manifest_path)
                        except: pass
                else:
                    for item in os.listdir(app_dir):
                        if re.search(r'\.old_[a-f0-9]{8}$', item):
                            path = os.path.join(app_dir, item)
                            try:
                                if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
                                else: os.remove(path)
                            except: pass
                            if os.path.exists(path): all_clean = False
            except: all_clean = False

            try:
                temp_zip = os.path.join(app_dir, "update.zip")
                if os.path.exists(temp_zip): os.remove(temp_zip)
            except: all_clean = False
            
            try:
                extract_dir = os.path.join(app_dir, "update_extract")
                if os.path.exists(extract_dir): shutil.rmtree(extract_dir, ignore_errors=True)
                if os.path.exists(extract_dir): all_clean = False
            except: all_clean = False

            try:
                cleanup_file = os.path.join(app_dir, ".update_cleanup")
                if os.path.exists(cleanup_file): os.remove(cleanup_file)
            except: all_clean = False
            
            if all_clean:
                break
            time.sleep(1)
            
    threading.Thread(target=_cleanup_task, daemon=True).start()

def apply_update(download_url, sha_url):
    global current_progress, current_speed_kb, current_eta_s, stop_beeping, current_downloaded_bytes, current_total_bytes
    try:
        if not getattr(sys, 'frozen', False):
            print("Not running as compiled exe, skipping update.")
            return

        exe_path = sys.executable
        app_dir = os.path.dirname(exe_path)
        temp_zip = os.path.join(app_dir, "update.zip")
        extract_dir = os.path.join(app_dir, "update_extract")
        
        print(f"Downloading update from {download_url}...")
        
        if HAS_ACCESSIBILITY:
            speaker.speak("Press space for progress.", interrupt=True)
            keyboard.on_press_key("space", announce_progress)
            beep_thread = threading.Thread(target=beep_loop, daemon=True)
            beep_thread.start()
        
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            length_header = response.getheader('Content-Length')
            current_total_bytes = int(length_header.strip()) if length_header else 1
            if current_total_bytes == 0:
                current_total_bytes = 1
            current_downloaded_bytes = 0
            chunk_size = 8192
            start_time = time.time()
            
            with open(temp_zip, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    current_downloaded_bytes += len(chunk)
                    
                    current_progress = min(current_downloaded_bytes / current_total_bytes, 1.0)
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        current_speed_kb = int((current_downloaded_bytes / 1024) / elapsed)
                        current_eta_s = int((current_total_bytes - current_downloaded_bytes) / (current_downloaded_bytes / elapsed))
        
        stop_beeping = True
        
        if not sha_url:
            os.remove(temp_zip)
            if HAS_ACCESSIBILITY:
                try:
                    keyboard.unhook_all()
                    speaker.speak("Update aborted: No cryptographic hash file found. For security, updates without verification data cannot be installed.", interrupt=True)
                except: pass
            from PyQt6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance()
            if app: QMessageBox.critical(None, "Update Failed", "Update aborted: No cryptographic hash file found. For security, updates without verification data cannot be installed.")
            return

        try:
            req_sha = urllib.request.Request(sha_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_sha, timeout=10) as res_sha:
                expected_hash = res_sha.read().decode('utf-8-sig').strip().upper()
            
            import hashlib
            sha256_hash = hashlib.sha256()
            with open(temp_zip, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            actual_hash = sha256_hash.hexdigest().upper()
            
            if actual_hash != expected_hash:
                os.remove(temp_zip)
                if HAS_ACCESSIBILITY:
                    try:
                        keyboard.unhook_all()
                        speaker.speak("Update failed. SHA-256 hash invalid.", interrupt=True)
                    except: pass
                from PyQt6.QtWidgets import QMessageBox, QApplication
                app = QApplication.instance()
                if app: QMessageBox.critical(None, "Update Failed", "SHA-256 hash verification failed! The update file is corrupt or was tampered with during download. The update has been aborted.")
                return
        except Exception as e:
            print(f"Failed to verify hash: {e}")
            raise e

        if HAS_ACCESSIBILITY:
            try:
                keyboard.unhook_all()
                speaker.speak("Download complete and verified. Installing...", interrupt=True)
            except:
                pass
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        import hashlib
        update_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        cleanup_file = os.path.join(app_dir, ".update_cleanup")
        
        manifest_paths = []
        rollback_map = {}
        new_items = []
        update_success = True
        
        try:
            for item in os.listdir(extract_dir):
                s = os.path.join(extract_dir, item)
                d = os.path.join(app_dir, item)
                old_d = d + f".old_{update_hash}"
                
                if os.path.exists(d):
                    if os.path.exists(old_d):
                        try:
                            if os.path.isdir(old_d): shutil.rmtree(old_d)
                            else: os.remove(old_d)
                        except: pass
                    os.rename(d, old_d)
                    rollback_map[old_d] = d
                    manifest_paths.append(old_d)
                
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
                new_items.append(d)
                
        except Exception as e:
            print("Error during transactional copy:", e)
            update_success = False
            for new_item in new_items:
                try:
                    if os.path.isdir(new_item): shutil.rmtree(new_item)
                    else: os.remove(new_item)
                except: pass
            for old_path, orig_path in rollback_map.items():
                try:
                    os.rename(old_path, orig_path)
                except: pass
            
        if not update_success:
            os.remove(temp_zip)
            shutil.rmtree(extract_dir, ignore_errors=True)
            if HAS_ACCESSIBILITY:
                try: speaker.speak("Update failed during copy. Changes have been rolled back.", interrupt=True)
                except: pass
            from PyQt6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance()
            if app: QMessageBox.critical(None, "Update Failed", "Update failed during installation. Your application has been rolled back to its previous state.")
            return

        os.remove(temp_zip)
        shutil.rmtree(extract_dir)
        
        try:
            with open(os.path.join(app_dir, '.update_manifest.json'), "w") as f:
                json.dump(manifest_paths, f)
        except:
            pass
        
        try:
            with open(cleanup_file, "w") as f:
                f.write(update_hash)
        except:
            pass
        
        print("Update applied successfully! Restarting...")
        subprocess.Popen([exe_path] + sys.argv[1:])
        os._exit(0)
    except Exception as e:
        print("Error applying update:", e)
        
        try:
            if 'temp_zip' in locals() and os.path.exists(temp_zip): os.remove(temp_zip)
            if 'extract_dir' in locals() and os.path.exists(extract_dir): shutil.rmtree(extract_dir, ignore_errors=True)
        except: pass
        
        stop_beeping = True
        if HAS_ACCESSIBILITY: keyboard.unhook_all()

def run_auto_updater(manual=False):
    cleanup_old_updates()
    version, url, notes, sha_url = check_for_updates()
    if url:
        # Create a temporary QApplication to show the dialog before the main app starts
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        dialog = UpdateDialog(CURRENT_VERSION, version, notes)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            apply_update(url, sha_url)
    elif manual:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "Up to Date", "You are already on the latest version!")

if __name__ == "__main__":
    run_auto_updater()
