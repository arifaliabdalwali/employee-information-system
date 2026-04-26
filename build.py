import os
import sys
import shutil
import subprocess

def build_app():
    print("🚀 بدء عملية تجميع البرنامج...")
    
    # تنظيف المجلدات السابقة
    print("🧹 تنظيف الملفات المؤقتة...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # إنشاء المجلدات اللازمة للتشغيل
    print("📁 إنشاء المجلدات اللازمة...")
    folders = [
        'static/documents/employees',
        'static/documents/books', 
        'static/documents/courses',
        'static/documents/punishments',
        'static/documents/committees',
        'static/documents/promotions',
        'static/documents/allowances',
        'static/documents/vacations',
        'static/documents/delegations'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    # أوامر PyInstaller
    print("🔨 تجميع البرنامج باستخدام PyInstaller...")
    
    pyinstaller_cmd = [
        'pyinstaller',
        'app.py',
        '--name=نظام_الموظفين',
        '--onefile',
        '--windowed',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--clean',
        '--noconfirm'
    ]
    
    try:
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ تم تجميع البرنامج بنجاح!")
            print(f"📂 الملف التنفيذي موجود في: dist\\نظام_الموظفين.exe")
            
            # نسخ قاعدة البيانات إلى مجلد dist
            if os.path.exists('emp.db'):
                shutil.copy2('emp.db', 'dist/emp.db')
                print("✅ تم نسخ قاعدة البيانات")
        else:
            print("❌ فشل التجميع!")
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"❌ خطأ أثناء التجميع: {e}")

if __name__ == '__main__':
    build_app()