# NOTE THIS IS ONLY FOR RUNNING THE REGISTRATION.PY

import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from Registration import RegistrationWindow

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('lab4.pyqt6.gui')
except Exception:
    pass

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    window = RegistrationWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
    
    
