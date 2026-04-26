@echo off
REM نظام إدارة الموظفين - تشغيل سريع
chcp 65001 >nul

echo.
echo ========================================
echo نظام إدارة الموظفين
echo ========================================
echo.

REM التحقق من Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير مثبت
    pause
    exit /b 1
)

echo ✓ Python مثبت
echo.

REM تثبيت Flask إذا لم يكن موجوداً
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⏳ تثبيت Flask...
    pip install -q flask flask-cors pandas openpyxl
    echo ✓ تم التثبيت
    echo.
)

REM تشغيل التطبيق
echo ⏳ تشغيل التطبيق...
echo.
python app.py

pause
