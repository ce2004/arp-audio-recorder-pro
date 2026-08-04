import os
import time
import threading
import subprocess
import urllib.request
import urllib.error
import json
import sys

try:
    from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
    from PyQt6.QtCore import Qt
except ImportError:
    print("Please install PyQt6.")
    sys.exit(1)

try:
    import numpy as np
    import soundcard as sc
    import keyboard
    import accessible_output2.outputs.auto
except ImportError:
    print("Please install numpy, soundcard, keyboard, and accessible_output2 modules.")
    sys.exit(1)

stop_beeping = False
current_progress = 0.0
current_speed_kb = 0
current_eta_s = 0
current_downloaded_bytes = 0
current_total_bytes = 0
speaker = accessible_output2.outputs.auto.Auto()

def beep_loop():
    global stop_beeping, current_progress
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
    pct = int(current_progress * 100)
    mb_s = round(current_speed_kb / 1024, 1)
    dl_mb = round(current_downloaded_bytes / (1024*1024), 1)
    tot_mb = round(current_total_bytes / (1024*1024), 1)
    
    text = f"{pct} percent, {mb_s} megabytes per second. {dl_mb} of {tot_mb} megabytes. {current_eta_s} seconds remaining."
    speaker.speak(text, interrupt=True)

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

def test_download():
    global current_progress, current_speed_kb, current_eta_s, stop_beeping, current_downloaded_bytes, current_total_bytes
    
    print("Starting test download... Press SPACE to hear progress!")
    speaker.speak("Starting test download. Press space to hear progress.")
    
    test_url = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
    
    keyboard.on_press_key("space", announce_progress)
    
    beep_thread = threading.Thread(target=beep_loop, daemon=True)
    beep_thread.start()
    
    try:
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            current_total_bytes = int(response.getheader('Content-Length').strip())
            current_downloaded_bytes = 0
            chunk_size = 8192
            start_time = time.time()
            
            with open("test_download.tmp", 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    current_downloaded_bytes += len(chunk)
                    
                    current_progress = current_downloaded_bytes / current_total_bytes
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        current_speed_kb = int((current_downloaded_bytes / 1024) / elapsed)
                        current_eta_s = int((current_total_bytes - current_downloaded_bytes) / (current_downloaded_bytes / elapsed))
                    
                    pass
                    
        print("\nDownload complete!")
        speaker.speak("Download complete.")
        time.sleep(2)
    except Exception as e:
        print("Download error:", e)
    finally:
        stop_beeping = True
        keyboard.unhook_all()
        if os.path.exists("test_download.tmp"):
            os.remove("test_download.tmp")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    test_release_notes = "Added a cool new feature\n- Fixed a crash on startup\n* Improved NVDA accessibility support!"
    
    dialog = UpdateDialog("v1.0.4", "v1.0.5", test_release_notes)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        test_download()
    else:
        print("Update cancelled by user.")
