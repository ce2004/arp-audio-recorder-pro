import sys
import os
import threading
import datetime
import time
import json
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QCheckBox, QFormLayout, QLineEdit, QDialog, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread

HAS_ACCESSIBILITY = False
try:
    import accessible_output2.outputs.auto
    speaker = accessible_output2.outputs.auto.Auto()
    HAS_ACCESSIBILITY = True
except ImportError:
    pass

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder_config.json")

def load_config():
    default_config = {
        "auto_start": False,
        "auto_start_delay": 0,
        "save_folder": os.getcwd(),
        "sample_rate": "48000",
        "bit_depth": "24",
        "channels": "2",
        "filename_prefix": "",
        "auto_split_secs": 0,
        "max_length_secs": 0,
        "group_splits": True,
        "buffer_size": 2048,
        "device_id": "",
        "device2_id": "none",
        "in1_route": "Both Channels",
        "in2_route": "Both Channels",
        "window_title": "Accessible Advanced Audio Recorder",
        "notify_start_stop": True,
        "notify_split": True,
        "notify_error": True,
        "notify_drive_disconnect": True,
        "notify_mic_disconnect": True,
        "speak_in_focus_only": False,
        "auto_resume_unattended": False,
        "continue_on_mic_disconnect": False,
        "confirm_exit": True,
        "check_updates_startup": True,
        "snd_start": True,
        "snd_stop": True,
        "snd_pause": True,
        "snd_unpause": True,
        "snd_volume": 100,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if "auto_split_mins" in config:
                    config["auto_split_secs"] = config.pop("auto_split_mins") * 60
                default_config.update(config)
        except:
            pass
    return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Failed to save config:", e)

class NotificationSettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Notification Settings")
        self.config = config
        
        layout = QFormLayout(self)
        
        self.chk_start_stop = QCheckBox("Notify on Start/Stop Recording")
        self.chk_start_stop.setChecked(self.config.get("notify_start_stop", True))
        layout.addRow(self.chk_start_stop)
        
        self.chk_split = QCheckBox("Notify on Auto-Split")
        self.chk_split.setChecked(self.config.get("notify_split", True))
        layout.addRow(self.chk_split)
        
        self.chk_error = QCheckBox("Notify on recording errors")
        self.chk_error.setChecked(self.config.get("notify_error", True))
        layout.addRow(self.chk_error)
        
        self.chk_drive = QCheckBox("Notify when output drive disconnects")
        self.chk_drive.setChecked(self.config.get("notify_drive_disconnect", True))
        layout.addRow(self.chk_drive)
        
        self.chk_mic_disc = QCheckBox("Notify on microphone disconnect")
        self.chk_mic_disc.setChecked(self.config.get("notify_mic_disconnect", True))
        layout.addRow(self.chk_mic_disc)
        
        self.chk_confirm_exit = QCheckBox("Confirm exit while recording")
        self.chk_confirm_exit.setChecked(self.config.get("confirm_exit", True))
        layout.addRow(self.chk_confirm_exit)
        
        self.chk_focus_speak = QCheckBox("Speak announcements only when window is in focus")
        self.chk_focus_speak.setChecked(self.config.get("speak_in_focus_only", False))
        layout.addRow(self.chk_focus_speak)
        
        self.chk_auto_resume = QCheckBox("Auto-resume unattended recording if drive/mic reconnects")
        self.chk_auto_resume.setChecked(self.config.get("auto_resume_unattended", False))
        layout.addRow(self.chk_auto_resume)
        
        btn_save = QPushButton("Save && Close")
        btn_save.clicked.connect(self.save_and_close)
        layout.addRow(btn_save)
        
    def save_and_close(self):
        self.config["notify_start_stop"] = self.chk_start_stop.isChecked()
        self.config["notify_split"] = self.chk_split.isChecked()
        self.config["notify_error"] = self.chk_error.isChecked()
        self.config["notify_drive_disconnect"] = self.chk_drive.isChecked()
        self.config["notify_mic_disconnect"] = self.chk_mic_disc.isChecked()
        self.config["speak_in_focus_only"] = self.chk_focus_speak.isChecked()
        self.config["auto_resume_unattended"] = self.chk_auto_resume.isChecked()
        self.config["confirm_exit"] = self.chk_confirm_exit.isChecked()
        save_config(self.config)
        self.accept()

class SoundSettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Configure Sounds")
        self.config = config
        
        layout = QFormLayout(self)
        
        self.chk_snd_start = QCheckBox("Play sound on Start")
        self.chk_snd_start.setChecked(self.config.get("snd_start", True))
        layout.addRow(self.chk_snd_start)
        
        self.chk_snd_stop = QCheckBox("Play sound on Stop")
        self.chk_snd_stop.setChecked(self.config.get("snd_stop", True))
        layout.addRow(self.chk_snd_stop)
        
        self.chk_snd_pause = QCheckBox("Play sound on Pause")
        self.chk_snd_pause.setChecked(self.config.get("snd_pause", True))
        layout.addRow(self.chk_snd_pause)
        
        self.chk_snd_unpause = QCheckBox("Play sound on Unpause")
        self.chk_snd_unpause.setChecked(self.config.get("snd_unpause", True))
        layout.addRow(self.chk_snd_unpause)
        
        self.spin_volume = PercentageSpinBox()
        self.spin_volume.setRange(1, 100)
        self.spin_volume.setValue(self.config.get("snd_volume", 100))
        layout.addRow("Sound Effects &Volume:", self.spin_volume)
        
        btn_save = QPushButton("Save && Close")
        btn_save.clicked.connect(self.save_and_close)
        layout.addRow(btn_save)
        
    def save_and_close(self):
        self.config["snd_start"] = self.chk_snd_start.isChecked()
        self.config["snd_stop"] = self.chk_snd_stop.isChecked()
        self.config["snd_pause"] = self.chk_snd_pause.isChecked()
        self.config["snd_unpause"] = self.chk_snd_unpause.isChecked()
        self.config["snd_volume"] = self.spin_volume.value()
        save_config(self.config)
        self.accept()

config = load_config()
if config.get("check_updates_startup", True):
    try:
        import updater
        updater.run_auto_updater()
    except Exception as e:
        print("Updater failed to run:", e)

class PercentageSpinBox(QSpinBox):
    def textFromValue(self, value):
        return f"{value} percent"

    def valueFromText(self, text):
        import re
        nums = re.findall(r'\d+', text)
        if nums:
            return int(nums[0])
        return self.value()

    def validate(self, text, pos):
        from PyQt6.QtGui import QValidator
        return (QValidator.State.Acceptable, text, pos)
        
    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Home:
            self.setValue(self.minimum())
            event.accept()
        elif event.key() == Qt.Key.Key_End:
            self.setValue(self.maximum())
            event.accept()
        else:
            super().keyPressEvent(event)

class DriveMonitorThread(QThread):
    disconnected_signal = pyqtSignal(str)
    
    def __init__(self, get_folder_func):
        super().__init__()
        self.get_folder = get_folder_func
        self.is_running = True
        
        folder = self.get_folder()
        if folder:
            drive = os.path.splitdrive(folder)[0].upper()
            if drive and drive != "C:":
                drive_path = drive + "\\" if not drive.endswith("\\") else drive
                self.last_drive_status = os.path.exists(drive_path)
            else:
                self.last_drive_status = True
        else:
            self.last_drive_status = True
        
    def run(self):
        while self.is_running:
            folder = self.get_folder()
            if folder:
                drive = os.path.splitdrive(folder)[0].upper()
                if drive and drive != "C:":
                    drive_path = drive + "\\" if not drive.endswith("\\") else drive
                    exists = os.path.exists(drive_path)
                    if not exists and self.last_drive_status:
                        self.disconnected_signal.emit(drive)
                        self.last_drive_status = False
                    elif exists:
                        self.last_drive_status = True
            time.sleep(1.0)
            
    def stop(self):
        self.is_running = False

class AutoResumeThread(QThread):
    resume_signal = pyqtSignal(str)
    
    def __init__(self, folder, mic1_id, mic2_id, missing):
        super().__init__()
        self.folder = folder
        self.mic1_id = mic1_id
        self.mic2_id = mic2_id
        self.missing = missing
        self.is_running = True
        
    def run(self):
        import soundcard as sc
        while self.is_running:
            drive_ok = True
            if self.folder:
                drive = os.path.splitdrive(self.folder)[0].upper()
                if drive and drive != "C:":
                    drive_path = drive + "\\" if not drive.endswith("\\") else drive
                    if not os.path.exists(drive_path):
                        drive_ok = False
            
            mic1_ok = False
            mic2_ok = True if self.mic2_id == "none" else False
            
            if drive_ok:
                try:
                    mics = sc.all_microphones()
                    mic_ids = [m.id for m in mics]
                    if self.mic1_id in mic_ids:
                        mic1_ok = True
                    if self.mic2_id != "none" and self.mic2_id in mic_ids:
                        mic2_ok = True
                except:
                    pass
                    
            if drive_ok and mic1_ok and mic2_ok:
                self.resume_signal.emit(self.missing)
                break
                
            time.sleep(1.0)
            
    def stop(self):
        self.is_running = False

class AudioMixerDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Configure Audio Channels")
        self.config = config
        
        layout = QFormLayout(self)
        
        self.cb_in1 = QComboBox()
        self.cb_in1.addItems(["Both Channels", "Left Channel Only", "Right Channel Only"])
        self.cb_in1.setCurrentText(self.config.get("in1_route", "Both Channels"))
        layout.addRow("Input &1 Routing:", self.cb_in1)
        
        self.cb_in2 = QComboBox()
        self.cb_in2.addItems(["Both Channels", "Left Channel Only", "Right Channel Only"])
        self.cb_in2.setCurrentText(self.config.get("in2_route", "Both Channels"))
        layout.addRow("Input &2 Routing:", self.cb_in2)
        
        self.chk_cont_mic = QCheckBox("Continue recording if a mic disconnects")
        self.chk_cont_mic.setChecked(self.config.get("continue_on_mic_disconnect", False))
        layout.addRow(self.chk_cont_mic)
        
        btn_save = QPushButton("Save && Close")
        btn_save.clicked.connect(self.save_and_close)
        layout.addRow(btn_save)
        
    def save_and_close(self):
        self.config["in1_route"] = self.cb_in1.currentText()
        self.config["in2_route"] = self.cb_in2.currentText()
        self.config["continue_on_mic_disconnect"] = self.chk_cont_mic.isChecked()
        save_config(self.config)
        self.accept()

class TimeFormatSpinBox(QSpinBox):
    def textFromValue(self, total_seconds):
        if total_seconds == 0:
            return "0 seconds (off)"
            
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")
        if minutes > 0:
            parts.append(f"{minutes} minute" if minutes == 1 else f"{minutes} minutes")
        if seconds > 0:
            parts.append(f"{seconds} second" if seconds == 1 else f"{seconds} seconds")
            
        return ", ".join(parts)

    def valueFromText(self, text):
        import re
        text = text.lower()
        tokens = re.findall(r'(\d+)\s*([a-z]*)', text)
        total = 0
        prev_unit = None
        
        for num_str, unit in tokens:
            num = int(num_str)
            if unit.startswith('h'):
                total += num * 3600
                prev_unit = 'h'
            elif unit.startswith('m'):
                total += num * 60
                prev_unit = 'm'
            elif unit.startswith('s'):
                total += num
                prev_unit = 's'
            else:
                if prev_unit == 'h':
                    total += num * 60
                    prev_unit = 'm'
                elif prev_unit == 'm':
                    total += num
                    prev_unit = 's'
                else:
                    total += num
                    prev_unit = 's'
                    
        return total

    def validate(self, text, pos):
        from PyQt6.QtGui import QValidator
        if '-' in text:
            return (QValidator.State.Invalid, text, pos)
        return (QValidator.State.Intermediate, text, pos)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Home:
            self.setValue(self.minimum())
            event.accept()
        elif event.key() == Qt.Key.Key_End:
            self.setValue(self.maximum())
            event.accept()
        else:
            super().keyPressEvent(event)


_old_btn_key_press = QPushButton.keyPressEvent
def new_btn_key_press(self, event):
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        self.click()
        return
    _old_btn_key_press(self, event)
QPushButton.keyPressEvent = new_btn_key_press

class SettingsDialog(QDialog):
    def __init__(self, parent, config, devices):
        super().__init__(parent)
        self.setWindowTitle("Recording Settings")
        self.setMinimumWidth(550)
        self.setMinimumHeight(600)
        self.config = config
        self.devices = devices
        
        self.build_ui()
        self.apply_config()

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        
        # Audio Device Settings
        dev_grp = QGroupBox("Audio Devices")
        dev_layout = QFormLayout()
        
        self.cb_sort = QComboBox()
        self.cb_sort.addItems(["Inputs First", "Outputs First"])
        dev_layout.addRow("Device &Sort Order:", self.cb_sort)
        
        self.device_cb = QComboBox()
        self.device2_cb = QComboBox()
        self.device2_cb.addItem("None", "none")
        
        sort_order = self.config.get("device_sort_order", "Inputs First")
        sorted_devices = sorted(self.devices, key=lambda d: (getattr(d, 'isloopback', False) if sort_order == "Inputs First" else not getattr(d, 'isloopback', False), d.name))
        for d in sorted_devices:
            prefix = "Output (Loopback): " if getattr(d, 'isloopback', False) else "Input: "
            self.device_cb.addItem(f"{prefix}{d.name}", d.id)
            self.device2_cb.addItem(f"{prefix}{d.name}", d.id)
            
        dev_layout.addRow("Primary Input &1:", self.device_cb)
        dev_layout.addRow("Secondary Input &2:", self.device2_cb)
        dev_grp.setLayout(dev_layout)
        layout.addWidget(dev_grp)
        
        # Folder Settings
        folder_grp = QGroupBox("Output Directory")
        folder_layout = QHBoxLayout()
        self.txt_folder = QLineEdit()
        self.txt_folder.setReadOnly(True)
        folder_layout.addWidget(self.txt_folder, stretch=1)
        
        btn_folder = QPushButton("C&hange Folder")
        btn_folder.clicked.connect(self.choose_folder)
        folder_layout.addWidget(btn_folder)
        folder_grp.setLayout(folder_layout)
        layout.addWidget(folder_grp)
        
        # Audio Format Settings
        audio_grp = QGroupBox("Audio Format Settings")
        form_layout = QFormLayout()
        
        warn_lbl = QLabel("To avoid downsampling/resampling garbage, select the\nEXACT rate your Windows device is set to!")
        warn_lbl.setStyleSheet("color: red; font-style: italic;")
        form_layout.addRow(warn_lbl)
        
        sr_lbl = QLabel("Sa&mple Rate (Hz):")
        self.sr_cb = QComboBox()
        self.sr_cb.addItems(["44100", "48000", "88200", "96000", "192000", "384000"])
        sr_lbl.setBuddy(self.sr_cb)
        form_layout.addRow(sr_lbl, self.sr_cb)
        
        bd_lbl = QLabel("&Bit Depth:")
        self.bd_cb = QComboBox()
        self.bd_cb.addItems(["16", "24", "32"])
        bd_lbl.setBuddy(self.bd_cb)
        form_layout.addRow(bd_lbl, self.bd_cb)
        
        ch_lbl = QLabel("&Channels:")
        self.ch_cb = QComboBox()
        self.ch_cb.addItems(["1 (Mono)", "2 (Stereo)"])
        ch_lbl.setBuddy(self.ch_cb)
        form_layout.addRow(ch_lbl, self.ch_cb)
        
        buf_lbl = QLabel("B&uffer Size (Frames):")
        self.buf_cb = QComboBox()
        self.buf_cb.addItems(["512", "1024", "2048", "4096", "8192"])
        buf_lbl.setBuddy(self.buf_cb)
        form_layout.addRow(buf_lbl, self.buf_cb)
        
        audio_grp.setLayout(form_layout)
        layout.addWidget(audio_grp)
        
        # File & Startup Settings
        file_grp = QGroupBox("File, Delay & Auto-Split Settings")
        file_form = QFormLayout()
        
        pref_lbl = QLabel("File &Prefix:")
        self.txt_prefix = QLineEdit()
        pref_lbl.setBuddy(self.txt_prefix)
        file_form.addRow(pref_lbl, self.txt_prefix)
        
        self.chk_auto_start = QCheckBox("Auto-st&art recording on launch")
        file_form.addRow(self.chk_auto_start)
        
        self.spin_delay = TimeFormatSpinBox()
        self.spin_delay.setRange(0, 3600)
        
        delay_lbl = QLabel("Start De&lay:")
        delay_lbl.setBuddy(self.spin_delay)
        file_form.addRow(delay_lbl, self.spin_delay)
        
        self.spin_max_len = TimeFormatSpinBox()
        self.spin_max_len.setRange(0, 2000000) # Cap at ~23 days to prevent QTimer 32-bit int overflow
        
        max_len_lbl = QLabel("Max Recording Length (0=off):")
        max_len_lbl.setBuddy(self.spin_max_len)
        file_form.addRow(max_len_lbl, self.spin_max_len)
        
        self.spin_split = TimeFormatSpinBox()
        self.spin_split.setRange(0, 3600 * 24)
        
        split_lbl = QLabel("Time Auto-S&plit every:")
        split_lbl.setBuddy(self.spin_split)
        file_form.addRow(split_lbl, self.spin_split)
        
        self.chk_group_splits = QCheckBox("Automatically place all splits into a unified folder")
        file_form.addRow(self.chk_group_splits)
        
        file_grp.setLayout(file_form)
        layout.addWidget(file_grp)
        
        # Misc Settings
        misc_grp = QGroupBox("Appearance & Extra Options")
        misc_form = QFormLayout()
        
        title_lbl = QLabel("Window &Title:")
        self.txt_title = QLineEdit()
        self.txt_title.setText(self.config.get("window_title", "Accessible Advanced Audio Recorder"))
        title_lbl.setBuddy(self.txt_title)
        misc_form.addRow(title_lbl, self.txt_title)
        
        self.chk_update_startup = QCheckBox("Check for &updates on startup")
        self.chk_update_startup.setChecked(self.config.get("check_updates_startup", True))
        misc_form.addRow(self.chk_update_startup)
        
        btn_check_updates = QPushButton("Check for &Updates Now")
        btn_check_updates.clicked.connect(self.manual_update_check)
        misc_form.addRow(btn_check_updates)
        
        btn_notif = QPushButton("Configure Notifications")
        btn_notif.clicked.connect(self.open_notifications)
        misc_form.addRow(btn_notif)
        
        btn_sounds = QPushButton("Configure Sounds")
        btn_sounds.clicked.connect(self.open_sounds)
        misc_form.addRow(btn_sounds)
        
        btn_mixer = QPushButton("Configure Audio Channels")
        btn_mixer.clicked.connect(self.open_mixer)
        misc_form.addRow(btn_mixer)
        
        misc_grp.setLayout(misc_form)
        layout.addWidget(misc_grp)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton("Save && Close")
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        main_layout.addLayout(btn_layout)


    def manual_update_check(self):
        try:
            import updater
            updater.run_auto_updater(manual=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check for updates: {e}")

    def open_notifications(self):
        dlg = NotificationSettingsDialog(self, self.config)
        dlg.exec()
        
    def open_sounds(self):
        dlg = SoundSettingsDialog(self, self.config)
        dlg.exec()
        
    def open_mixer(self):
        dlg = AudioMixerDialog(self, self.config)
        dlg.exec()

    def update_folder_label(self, path):
        self.txt_folder.setText(path)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.config["save_folder"])
        if folder:
            drive = os.path.splitdrive(folder)[0].upper()
            if drive and drive != "C:":
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("External Drive Warning")
                msg.setText(f"You have selected a directory on drive {drive}.\n\nWhile this will work perfectly, it can be dangerous. If this is a removable USB drive or external hard drive and it gets disconnected or bumped while the app is running, your recording could be abruptly terminated.\n\nPlease ensure the drive remains securely connected.")
                btn_understand = msg.addButton("I understand", QMessageBox.ButtonRole.AcceptRole)
                btn_revert = msg.addButton("Revert", QMessageBox.ButtonRole.RejectRole)
                msg.exec()
                
                if msg.clickedButton() == btn_revert:
                    return
                    
            self.update_folder_label(folder)

    def apply_config(self):
        self.update_folder_label(self.config["save_folder"])
        self.chk_auto_start.setChecked(self.config["auto_start"])
        self.cb_sort.setCurrentText(self.config.get("device_sort_order", "Inputs First"))
        self.txt_prefix.setText(self.config.get("filename_prefix", ""))
        
        self.spin_delay.setValue(self.config.get("auto_start_delay", 0))
        self.spin_split.setValue(self.config.get("auto_split_secs", 0))
        self.spin_max_len.setValue(self.config.get("max_length_secs", 0))
        self.chk_group_splits.setChecked(self.config.get("group_splits", True))
        
        self.txt_title.setText(self.config.get("window_title", "Accessible Advanced Audio Recorder"))
        
        sr = self.config["sample_rate"]
        idx = self.sr_cb.findText(sr)
        if idx >= 0: self.sr_cb.setCurrentIndex(idx)
        
        bd = self.config["bit_depth"]
        idx = self.bd_cb.findText(bd)
        if idx >= 0: self.bd_cb.setCurrentIndex(idx)
        
        ch = self.config["channels"]
        self.ch_cb.setCurrentIndex(0 if ch == "1" else 1)
            
        bs = str(self.config.get("buffer_size", 2048))
        idx = self.buf_cb.findText(bs)
        if idx >= 0: self.buf_cb.setCurrentIndex(idx)
        
        dev_id = self.config.get("device_id", "")
        if dev_id:
            idx = self.device_cb.findData(dev_id)
            if idx >= 0:
                self.device_cb.setCurrentIndex(idx)
            else:
                self.device_cb.insertItem(0, f"DISCONNECTED: {dev_id}", dev_id)
                self.device_cb.setCurrentIndex(0)
                
        dev2_id = self.config.get("device2_id", "none")
        if dev2_id:
            idx = self.device2_cb.findData(dev2_id)
            if idx >= 0:
                self.device2_cb.setCurrentIndex(idx)
            else:
                self.device2_cb.insertItem(1, f"DISCONNECTED: {dev2_id}", dev2_id)
                self.device2_cb.setCurrentIndex(1)

    def save_and_close(self):
        d1 = self.device_cb.currentData()
        d2 = self.device2_cb.currentData()
        if d2 != "none" and d1 == d2:
            QMessageBox.warning(self, "Invalid Selection", "Input 1 and Input 2 cannot be the same device.")
            return
            
        self.config["device_id"] = d1
        self.config["device2_id"] = d2
        
        self.config["auto_start"] = self.chk_auto_start.isChecked()
        self.config["auto_start_delay"] = self.spin_delay.value()
        self.config["auto_split_secs"] = self.spin_split.value()
        self.config["max_length_secs"] = self.spin_max_len.value()
        self.config["group_splits"] = self.chk_group_splits.isChecked()
        
        self.config["sample_rate"] = self.sr_cb.currentText()
        self.config["bit_depth"] = self.bd_cb.currentText()
        self.config["channels"] = "1" if "1" in self.ch_cb.currentText() else "2"
        self.config["filename_prefix"] = self.txt_prefix.text()
        self.config["buffer_size"] = int(self.buf_cb.currentText())
        
        self.config["window_title"] = self.txt_title.text()
        self.config["check_updates_startup"] = self.chk_update_startup.isChecked()
        
        self.config["save_folder"] = self.txt_folder.text()
        self.config["device_sort_order"] = self.cb_sort.currentText()
            
        save_config(self.config)
        self.accept()

class AudioRecorderApp(QMainWindow):
    error_signal = pyqtSignal(str)
    split_signal = pyqtSignal()
    mic_disconnected_signal = pyqtSignal(int, bool)

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setWindowTitle(self.config.get("window_title", "Accessible Advanced Audio Recorder"))
        self.resize(500, 300)
        
        self.is_recording = False
        self.is_paused = False
        self.devices = []
        self.record_thread_handle = None
        self.current_filename = None
        self.current_session_folder = None
        self.split_count = 1
        self.current_status_msg = "Status: Ready"
        
        self.needs_split = False
        self.split_timer = QTimer(self)
        self.split_timer.timeout.connect(self.do_auto_split)
        
        self.max_len_timer = QTimer(self)
        self.max_len_timer.timeout.connect(self.force_stop_max_length)
        
        self.split_signal.connect(self.on_split_completed)
        
        self.live_stats_timer = QTimer(self)
        self.live_stats_timer.timeout.connect(self.update_live_stats)
        
        self.drive_thread = DriveMonitorThread(lambda: self.config.get("save_folder", ""))
        self.drive_thread.disconnected_signal.connect(self.handle_drive_disconnect)
        self.drive_thread.start()
        
        self.error_signal.connect(self.handle_error)
        self.mic_disconnected_signal.connect(self.handle_mic_disconnect)
        
        self.populate_devices()
        self.build_ui()
        
        saved_dev_id = self.config.get("device_id", "")
        if saved_dev_id:
            found = any(m.id == saved_dev_id for m in self.devices)
            if not found:
                QMessageBox.warning(
                    self,
                    "Device Not Found",
                    f"CRITICAL: Your explicitly configured audio device is missing!\n\n"
                    f"The device matching ID:\n'{saved_dev_id}'\n\ncould not be found. It may be disconnected, powered off, or disabled in Windows.\n\n"
                    "For safety and privacy, this application WILL NOT automatically fall back to another microphone.\n\n"
                    "Action Required:\n"
                    "1. Reconnect your device and restart this application, OR\n"
                    "2. Open Settings and manually select a different input device."
                )
                
        self.update_dashboard_status()
        
        if self.config.get("auto_start", False):
            delay = self.config.get("auto_start_delay", 0)
            self.auto_start_timer = QTimer(self)
            self.auto_start_timer.setSingleShot(True)
            self.auto_start_timer.timeout.connect(self.start_recording)
            if delay > 0:
                self.current_status_msg = f"Status: Auto-recording in {delay} seconds..."
                self.update_dashboard_status()
                self.auto_start_timer.start(delay * 1000)
            else:
                self.auto_start_timer.start(100)

    def notify(self, title, msg, setting_key):
        if not self.config.get(setting_key, True):
            return
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=msg,
                app_name="Audio Recorder Pro",
                timeout=3
            )
        except Exception as e:
            print(f"Notification failed: {e}")

    def play_sound(self, event_name):
        if not self.config.get(f"snd_{event_name}", True): return
        
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)
            
        path = os.path.join(base_dir, "sounds", f"{event_name}.wav")
        if os.path.exists(path):
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            
            if not hasattr(self, 'active_sounds'):
                self.active_sounds = []
            
            self.active_sounds = [s for s in self.active_sounds if s.isPlaying()]
            
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            volume = self.config.get("snd_volume", 100) / 100.0
            effect.setVolume(volume)
            effect.play()
            self.active_sounds.append(effect)
        else:
            pass

    def populate_devices(self):
        self.devices = []
        try:
            import soundcard as sc
            self.devices = sc.all_microphones(include_loopback=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not enumerate audio devices: {e}")

    def build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        title_lbl = QLabel("Audio Recorder Dashboard")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_lbl)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.btn_exit = QPushButton("E&xit")
        self.btn_exit.setMinimumHeight(40)
        self.btn_exit.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_exit)
        
        self.btn_settings = QPushButton("Se&ttings")
        self.btn_settings.setMinimumHeight(40)
        self.btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(self.btn_settings)
        
        self.btn_toggle_record = QPushButton("&Start Recording")
        self.btn_toggle_record.setMinimumHeight(40)
        self.btn_toggle_record.clicked.connect(self.toggle_recording)
        btn_layout.addWidget(self.btn_toggle_record)
        
        self.btn_pause = QPushButton("&Pause")
        self.btn_pause.setMinimumHeight(40)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.btn_pause)
        
        main_layout.addLayout(btn_layout)
        
        # Overview label
        self.overview_lbl = QLabel()
        self.overview_lbl.setWordWrap(True)
        self.overview_lbl.setStyleSheet("margin-top: 15px; margin-bottom: 15px;")
        self.overview_lbl.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        main_layout.addWidget(self.overview_lbl)
        
        main_layout.addStretch()
        
        # Live Stats label
        self.live_stats_lbl = QLabel("")
        self.live_stats_lbl.setStyleSheet("font-weight: bold; padding: 10px; background-color: #e0e0e0; border-radius: 5px;")
        self.live_stats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_stats_lbl.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.live_stats_lbl.hide()
        main_layout.addWidget(self.live_stats_lbl)
        
        # Set exact Tab Order for NVDA
        QWidget.setTabOrder(self.btn_exit, self.btn_settings)
        QWidget.setTabOrder(self.btn_settings, self.btn_toggle_record)
        QWidget.setTabOrder(self.btn_toggle_record, self.btn_pause)
        QWidget.setTabOrder(self.btn_pause, self.overview_lbl)
        QWidget.setTabOrder(self.overview_lbl, self.live_stats_lbl)
        
        # Set initial focus
        self.btn_exit.setFocus()

    def open_settings(self):
        self.populate_devices()
        dlg = SettingsDialog(self, self.config, self.devices)
        if dlg.exec():
            self.setWindowTitle(self.config.get("window_title", "Accessible Advanced Audio Recorder"))
            self.update_dashboard_status()

    def update_dashboard_status(self):
        dev_id = self.config.get("device_id", "")
        mic = next((m for m in self.devices if m.id == dev_id), None)
        mic_name = mic.name if mic else "None Selected (Will use default)"
        
        auto_start = "On" if self.config.get("auto_start") else "Off"
        folder = self.config.get("save_folder", "Unknown")
        split = self.config.get("auto_split_secs", 0)
        split_txt = f"{split} seconds" if split > 0 else "Off"
        
        overview = (
            f"Recording Device is set to: {mic_name}\n"
            f"Output Folder is set to: {folder}\n"
            f"Auto-Recording is: {auto_start}\n"
            f"Auto-Split is: {split_txt}\n\n"
            f"{self.current_status_msg}"
        )
        self.overview_lbl.setText(overview)

    def update_live_stats(self):
        if not self.is_recording:
            return
            
        try:
            sr = int(self.config["sample_rate"])
            ch = int(self.config["channels"])
            bd = int(self.config["bit_depth"])
            
            seconds = int(getattr(self, 'total_frames_written', 0) / sr) if sr > 0 else 0
            bytes_written = getattr(self, 'total_frames_written', 0) * ch * (bd / 8)
            mb = bytes_written / (1024 * 1024)
            
            m, s = divmod(seconds, 60)
            
            time_str = "Recording time, "
            if m > 0:
                time_str += f"{m} minutes, {s} seconds. "
            else:
                time_str += f"{s} seconds. "
            
            split_info = f" (Split {getattr(self, 'split_count', 1)})" if getattr(self, 'split_count', 1) > 1 else ""
            self.live_stats_lbl.setText(f"{time_str}{mb:.2f} MB Storage used on current split{split_info}.")
        except Exception:
            pass

    def speak(self, msg):
        if not HAS_ACCESSIBILITY: return
        if self.config.get("speak_in_focus_only", False):
            if not self.isActiveWindow():
                return
        try:
            speaker.speak(msg)
        except Exception:
            pass

    def do_auto_split(self):
        if self.is_recording:
            self.needs_split = True

    def on_split_completed(self):
        self.split_count = getattr(self, 'split_count', 1) + 1
        msg = f"Split {self.split_count} started"
        self.notify("File Split", msg, "notify_split")
        self.speak(msg)
        self.current_status_msg = f"Status: Recording Split {self.split_count} to {os.path.basename(self.current_filename)}"
        self.update_dashboard_status()
        
    def force_stop_max_length(self):
        if self.is_recording:
            self.stop_recording(notify=False)
            self.notify("Max Length Reached", "The recording automatically stopped because it reached the maximum length.", "notify_start_stop")

    def handle_drive_disconnect(self, drive):
        if getattr(self, 'handling_disconnect', False): return
        self.handling_disconnect = True
        
        was_recording = self.is_recording
        if self.is_recording:
            self.stop_recording(notify=False)
            
        if self.config.get("notify_drive_disconnect", True):
            msg = f"The drive {drive} was disconnected."
            if was_recording:
                msg += " The contents of the recording up to this point have been saved."
            self.notify("Drive Disconnected", msg, "notify_drive_disconnect")
            
        if was_recording and self.config.get("auto_resume_unattended", False):
            self.start_auto_resume_thread("drive")
            msg = "Waiting for output drive to reconnect before resuming..."
            self.speak(msg)
            self.current_status_msg = f"Status: Error - {msg}"
            self.update_dashboard_status()
            self.handling_disconnect = False
            return
            
        QMessageBox.critical(self, "Drive Disconnected", 
            f"The output drive ({drive}) was suddenly removed or disconnected.\n\n" +
            ("The active recording was automatically stopped. The contents of the recording up to this point have been safely saved.\n\n" if was_recording else "") +
            "Please reconnect the drive or go to Settings to select a new Output Directory."
        )
        self.handling_disconnect = False

    def handle_error(self, err_msg):
        folder = self.config.get("save_folder", "")
        if folder:
            drive = os.path.splitdrive(folder)[0].upper()
            if drive and not os.path.exists(drive + "\\"):
                # Drive monitor handles it
                return
                
        self.stop_recording(notify=False)
        self.notify("Error", "Recording failed.", "notify_error")
        QMessageBox.critical(self, "Recording Error", err_msg)

    def handle_mic_disconnect(self, mic_num, will_continue):
        msg = f"CRITICAL ERROR: Microphone {mic_num} was unplugged or disabled during recording!"
        if will_continue:
            msg += "\n\nHowever, because 'Continue recording' is enabled, the recording will continue using the remaining input."
            self.notify("Microphone Disconnected", msg, "notify_mic_disconnect")
            QMessageBox.critical(self, "Microphone Disconnected", msg)
        else:
            msg += "\n\nRecording has been safely stopped."
            self.stop_recording(notify=False)
            self.notify("Microphone Disconnected", msg, "notify_mic_disconnect")
            
            if self.config.get("auto_resume_unattended", False):
                self.start_auto_resume_thread("mic")
                msg = "Waiting for microphone to reconnect before resuming..."
                self.speak(msg)
                self.current_status_msg = f"Status: Error - {msg}"
                self.update_dashboard_status()
                return
                
            QMessageBox.critical(self, "Microphone Disconnected", msg)

    def start_auto_resume_thread(self, missing):
        if getattr(self, 'auto_resume_thread', None) and self.auto_resume_thread.is_running:
            self.auto_resume_thread.missing = "both"
            return
        folder = self.config.get("save_folder", "")
        mic1_id = self.config.get("device_id", "")
        mic2_id = self.config.get("device2_id", "none")
        self.auto_resume_thread = AutoResumeThread(folder, mic1_id, mic2_id, missing)
        self.auto_resume_thread.resume_signal.connect(self.handle_auto_resume)
        self.auto_resume_thread.start()
        
    def handle_auto_resume(self, missing):
        if getattr(self, 'auto_resume_thread', None):
            self.auto_resume_thread.stop()
            
        if missing == "drive":
            self.speak("Output drive found. Recording again after error.")
        elif missing == "mic":
            self.speak("Microphone found. Recording again after error.")
        else:
            self.speak("Devices found. Recording again after error.")
            
        self.start_recording()

    def record_audio_worker(self, mic1, mic2, sr, ch, subtype, buf_size, prefix):
        file = None
        try:
            import soundfile as sf
            import numpy as np
            import queue
            
            in1_route = self.config.get("in1_route", "Both Channels")
            in2_route = self.config.get("in2_route", "Both Channels")
            
            def apply_routing(data, route, out_channels):
                if route == "Left Channel Only":
                    mono = data[:, 0] if data.shape[1] >= 2 else data[:, 0]
                elif route == "Right Channel Only":
                    mono = data[:, 1] if data.shape[1] >= 2 else data[:, 0]
                else:
                    mono = np.mean(data, axis=1, dtype=np.float32) if data.shape[1] >= 2 else data[:, 0]

                if out_channels == 1:
                    return mono.reshape(-1, 1)
                
                out = np.zeros((len(data), 2), dtype=np.float32)
                if route == "Left Channel Only":
                    out[:, 0] = mono
                elif route == "Right Channel Only":
                    out[:, 1] = mono
                else:
                    if data.shape[1] >= 2:
                        out[:, 0] = data[:, 0]
                        out[:, 1] = data[:, 1]
                    else:
                        out[:, 0] = data[:, 0]
                        out[:, 1] = data[:, 0]
                return out
                
            file = sf.SoundFile(self.current_filename, mode='w', samplerate=sr, channels=ch, subtype=subtype)
            
            is_active = True
            def check_active(): return self.is_recording and is_active

            num_readers = 2 if mic2 else 1
            ready_barrier = threading.Barrier(num_readers + 1)
            
            def reader_thread(mic, out_q):
                try:
                    with mic.recorder(samplerate=sr, channels=2) as rec:
                        # Pre-read 1 block to flush WASAPI startup artifacts
                        rec.record(numframes=buf_size)
                        ready_barrier.wait()
                        
                        while check_active():
                            data = rec.record(numframes=buf_size)
                            try:
                                out_q.put((time.time(), data), timeout=1.0)
                            except queue.Full:
                                pass
                except Exception as e:
                    print(f"Reader error: {e}")
                    try:
                        ready_barrier.abort()
                    except:
                        pass

            q1 = queue.Queue(maxsize=100)
            t1 = threading.Thread(target=reader_thread, args=(mic1, q1), daemon=True)
            t1.start()
            
            q2 = None
            if mic2:
                q2 = queue.Queue(maxsize=100)
                t2 = threading.Thread(target=reader_thread, args=(mic2, q2), daemon=True)
                t2.start()
                
            try:
                ready_barrier.wait()
            except threading.BrokenBarrierError:
                self.error_signal.emit("Failed to initialize audio devices.")
                is_active = False
                file.close()
                return
            
            try:
                expected_time = time.time()
                mic1_failed = False
                mic2_failed = False
                continue_on_disc = self.config.get("continue_on_mic_disconnect", False)
                abort_recording = False
                last_flush_time = time.time()
                
                buf_duration = buf_size / sr
                last_frame_time = time.time()
                mic1_silent = False
                mic2_silent = False
                
                while self.is_recording and not abort_recording:
                    s1 = q1.qsize()
                    s2 = q2.qsize() if mic2 else 0
                    
                    if s1 > 0: mic1_silent = False
                    if s2 > 0: mic2_silent = False
                    
                    if s1 == 0 and s2 == 0:
                        time.sleep(0.01)
                        if not t1.is_alive() and not mic1_failed:
                            mic1_failed = True
                            will_continue = bool(continue_on_disc and mic2 and not mic2_failed)
                            self.mic_disconnected_signal.emit(1, will_continue)
                            if not will_continue:
                                abort_recording = True
                                break
                        if mic2 and not t2.is_alive() and not mic2_failed:
                            mic2_failed = True
                            will_continue = bool(continue_on_disc and not mic1_failed)
                            self.mic_disconnected_signal.emit(2, will_continue)
                            if not will_continue:
                                abort_recording = True
                                break
                                
                        if time.time() - last_frame_time > buf_duration + 0.05:
                            data1 = np.zeros((buf_size, 2), dtype=np.float32)
                            data2 = np.zeros((buf_size, 2), dtype=np.float32) if mic2 else None
                            last_frame_time = time.time()
                        else:
                            continue
                            
                    q1_timeout = 0.0 if mic1_silent else (buf_duration + 0.05)
                    try:
                        ts1, data1 = q1.get(timeout=q1_timeout)
                        mic1_silent = False
                    except queue.Empty:
                        mic1_silent = True
                        ts1 = time.time()
                        data1 = np.zeros((buf_size, 2), dtype=np.float32)
                        
                    data2 = None
                    if mic2:
                        q2_timeout = 0.0 if mic2_silent else (buf_duration + 0.05)
                        while True:
                            try:
                                ts2, d2 = q2.get(timeout=q2_timeout)
                                if ts2 < ts1 - 0.5:
                                    continue
                                data2 = d2
                                mic2_silent = False
                                break
                            except queue.Empty:
                                mic2_silent = True
                                data2 = np.zeros_like(data1)
                                break
                                
                    last_frame_time = time.time()
                            
                    if not self.is_paused:
                        r1 = apply_routing(data1, in1_route, ch)
                        if mic2:
                            r2 = apply_routing(data2, in2_route, ch)
                            mixed = np.clip(r1 + r2, -1.0, 1.0)
                            file.write(mixed)
                        else:
                            file.write(r1)
                            
                        curr_time = time.time()
                        if curr_time - last_flush_time > 2.0:
                            file.flush()
                            last_flush_time = curr_time
                            
                        self.total_frames_written = getattr(self, 'total_frames_written', 0) + len(r1)
                        
                        if getattr(self, 'needs_split', False):
                            self.needs_split = False
                            
                            folder = self.config.get("save_folder", "")
                            drive = os.path.splitdrive(folder)[0].upper()
                            drive_path = drive + "\\" if not drive.endswith("\\") else drive
                            try:
                                file.close()
                            except:
                                pass
                            
                            if drive and drive != "C:" and not os.path.exists(drive_path):
                                self.error_signal.emit("Output drive disconnected during auto-split.")
                                break
                            
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            base_filename = os.path.join(self.current_session_folder, f"{prefix}_{timestamp}" if prefix else timestamp)
                            self.current_filename = f"{base_filename}.wav"
                            counter = 1
                            while os.path.exists(self.current_filename):
                                self.current_filename = f"{base_filename}_{counter}.wav"
                                counter += 1
                            
                            file = sf.SoundFile(self.current_filename, mode='w', samplerate=sr, channels=ch, subtype=subtype)
                            self.total_frames_written = 0
                            self.split_signal.emit()
            finally:
                is_active = False
                if file and not file.closed:
                    try:
                        file.close()
                    except:
                        pass
                                    
        except Exception as e:
            if self.is_recording:
                self.error_signal.emit(f"An error occurred during recording: {e}")

    def toggle_recording(self):
        if hasattr(self, 'auto_start_timer') and self.auto_start_timer.isActive():
            self.auto_start_timer.stop()
            self.current_status_msg = "Status: Ready"
            self.update_dashboard_status()
            
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.play_sound("pause")
            self.speak("Recording paused")
            self.btn_pause.setText("R&esume")
            self.current_status_msg = f"Status: Paused (Split {getattr(self, 'split_count', 1)})"
        else:
            self.play_sound("unpause")
            self.speak("Recording resumed")
            self.btn_pause.setText("&Pause")
            self.current_status_msg = f"Status: Recording Split {getattr(self, 'split_count', 1)} to {os.path.basename(self.current_filename)}"
        self.update_dashboard_status()

    def start_recording(self):
        if self.is_recording: return
        
        folder = self.config.get("save_folder", "")
        if not folder:
            QMessageBox.critical(self, "Output Directory Error", "Please select an output directory in settings before recording.")
            return
            
        drive = os.path.splitdrive(folder)[0].upper()
        if drive and not os.path.exists(drive + "\\"):
            QMessageBox.warning(self, "Output Drive Missing", "The output drive you configured is currently disconnected.\n\nLike your microphone settings, this app does not automatically default to another location to prevent lost files.\n\nPlease reconnect the drive or select a new output folder in Settings.")
            return
        
        dev_id = self.config.get("device_id", "")
        if not dev_id:
            QMessageBox.warning(self, "Warning", "No audio device has been configured yet. Please open Settings and explicitly select an input device.")
            return
            
        mic1 = next((m for m in self.devices if m.id == dev_id), None)
        if not mic1:
            QMessageBox.warning(self, "Warning", "Input 1 is disconnected. Please reconnect it or open Settings and select a valid audio device.")
            return
            
        mic2 = None
        dev2_id = self.config.get("device2_id", "none")
        if dev2_id != "none":
            mic2 = next((m for m in self.devices if m.id == dev2_id), None)
            if not mic2:
                QMessageBox.warning(self, "Warning", "Input 2 is disconnected. Please reconnect or disable it in Settings.")
                return
            
        sr = int(self.config["sample_rate"])
        bd = int(self.config["bit_depth"])
        ch = int(self.config["channels"])
        buf_size = self.config["buffer_size"]
        
        subtype_map = {16: 'PCM_16', 24: 'PCM_24', 32: 'PCM_32'}
        subtype = subtype_map[bd]
        
        prefix = self.config.get("filename_prefix", "").strip()
        
        prefix = re.sub(r'[\\/*?:"<>|]', "", prefix)
        
        split_secs = self.config.get("auto_split_secs", 0)
        
        try:
            if self.config.get("group_splits", True) and split_secs > 0:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_session_folder = os.path.join(self.config["save_folder"], f"{prefix}_{timestamp}" if prefix else timestamp)
                os.makedirs(self.current_session_folder, exist_ok=True)
            else:
                self.current_session_folder = self.config["save_folder"]
                os.makedirs(self.current_session_folder, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.join(self.current_session_folder, f"{prefix}_{timestamp}" if prefix else timestamp)
            self.current_filename = f"{base_filename}.wav"
            counter = 1
            while os.path.exists(self.current_filename):
                self.current_filename = f"{base_filename}_{counter}.wav"
                counter += 1
            
            self.is_recording = True
            self.is_paused = False
            self.total_frames_written = 0
            self.btn_toggle_record.setText("S&top Recording")
            self.btn_pause.setEnabled(True)
            self.btn_pause.setText("&Pause")
            self.btn_settings.setEnabled(False)
            
            self.needs_split = False
            self.record_thread_handle = threading.Thread(
                target=self.record_audio_worker, 
                args=(mic1, mic2, sr, ch, subtype, buf_size, prefix),
                daemon=True
            )
            self.record_thread_handle.start()
            
            if split_secs > 0:
                self.split_timer.start(split_secs * 1000)
                
            max_len = self.config.get("max_length_secs", 0)
            if max_len > 0:
                self.max_len_timer.start(max_len * 1000)
                
            self.live_stats_lbl.setText("Recording time, 0 seconds. 0.00 MB Storage used on current split.")
            self.live_stats_lbl.show()
            self.live_stats_timer.start(1000)
            
            self.split_count = 1
            self.speak("Recording started")
            
            self.current_status_msg = f"Status: Recording Split {self.split_count} to {os.path.basename(self.current_filename)}"
            self.update_dashboard_status()
            
            self.play_sound("start")
            self.notify("Recording Started", "Audio recording has begun.", "notify_start_stop")
            
        except Exception as e:
            self.is_recording = False
            self.btn_toggle_record.setText("&Start Recording")
            self.btn_pause.setEnabled(False)
            self.btn_settings.setEnabled(True)
            QMessageBox.critical(self, "Audio Error", f"Failed to start recording.\n\nError: {e}")

    def stop_recording(self, notify=True):
        if not self.is_recording: return
        self.is_recording = False
        self.is_paused = False
        self.needs_split = False
        self.split_timer.stop()
        self.max_len_timer.stop()
        self.live_stats_timer.stop()
        
        if notify:
            self.speak("Recording stopped")
            
        if self.record_thread_handle:
            self.record_thread_handle.join(timeout=0.1)
            self.record_thread_handle = None
            
        self.btn_toggle_record.setText("&Start Recording")
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("&Pause")
        self.btn_settings.setEnabled(True)
        self.live_stats_lbl.hide()
        
        self.current_status_msg = "Status: Ready"
        self.update_dashboard_status()
        self.play_sound("stop")
        
        self.current_session_folder = None
        
        if notify:
            self.notify("Recording Saved", "File safely saved to disk!", "notify_start_stop")

    def closeEvent(self, event):
        if self.is_recording and self.config.get("confirm_exit", True):
            stats = self.live_stats_lbl.text() if self.live_stats_lbl.isVisible() else "Recording in progress."
            msg = (
                "You are currently recording.\n\n"
                f"{stats}\n\n"
                "Are you sure you'd like to exit? If you do, your recording will be saved, "
                "and if you have notifications enabled, you will be sent a notification before the program exits."
            )
            reply = QMessageBox.question(
                self, "Confirm Exit", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        self.stop_recording(notify=True)
        if hasattr(self, 'drive_thread'):
            self.drive_thread.stop()
            self.drive_thread.wait(100)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioRecorderApp()
    window.show()
    sys.exit(app.exec())
