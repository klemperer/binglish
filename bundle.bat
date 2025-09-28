pyinstaller --onefile --windowed -i binglish.ico --add-data "binglish.ico;." --hidden-import "pystray._win32" binglish.py
pause