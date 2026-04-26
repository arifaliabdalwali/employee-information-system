#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة الموظفين - برنامج التشغيل (نسخة تصحيح الأخطاء)
يعرض جميع الأخطاء بوضوح
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def main():
    # الحصول على مسار المشروع
    project_dir = Path(__file__).parent
    
    print("=" * 70)
    print("نظام إدارة الموظفين - برنامج التشغيل")
    print("=" * 70)
    print()
    
    # التحقق من وجود ملفات المشروع
    print("✓ التحقق من الملفات...")
    
    if not (project_dir / "app.py").exists():
        print(" خطأ: لم يتم العثور على ملف app.py")
        print(f"   المسار المتوقع: {project_dir / 'app.py'}")
        input("\nاضغط أي مفتاح للخروج...")
        return
    print("   تم العثور على app.py")
    
    if not (project_dir / "emp.db").exists():
        print(" خطأ: لم يتم العثور على قاعدة البيانات emp.db")
        print(f"   المسار المتوقع: {project_dir / 'emp.db'}")
        input("\nاضغط أي مفتاح للخروج...")
        return
    print("   تم العثور على emp.db")
    
    if not (project_dir / "templates").exists():
        print(" خطأ: لم يتم العثور على مجلد templates")
        print(f"   المسار المتوقع: {project_dir / 'templates'}")
        input("\nاضغط أي مفتاح للخروج...")
        return
    print("  تم العثور على مجلد templates")
    
    if not (project_dir / "static").exists():
        print("خطأ: لم يتم العثور على مجلد static")
        print(f"   المسار المتوقع: {project_dir / 'static'}")
        input("\nاضغط أي مفتاح للخروج...")
        return
    print("   تم العثور على مجلد static")
    
    print()
    
    # التحقق من Python
    print("التحقق من Python...")
    if sys.version_info < (3, 8):
        print(f" خطأ: Python 3.8 أو أحدث مطلوب (لديك {sys.version})")
        input("\nاضغط أي مفتاح للخروج...")
        return
    print(f"  Python {sys.version_info.major}.{sys.version_info.minor} مثبت")
    print()
    
    # إنشاء البيئة الافتراضية إذا لم تكن موجودة
    venv_dir = project_dir / "venv"
    if not venv_dir.exists():
        print("⏳ إنشاء البيئة الافتراضية (قد يستغرق دقيقة)...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True)
            print("  تم إنشاء البيئة الافتراضية")
        except Exception as e:
            print(f"خطأ في إنشاء البيئة الافتراضية:")
            print(f"   {e}")
            input("\nاضغط أي مفتاح للخروج...")
            return
    else:
        print("البيئة الافتراضية موجودة")
    print()
    
    # تحديد مسار Python في البيئة الافتراضية
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"
    
    if not venv_python.exists():
        print(f"خطأ: لم يتم العثور على Python في البيئة الافتراضية")
        print(f"   المسار المتوقع: {venv_python}")
        input("\nاضغط أي مفتاح للخروج...")
        return
    
    # تثبيت المكتبات المطلوبة
    print("التحقق من المكتبات المطلوبة...")
    try:
        # التحقق من وجود Flask
        result = subprocess.run(
            [str(venv_python), "-c", "import flask"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("   تثبيت المكتبات...")
            requirements_file = project_dir / "requirements.txt"
            if requirements_file.exists():
                subprocess.run(
                    [str(venv_pip), "install", "-q", "-r", str(requirements_file)],
                    check=True,
                    capture_output=True,
                    timeout=60
                )
            else:
                subprocess.run(
                    [str(venv_pip), "install", "-q", "flask", "flask-cors", "pandas", "openpyxl"],
                    check=True,
                    capture_output=True,
                    timeout=60
                )
            print("  تم تثبيت المكتبات")
        else:
            print("  جميع المكتبات مثبتة")
    except subprocess.TimeoutExpired:
        print("    تحذير: انتهت مهلة تثبيت المكتبات")
    except Exception as e:
        print(f"    تحذير: {e}")
    print()
    
    # تشغيل Flask
    print("=" * 70)
    print(" تشغيل التطبيق...")
    print("=" * 70)
    print()
    
    # تغيير المجلد الحالي
    os.chdir(str(project_dir))
    
    # تشغيل Flask
    try:
        print(" سجل التطبيق:")
        print("-" * 70)
        
        flask_process = subprocess.Popen(
            [str(venv_python), "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # قراءة السجل
        started = False
        for line in flask_process.stdout:
            print(line.rstrip())
            
            # التحقق من بدء التطبيق
            if "Running on" in line or "WARNING" in line:
                started = True
            
            # إذا بدأ التطبيق، افتح المتصفح
            if started and not hasattr(main, 'browser_opened'):
                time.sleep(1)
                print()
                print("=" * 70)
                print(" التطبيق يعمل الآن!")
                print("=" * 70)
                print()
                print(" فتح المتصفح...")
                webbrowser.open("http://localhost:5000")
                main.browser_opened = True
        
        # انتظر انتهاء العملية
        flask_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف التطبيق بواسطة المستخدم")
    except Exception as e:
        print(f"\n خطأ في تشغيل التطبيق:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        input("\nاضغط أي مفتاح للخروج...")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n تم إيقاف البرنامج")
    except Exception as e:
        print(f"\n خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        input("\nاضغط أي مفتاح للخروج...")
