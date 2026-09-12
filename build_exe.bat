@echo off
setlocal

echo === Cai dat PyInstaller (neu chua co) ===
py -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error

echo.
echo === Cai dat cac thu vien ung dung ===
py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo === Dong goi thanh file .exe ===
py -m PyInstaller --noconfirm --onefile --windowed ^
    --name "PPT_Event_Controller" ^
    --hidden-import=win32timezone ^
    --hidden-import=win32com.client ^
    --hidden-import=pythoncom ^
    --hidden-import=pywintypes ^
    main.py
if errorlevel 1 goto :error

echo.
echo === Hoan tat ===
echo File .exe nam trong thu muc dist\PPT_Event_Controller.exe
echo Hay copy file .exe do vao cung thu muc voi README.md va sample_program.json
echo (app_settings.json va autosave.json se tu tao ra canh file .exe khi chay).
goto :end

:error
echo.
echo Co loi xay ra trong qua trinh dong goi. Xem thong bao loi ben tren.

:end
pause
