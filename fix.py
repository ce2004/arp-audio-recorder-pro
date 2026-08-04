import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Global enter key fix
inject = '''
_old_btn_key_press = QPushButton.keyPressEvent
def new_btn_key_press(self, event):
    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
        self.click()
        return
    _old_btn_key_press(self, event)
QPushButton.keyPressEvent = new_btn_key_press

'''
if '_old_btn_key_press' not in code:
    code = code.replace('class SettingsDialog(QDialog):', inject + 'class SettingsDialog(QDialog):')

# 2. Grouping fix
code = re.sub(r'layout\.addRow\(\s*\"\"\s*,\s*([^)]+)\)', r'layout.addRow(\1)', code)
code = re.sub(r'misc_form\.addRow\(\s*\"\"\s*,\s*([^)]+)\)', r'misc_form.addRow(\1)', code)
code = re.sub(r'file_form\.addRow\(\s*\"\"\s*,\s*([^)]+)\)', r'file_form.addRow(\1)', code)
code = re.sub(r'dev_layout\.addRow\(\s*\"\"\s*,\s*([^)]+)\)', r'dev_layout.addRow(\1)', code)

# 3. Sort Order UI
sort_combo = '''        self.cb_sort = QComboBox()
        self.cb_sort.addItems(["Inputs First", "Outputs First"])
        dev_layout.addRow("Device &Sort Order:", self.cb_sort)
        
        self.device_cb = QComboBox()'''
if 'self.cb_sort = QComboBox()' not in code:
    code = code.replace('        self.device_cb = QComboBox()', sort_combo)

if 'self.cb_sort.setCurrentText(' not in code:
    code = code.replace('self.chk_auto_start.setChecked(self.config["auto_start"])', 
                        'self.chk_auto_start.setChecked(self.config["auto_start"])\n        self.cb_sort.setCurrentText(self.config.get("device_sort_order", "Inputs First"))')

if 'self.config["device_sort_order"]' not in code:
    code = code.replace('self.config["save_folder"] = self.txt_folder.text()', 
                        'self.config["save_folder"] = self.txt_folder.text()\n        self.config["device_sort_order"] = self.cb_sort.currentText()')

# 4. Remove Mic / Sort devices logic
populate_loop_old = '''        for d in self.devices:
            prefix = "Output (Loopback): " if getattr(d, 'isloopback', False) else "Input (Mic): "
            self.device_cb.addItem(f"{prefix}{d.name}", d.id)
            self.device2_cb.addItem(f"{prefix}{d.name}", d.id)'''

populate_loop_new = '''        sort_order = self.config.get("device_sort_order", "Inputs First")
        sorted_devices = sorted(self.devices, key=lambda d: (getattr(d, 'isloopback', False) if sort_order == "Inputs First" else not getattr(d, 'isloopback', False), d.name))
        for d in sorted_devices:
            prefix = "Output (Loopback): " if getattr(d, 'isloopback', False) else "Input: "
            self.device_cb.addItem(f"{prefix}{d.name}", d.id)
            self.device2_cb.addItem(f"{prefix}{d.name}", d.id)'''

code = code.replace(populate_loop_old, populate_loop_new)

# 5. Fix empty prefix
code = code.replace('\"filename_prefix\": \"Recording\",', '\"filename_prefix\": \"\",')
code = code.replace('self.config.get(\"filename_prefix\", \"Recording\")', 'self.config.get(\"filename_prefix\", \"\")')
code = code.replace('if not prefix: prefix = \"Recording\"\\n', '')
code = code.replace('if not prefix: prefix = \"Recording\"\\r\\n', '')
code = code.replace('if not prefix: prefix = \"Recording\"', '')

code = code.replace('f\"{prefix}_{timestamp}\"', 'f\"{prefix}_{timestamp}\" if prefix else timestamp')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

