with open('updater.py', 'r', encoding='utf-8') as f:
    code = f.read()

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
    code = code.replace('class UpdateDialog(QDialog):', inject + '\nclass UpdateDialog(QDialog):')

with open('updater.py', 'w', encoding='utf-8') as f:
    f.write(code)
