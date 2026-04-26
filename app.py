
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash,
    send_file, send_from_directory, current_app, g, Response, jsonify
)
import sqlite3
import sys
import os
import shutil
from datetime import datetime
import zipfile
from pathlib import Path
import uuid
import pandas as pd
from io import BytesIO, StringIO
import csv
import time



app = Flask(__name__)
app.secret_key = "any_secret_key"

DB_NAME = "emp.db"

BACKUP_DIR = Path("backups")
DOCUMENTS_DIR = Path("static/documents")

MAX_BACKUPS = 10

BACKUP_DIR.mkdir(exist_ok=True)

DB_NAME = "emp.db"
UPLOAD_FOLDER = "uploads"  # مكان الصور
BASE_URL = "http://localhost:5000"  # عدله إذا كنت ترفعه للسيرفر


UPLOAD_FOLDERS = {
    "employees": "static/documents/employees",
    "books": "static/documents/books",
    "courses": "static/documents/courses",
    "punishments": "static/documents/punishments",
    "committees": "static/documents/committees",
    "promotions": "static/documents/promotions",
    "allowances": "static/documents/allowances",
    "vacations": "static/documents/vacations",
    "delegations": "static/documents/delegations",
     "copybooks": "static/documents/copybooks"
    
}
import sys
import os
import locale

def safe_print(text=""):
    text = str(text)

    replacements = {
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "⚠": "[WARNING]",
        "⏳": "[WAIT]",
        "✓": "[OK]",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or locale.getpreferredencoding(False) or "cp1252"
        text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(text)

for folder in UPLOAD_FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # تفعيل جميع الإعدادات المتقدمة
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
    conn.execute("PRAGMA cache_size = -64000")  # زيادة الكاش إلى 64MB
    conn.execute("PRAGMA synchronous = NORMAL")  # توازن بين السرعة والموثوقية
    conn.execute("PRAGMA temp_store = MEMORY")  # التخزين المؤقت في الذاكرة
    conn.execute("PRAGMA busy_timeout = 30000")  # زيادة وقت الانتظار
    conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory mapping
    return conn

# تفعيل إعدادات SQLite المتقدمة عند بدء التشغيل
def setup_database_advanced():
    conn = get_db()
    try:
        # إعدادات متقدمة للأداء
        conn.execute("PRAGMA auto_vacuum = INCREMENTAL")  # تنظيف تلقائي
        conn.execute("PRAGMA optimize")  # تحسين الاستعلامات
        print("✅ تم تفعيل إعدادات SQLite المتقدمة")
    except Exception as e:
        print(f"❌ خطأ في إعدادات SQLite: {e}")
    finally:
        conn.close()

# استدعاء الإعدادات المتقدمة
setup_database_advanced()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

   
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dept TEXT,
            certificate TEXT,
            gender TEXT,
            job TEXT,    
            job_title TEXT,
            stage TEXT,
            address TEXT,
            phone TEXT,
            notes TEXT
        )
    """)
    cur.execute("PRAGMA table_info(employees)")
    columns = [col[1] for col in cur.fetchall()]

    if "degree" not in columns:
        cur.execute("ALTER TABLE employees ADD COLUMN degree TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employee_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            filename TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            book_number TEXT,
            book_date TEXT,
            book_title TEXT,
            notes TEXT, 
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS book_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            filename TEXT,
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS copybooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            book_number TEXT,
            book_date TEXT,
            book_title TEXT,
            notes TEXT, 
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS copybook_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            copybook_id INTEGER,
            filename TEXT,
            FOREIGN KEY(copybook_id) REFERENCES copybooks(id) ON DELETE CASCADE
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            book_number TEXT,
            book_date TEXT,
            course_date TEXT,
            course_title TEXT,
            course_time_date TEXT,
            result TEXT,
            notes TEXT,    
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            filename TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS punishments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            book_number TEXT,
            book_date TEXT,
            book_title TEXT,
            punishment_type TEXT,
            notes TEXT,    
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS punishment_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            punishment_id INTEGER,
            filename TEXT,
            FOREIGN KEY(punishment_id) REFERENCES punishments(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS committees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        book_number TEXT,
        book_date TEXT,
        committee_title TEXT,
        notes TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
       )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS committee_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER,
        filename TEXT,
        FOREIGN KEY(committee_id) REFERENCES committees(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        book_number TEXT,
        book_date TEXT,
        grade TEXT,
        entitlement_date TEXT,
        job_title TEXT,
        notes TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promotion_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        promotion_id INTEGER,
        filename TEXT,
        FOREIGN KEY(promotion_id) REFERENCES promotions(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS allowances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        book_number TEXT,
        book_date TEXT,
        grade TEXT,
        degree TEXT,        
        stage TEXT,
        entitlement_date TEXT,
        notes TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
         CREATE TABLE IF NOT EXISTS allowance_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        allowance_id INTEGER,
        filename TEXT,
        FOREIGN KEY(allowance_id) REFERENCES allowances(id) ON DELETE CASCADE
       )
    """)

    cur.execute("""
       CREATE TABLE IF NOT EXISTS vacations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        book_number TEXT,
        book_date TEXT,
        vacation_type TEXT,
        duration TEXT,
        start_date TEXT,
        end_date TEXT,
        notes TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
       CREATE TABLE IF NOT EXISTS vacation_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vacation_id INTEGER,
        filename TEXT,
        FOREIGN KEY(vacation_id) REFERENCES vacations(id) ON DELETE CASCADE
       )
    """)

    cur.execute("""
       CREATE TABLE IF NOT EXISTS delegations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        book_number TEXT,
        book_date TEXT,
        delegation_destination TEXT,
        duration TEXT,
        return_date TEXT,
        notes TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
       )
    """)
    cur.execute("""
       CREATE TABLE IF NOT EXISTS delegation_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delegation_id INTEGER,
        filename TEXT,
        FOREIGN KEY(delegation_id) REFERENCES delegations(id) ON DELETE CASCADE
       )
    """)


    conn.commit()
    conn.close()


init_db()

DEPARTMENTS = [
    "مدير القسم",
    "الادارية", 
    "نظم المعلومات",
    "الشبكات",
     "الصيانة",
    "الحكومة الإلكترونية",
    "تصميم المواقع",
    "الذكاء الاصطناعي"
]
def create_backup():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"

    try:
        backup_path.mkdir(parents=True, exist_ok=True)

        # 1. نسخ قاعدة البيانات
        shutil.copy2(DB_NAME, backup_path / DB_NAME)

        # 2. نسخ جميع الصور والمستندات
        if DOCUMENTS_DIR.exists():
            shutil.copytree(
                DOCUMENTS_DIR,
                backup_path / "documents"
            )

        # 3. حذف النسخ القديمة إذا تجاوز الحد
        backups = sorted(
            BACKUP_DIR.iterdir(),
            key=lambda x: x.stat().st_mtime
        )

        if len(backups) > MAX_BACKUPS:
            for old_backup in backups[:-MAX_BACKUPS]:
                shutil.rmtree(old_backup)

        return True, "تم إنشاء النسخة الاحتياطية بنجاح"

    except Exception as e:
        return False, f"خطأ أثناء النسخ الاحتياطي: {e}"
def restore_backup(backup_name):
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        return False, "النسخة غير موجودة"

    try:
        # 1️⃣ استعادة قاعدة البيانات
        if Path(DB_NAME).exists():
            os.remove(DB_NAME)

        shutil.copy2(backup_path / DB_NAME, DB_NAME)

        # 2️⃣ استعادة الصور (بشكل صحيح)
        backup_docs = backup_path / "documents"

        if backup_docs.exists():
            DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

            for item in backup_docs.iterdir():
                dest = DOCUMENTS_DIR / item.name

                if dest.exists():
                    shutil.rmtree(dest)

                shutil.copytree(item, dest)

        return True, "تمت الاستعادة بنجاح (الصور سليمة)"

    except Exception as e:
        return False, f"خطأ أثناء الاستعادة: {e}"

def get_employee_count_by_dept(dept_name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees WHERE dept=?", (dept_name,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_employees_by_dept(dept_name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE dept=? ORDER BY id", (dept_name,))
    employees = cur.fetchall()
    conn.close()
    return employees

def get_all_employees():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees ORDER BY id")
    employees = cur.fetchall()
    conn.close()
    return employees

@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route('/check_duplicate')
def check_duplicate():
    """التحقق من تكرار البيانات"""
    if 'user' not in session:
        return jsonify({'exists': False})
    
    table = request.args.get('table', '')
    field = request.args.get('field', '')
    value = request.args.get('value', '')
    
    if not all([table, field, value]):
        return jsonify({'exists': False})
    
    # السماح فقط بالحقول المحددة
    allowed_fields = ['name', 'book_number']
    if field not in allowed_fields:
        return jsonify({'exists': False})
    
    # السماح فقط بالجداول المحددة
    allowed_tables = [
        'employees',      # name فقط
        'books',          # book_number فقط
        'courses',        # book_number فقط
        'punishments',    # book_number فقط
        'committees',     # book_number فقط
        'promotions',     # book_number فقط
        'allowances',     # book_number فقط
        'vacations',      # book_number فقط
        'delegations'     # book_number فقط
    ]
    
    if table not in allowed_tables:
        return jsonify({'exists': False})
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # التحقق من التكرار
        query = f"SELECT COUNT(*) as count FROM {table} WHERE {field} = ?"
        cur.execute(query, (value,))
        result = cur.fetchone()
        exists = result['count'] > 0 if result else False
        
    except Exception as e:
        print(f"❌ خطأ في التحقق من التكرار: {e}")
        exists = False
    finally:
        conn.close()
    
    return jsonify({'exists': exists})

@app.route('/main')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    departments_data = []
    total_employees = 0
    
    for dept in DEPARTMENTS:
        count = get_employee_count_by_dept(dept)
        total_employees += count
        
        departments_data.append({
            'name': dept,
            'employee_count': count
        })
    
    return render_template('index_employee.html',  # استخدام القالب الحالي
                         departments=departments_data,
                         total_employees=total_employees)
# صفحة عرض موظفين قسم معين
@app.route('/department/<dept_name>')
def department_employees(dept_name):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if dept_name not in DEPARTMENTS:
        return "القسم غير موجود", 404
    
    employees = get_employees_by_dept(dept_name)
    
    return render_template('department_employees.html', 
                         employees=employees, 
                         dept_name=dept_name)


# تغيير اسم المسار من view_thank_letters إلى add_thank_letter
@app.route('/add_thank_letter')
def add_thank_letter():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    dept_name = request.args.get('dept_name', 'جميع الأقسام')
    
    conn = get_db()
    if dept_name == 'جميع الأقسام':
        employees = conn.execute('SELECT * FROM employees').fetchall()
    else:
        employees = conn.execute('SELECT * FROM employees WHERE dept = ?', (dept_name,)).fetchall()
    conn.close()
    
    return render_template('view_thank_letters.html', dept_name=dept_name, employees=employees)

@app.route('/save_thank_letter', methods=['POST'])
def save_thank_letter():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    dept_name = request.args.get('dept_name', 'جميع الأقسام')
    
    # جمع البيانات من النموذج
    letter_number = request.form.get('letter_number', '')
    letter_title = request.form.get('letter_title', '')
    letter_date = request.form.get('letter_date', '')
    letter_content = request.form.get('letter_content', '')
    selected_employees = request.form.getlist('selected_employees')
    
    # التحقق من البيانات
    if not letter_number or not letter_title or not letter_date or not letter_content:
        flash('يرجى ملء جميع الحقول المطلوبة', 'error')
        return redirect(url_for('add_thank_letter', dept_name=dept_name))
    
    if not selected_employees:
        flash('يرجى اختيار موظف واحد على الأقل', 'error')
        return redirect(url_for('add_thank_letter', dept_name=dept_name))
    
    conn = get_db()
    
    try:
        # حفظ كتاب الشكر لكل موظف في جدول الكتب
        book_ids = []
        
        for emp_id in selected_employees:
            # إدخال الكتاب في جدول الكتب
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO books (employee_id, book_number, book_date, book_title, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (emp_id, letter_number, letter_date, letter_title, letter_content))
            book_id = cur.lastrowid
            book_ids.append(book_id)
            
            # حفظ صورة الكتاب لكل موظف
            if 'letter_image' in request.files:
                file = request.files['letter_image']
                if file and file.filename:
                    # إعادة تعيين مؤشر الملف لبدايته
                    file.stream.seek(0)
                    
                    ext = os.path.splitext(file.filename)[1]
                    filename = f"{book_id}_{uuid.uuid4().hex}{ext}"
                    filepath = os.path.join(UPLOAD_FOLDERS["books"], filename)
                    
                    # حفظ الصورة للموظف الحالي
                    file.save(filepath)
                    cur.execute("INSERT INTO book_docs (book_id, filename) VALUES (?, ?)", (book_id, filename))
        
        conn.commit()
        flash(f'تم حفظ كتاب الشكر بنجاح للموظفين المحددين ({len(selected_employees)} موظف)', 'success')
        
    except Exception as e:
        conn.rollback()
        flash('حدث خطأ أثناء حفظ كتاب الشكر', 'error')
        print(f"Error: {e}")
        
    finally:
        conn.close()
    
    # العودة لنفس صفحة الإضافة لإضافة كتاب جديد
    return redirect(url_for('add_thank_letter', dept_name=dept_name))

@app.route('/view_thank_letters')
def view_thank_letters():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    thank_letters = session.get('thank_letters', [])
    return render_template('view_thank_letters.html', thank_letters=thank_letters)

@app.route('/delete_thank_letter/<letter_id>')
def delete_thank_letter(letter_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    
    try:
        # البحث عن كتاب الشكر في الجلسة
        if 'thank_letters' in session:
            letter_to_delete = None
            for letter in session['thank_letters']:
                if letter.get('id') == letter_id:
                    letter_to_delete = letter
                    break
            
            if letter_to_delete and 'book_ids' in letter_to_delete:
                # حذف الكتب من قاعدة البيانات
                for book_id in letter_to_delete['book_ids']:
                    # حذف ملفات الصور المرتبطة
                    cur = conn.cursor()
                    cur.execute("SELECT filename FROM book_docs WHERE book_id=?", (book_id,))
                    files = cur.fetchall()
                    for file in files:
                        try:
                            os.remove(os.path.join(UPLOAD_FOLDERS["books"], file[0]))
                        except:
                            pass
                    
                    # حذف من book_docs
                    cur.execute("DELETE FROM book_docs WHERE book_id=?", (book_id,))
                    # حذف من books
                    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
                
                conn.commit()
            
            # حذف من الجلسة
            session['thank_letters'] = [letter for letter in session['thank_letters'] if letter.get('id') != letter_id]
            session.modified = True
            flash('تم حذف كتاب الشكر بنجاح', 'success')
        
    except Exception as e:
        conn.rollback()
        flash('حدث خطأ أثناء حذف كتاب الشكر', 'error')
        print(f"Error: {e}")
        
    finally:
        conn.close()
    
    return redirect(url_for('view_thank_letters'))

@app.route("/search_documents", methods=["GET", "POST"])
def search_documents():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == "POST":
        search_query = request.form.get("search_query")
        document_type = request.form.get("document_type")
        
        conn = get_db()
        cur = conn.cursor()
        
        # جلب جميع الجداول الموجودة في قاعدة البيانات
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [table[0] for table in cur.fetchall()]
        
        # قائمة الجداول المراد البحث فيها
        target_tables = [
            'employees', 'books', 'courses', 'punishments', 
            'committees', 'promotions', 'allowances', 
            'vacations', 'delegations'
        ]
        
        # تصفية الجداول الموجودة فعلياً
        searchable_tables = []
        for table in target_tables:
            if table in all_tables:
                searchable_tables.append(table)
        
        all_results = []
        
        # البحث في جميع الجداول القابلة للبحث
        for table in searchable_tables:
            try:
                # جلب أسماء الأعمدة في الجدول
                cur.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cur.fetchall()]
                
                if not search_query:
                    query = f"SELECT * FROM {table} LIMIT 10"
                    cur.execute(query)
                else:
                    # بناء استعلام البحث في جميع الأعمدة النصية
                    search_conditions = []
                    params = []
                    
                    for column in columns:
                        # البحث في جميع الحقول النصية والتواريخ
                        if column not in ['id']:
                            search_conditions.append(f"{column} LIKE ?")
                            params.append(f"%{search_query}%")
                    
                    if search_conditions:
                        query = f"SELECT * FROM {table} WHERE {' OR '.join(search_conditions)}"
                        cur.execute(query, params)
                        
                        results = cur.fetchall()
                        
                        # إذا كان هناك بحث، نرتب النتائج حسب الأولوية
                        if search_query and results:
                            scored_results = []
                            for row in results:
                                row_dict = dict(zip(columns, row))
                                score = 0
                                
                                # إعطاء نقاط أعلى للعناوين
                                title_fields = ['title', 'book_title', 'course_title', 'committee_title', 'name']
                                for field in title_fields:
                                    if row_dict.get(field) and search_query.lower() in str(row_dict.get(field, '')).lower():
                                        score += 10
                                
                                # إعطاء نقاط أقل للحقول الأخرى
                                other_fields = ['book_number', 'description', 'notes']
                                for field in other_fields:
                                    if row_dict.get(field) and search_query.lower() in str(row_dict.get(field, '')).lower():
                                        score += 5
                                
                                scored_results.append((score, row))
                            
                            # فرز النتائج حسب النقاط (من الأعلى للأدنى)
                            scored_results.sort(key=lambda x: x[0], reverse=True)
                            results = [row for score, row in scored_results]
                    else:
                        continue
                
                # معالجة النتائج
                for row in results:
                    # تحويل الصف إلى قاموس
                    row_dict = dict(zip(columns, row))
                    
                    # استخراج المعلومات الأساسية للعرض
                    book_number = row_dict.get('book_number') or row_dict.get('id') or row_dict.get('code') or ''
                    title = row_dict.get('title') or row_dict.get('name') or row_dict.get('subject') or ''
                    date_field = row_dict.get('created_at') or row_dict.get('date') or row_dict.get('book_date') or ''
                    
                    # جلب اسم الموظف إذا كان هناك employee_id
                    employee_name = ""
                    employee_id = row_dict.get('employee_id')
                    if employee_id:
                        cur.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
                        employee_result = cur.fetchone()
                        if employee_result:
                            employee_name = employee_result[0]
                    
                    # جلب صورة الكتاب/المستند
                    document_image = ""
                    if table != 'employees':
                        # البحث في جدول المرفقات المناسب
                        docs_table = f"{table}_docs"
                        if docs_table in all_tables:
                            cur.execute(f"SELECT filename FROM {docs_table} WHERE {table}_id = ? LIMIT 1", (row_dict['id'],))
                            image_result = cur.fetchone()
                            if image_result:
                                document_image = image_result[0]
                    
                    all_results.append({
                        'id': row_dict.get('id'),
                        'book_number': str(book_number),
                        'title': str(title),
                        'table_name': table,
                        'date': date_field,
                        'type': get_table_type(table),
                        'employee_name': employee_name,
                        'employee_id': employee_id,
                        'document_image': document_image,
                        'full_data': row_dict  # حفظ جميع البيانات للعرض
                    })
                    
            except Exception as e:
                print(f"Error searching table {table}: {e}")
                continue
        
        conn.close()
        
        return render_template("search_documents.html", 
                             results=all_results,
                             search_query=search_query, 
                             document_type=document_type)
    
    return render_template("search_documents.html", results=[])

def get_table_type(table_name):
    """تحديد نوع الجدول بناءً على اسمه"""
    type_mapping = {
        'employees': 'الموظفين',
        'books': 'الكتب',
        'courses': 'الدورات',
        'punishments': 'العقوبات',
        'committees': 'اللجان',
        'promotions': 'الترفيعات',
        'allowances': 'البدلات',
        'vacations': 'الإجازات',
        'delegations': 'الإيفادات'
    }
    return type_mapping.get(table_name, table_name)

def get_view_route(table_name):
    """الحصول على اسم المسار المناسب لعرض الجدول"""
    route_mapping = {
        'employees': 'view_employee',
        'books': 'view_book', 
        'courses': 'view_course',
        'punishments': 'view_punishment',
        'committees': 'view_committee',
        'promotions': 'view_promotion',
        'allowances': 'view_allowance',
        'vacations': 'view_vacation',
        'delegations': 'view_delegation'
    }
    return route_mapping.get(table_name, 'index')

@app.route("/view/<table_name>/<int:document_id>")
def universal_view(table_name, document_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # التحقق من وجود الجدول
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cur.fetchone():
        flash("❌ الجدول غير موجود", "error")
        return redirect(url_for('search_documents'))
    
    # جلب بيانات المستند
    cur.execute(f"SELECT * FROM {table_name} WHERE id = ?", (document_id,))
    document = cur.fetchone()
    
    if document:
        # تحويل إلى قاموس
        columns = [desc[0] for desc in cur.description]
        document_dict = dict(zip(columns, document))
        
        # جلب اسم الموظف إذا كان هناك employee_id
        employee_name = ""
        employee_id = document_dict.get('employee_id')
        if employee_id:
            cur.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
            employee_result = cur.fetchone()
            if employee_result:
                employee_name = employee_result[0]
        
        # جلب المرفقات إذا وجدت
        attachments = []
        if 'id' in document_dict:
            # محاولة جلب المرفقات من الجداول المختلفة
            attachment_tables = [
                f"{table_name}_docs",
                f"{table_name}_attachments", 
                f"{table_name}_files"
            ]
            
            for att_table in attachment_tables:
                try:
                    cur.execute(f"SELECT * FROM {att_table} WHERE {table_name}_id = ?", (document_id,))
                    table_attachments = cur.fetchall()
                    if table_attachments:
                        # تحويل المرفقات إلى قاموس
                        att_columns = [desc[0] for desc in cur.description]
                        for att in table_attachments:
                            attachments.append(dict(zip(att_columns, att)))
                except:
                    continue
    else:
        document_dict = None
        attachments = []
        employee_name = ""
    
    conn.close()
    
    if not document_dict:
        flash("❌ المستند غير موجود", "error")
        return redirect(url_for('search_documents'))
    
    return render_template("universal_view.html", 
                         document=document_dict,
                         table_name=table_name,
                         attachments=attachments,
                         employee_name=employee_name,
                         document_type=get_table_type(table_name))

@app.route('/add_job') # الرابط في المتصفح
def add_add():
    # تأكد أن الاسم هنا مطابق تماماً لاسم الملف داخل مجلد templates
    return render_template('add_job.html')

@app.route('/all_employees')
def all_employees():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # الحصول على معاملات البحث والعرض
    search_query = request.args.get('search', '')
    display_fields = request.args.getlist('display')  # الحقول المطلوبة للعرض
    
    # معاملات البحث التفصيلي - التصحيح هنا
    search_gender = request.args.get('search_gender')
    search_dept = request.args.get('search_dept')
    search_certificate = request.args.get('search_certificate')
    search_job = request.args.get('search_job')
    search_degree = request.args.get('search_degree')
    search_stage = request.args.get('search_stage')
    search_job_title = request.args.get('search_job_title')
    
    # قوائم التحديد
    selected_genders = []
    selected_departments = []
    selected_certificates = []
    selected_jobs = []
    selected_degrees = []
    selected_stages = []
    selected_job_titles = []
    
    conn = get_db()
    cur = conn.cursor()
    
    # جلب القيم الفريدة من قاعدة البيانات
    cur.execute("SELECT DISTINCT certificate FROM employees WHERE certificate IS NOT NULL AND certificate != '' ORDER BY certificate")
    certificates = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT job FROM employees WHERE job IS NOT NULL AND job != '' ORDER BY job")
    jobs = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT degree FROM employees WHERE degree IS NOT NULL AND degree != '' ORDER BY degree")
    degrees = [str(row[0]) for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT stage FROM employees WHERE stage IS NOT NULL AND stage != '' ORDER BY stage")
    stages = [str(row[0]) for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT job_title FROM employees WHERE job_title IS NOT NULL AND job_title != '' ORDER BY job_title")
    job_titles = [row[0] for row in cur.fetchall()]
    
    # جلب جميع الموظفين
    cur.execute("SELECT * FROM employees ORDER BY id")
    all_employees_data = cur.fetchall()
    conn.close()
    
    # تحويل الصفوف إلى قاموس
    all_employees = []
    for emp in all_employees_data:
        all_employees.append(dict(emp))
    
    # جمع القيم المحددة من الطلب - التصحيح هنا
    
    # للجنس - تحقق من وجود القيمة في request.args
    if search_gender:
        male_value = request.args.get('gender_male')
        female_value = request.args.get('gender_female')
        if male_value == 'ذكر':
            selected_genders.append('ذكر')
        if female_value == 'انثى':
            selected_genders.append('انثى')
    
    # للأقسام - التصحيح المهم هنا
    if search_dept:
        for dept in DEPARTMENTS:
            param_name = f'dept_{dept.replace(" ", "_")}'
            param_value = request.args.get(param_name)
            if param_value == dept:  # تحقق من القيمة الفعلية
                selected_departments.append(dept)
    
    # للشهادات
    if search_certificate:
        for cert in certificates:
            param_name = f'cert_{cert.replace(" ", "_").replace("/", "_")}'
            param_value = request.args.get(param_name)
            if param_value == cert:
                selected_certificates.append(cert)
    
    # للمناصب - التصحيح
    if search_job:
        job_mapping = {
            'job_manager': 'مدير قسم',
            'job_developer': 'معاون مدير قسم',
            'job_designer': 'مسؤول شعبة',
            'job_analyst': 'موظف'
        }
        for param_name, job_value in job_mapping.items():
            param_value = request.args.get(param_name)
            if param_value == job_value:
                selected_jobs.append(job_value)
    
    # للدرجات
    if search_degree:
        for i in range(1, 13):
            param_name = f'degree_{i}'
            param_value = request.args.get(param_name)
            if param_value == str(i):
                selected_degrees.append(str(i))
    
    # للمراحل
    if search_stage:
        for i in range(1, 13):
            param_name = f'stage_{i}'
            param_value = request.args.get(param_name)
            if param_value == str(i):
                selected_stages.append(str(i))
    
    # للعناوين الوظيفية
    if search_job_title:
        for title in job_titles:
            param_name = f'title_{title.replace(" ", "_").replace("/", "_")}'
            param_value = request.args.get(param_name)
            if param_value == title:
                selected_job_titles.append(title)
    
    # تطبيق البحث والتصفية
    filtered_employees = []
    
    for employee in all_employees:
        match = True
        
        # البحث العام
        if search_query:
            query_lower = search_query.lower()
            found = False
            
            # البحث في جميع الحقول النصية
            for field in ['name', 'dept', 'job', 'phone', 'certificate', 
                         'job_title', 'gender']:
                if field in employee and employee[field]:
                    if query_lower in str(employee[field]).lower():
                        found = True
                        break
            
            # البحث في الدرجة والمرحلة كأرقام
            if not found:
                if search_query.isdigit():
                    if employee.get('degree') == int(search_query):
                        found = True
                    elif employee.get('stage') == int(search_query):
                        found = True
            
            if not found:
                match = False
        
        # تصفية الجنس
        if match and selected_genders:
            if employee.get('gender') not in selected_genders:
                match = False
        
        # تصفية الأقسام - التصحيح المهم: يجب أن يكون مطابقاً تماماً
        if match and selected_departments:
            emp_dept = employee.get('dept', '')
            if emp_dept not in selected_departments:
                match = False
        
        # تصفية الشهادات
        if match and selected_certificates:
            if employee.get('certificate') not in selected_certificates:
                match = False
        
        # تصفية المناصب
        if match and selected_jobs:
            emp_job = employee.get('job', '')
            # البحث عن أي من المناصب المحددة في وظيفة الموظف
            job_matched = False
            for selected_job in selected_jobs:
                if selected_job in emp_job:
                    job_matched = True
                    break
            if not job_matched:
                match = False
        
        # تصفية الدرجات
        if match and selected_degrees:
            emp_degree = str(employee.get('degree', ''))
            if emp_degree not in selected_degrees:
                match = False
        
        # تصفية المراحل
        if match and selected_stages:
            emp_stage = str(employee.get('stage', ''))
            if emp_stage not in selected_stages:
                match = False
        
        # تصفية العناوين الوظيفية
        if match and selected_job_titles:
            if employee.get('job_title') not in selected_job_titles:
                match = False
        
        if match:
            filtered_employees.append(employee)
    
    # إذا لم يتم اختيار حقول، استخدم الافتراضية
    if not display_fields:
        display_fields = ['name', 'dept', 'job']
    
    return render_template('all_employees.html', 
                         employees=filtered_employees,
                         search_query=search_query,
                         display_fields=display_fields,
                         departments=DEPARTMENTS,
                         certificates=certificates,
                         jobs=jobs,
                         degrees=degrees,
                         stages=stages,
                         job_titles=job_titles,
                         search_gender=search_gender,
                         search_dept=search_dept,
                         search_certificate=search_certificate,
                         search_job=search_job,
                         search_degree=search_degree,
                         search_stage=search_stage,
                         search_job_title=search_job_title,
                         selected_genders=selected_genders,
                         selected_departments=selected_departments,
                         selected_certificates=selected_certificates,
                         selected_jobs=selected_jobs,
                         selected_degrees=selected_degrees,
                         selected_stages=selected_stages,
                         selected_job_titles=selected_job_titles)

@app.route('/print_employees')
def print_employees():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # استخدام نفس معاملات URL تماماً من صفحة all_employees
    search_query = request.args.get('search', '')
    display_fields = request.args.getlist('display')
    
    # نفس معاملات البحث التفصيلي
    search_gender = request.args.get('search_gender')
    search_dept = request.args.get('search_dept')
    search_certificate = request.args.get('search_certificate')
    search_job = request.args.get('search_job')
    search_degree = request.args.get('search_degree')
    search_stage = request.args.get('search_stage')
    search_job_title = request.args.get('search_job_title')
    
    # استرجاع إعدادات الترتيب من الجلسة
    job_sort_order = session.get('job_sort_order', [
        'مدير قسم',
        'معاون مدير قسم', 
        'مسؤول شعبة',
        'موظف'
    ])
    
    dept_sort_order = session.get('dept_sort_order', [
        "مدير القسم",
        "الادارية", 
        "نظم المعلومات",
        "الشبكات",
        "الصيانة",
        "الحكومة الإلكترونية",
        "تصميم المواقع",
        "الذكاء الاصطناعي"
    ])
    
    # نفس منطق البحث تماماً كما في all_employees
    # قوائم التحديد
    selected_genders = []
    selected_departments = []
    selected_certificates = []
    selected_jobs = []
    selected_degrees = []
    selected_stages = []
    selected_job_titles = []
    
    conn = get_db()
    cur = conn.cursor()
    
    # جلب القيم الفريدة
    cur.execute("SELECT DISTINCT certificate FROM employees WHERE certificate IS NOT NULL AND certificate != '' ORDER BY certificate")
    certificates = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT job FROM employees WHERE job IS NOT NULL AND job != '' ORDER BY job")
    jobs = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT degree FROM employees WHERE degree IS NOT NULL AND degree != '' ORDER BY degree")
    degrees = [str(row[0]) for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT stage FROM employees WHERE stage IS NOT NULL AND stage != '' ORDER BY stage")
    stages = [str(row[0]) for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT job_title FROM employees WHERE job_title IS NOT NULL AND job_title != '' ORDER BY job_title")
    job_titles = [row[0] for row in cur.fetchall()]
    
    # جلب جميع الموظفين
    cur.execute("SELECT * FROM employees")
    all_employees_data = cur.fetchall()
    conn.close()
    
    # تحويل الصفوف إلى قاموس
    all_employees = []
    for emp in all_employees_data:
        all_employees.append(dict(emp))
    
    # جمع القيم المحددة من الطلب - بنفس الكود تماماً
    if search_gender:
        male_value = request.args.get('gender_male')
        female_value = request.args.get('gender_female')
        if male_value == 'ذكر':
            selected_genders.append('ذكر')
        if female_value == 'انثى':
            selected_genders.append('انثى')
    
    if search_dept:
        for dept in DEPARTMENTS:
            param_name = f'dept_{dept.replace(" ", "_")}'
            param_value = request.args.get(param_name)
            if param_value == dept:
                selected_departments.append(dept)
    
    if search_certificate:
        for cert in certificates:
            param_name = f'cert_{cert.replace(" ", "_").replace("/", "_")}'
            param_value = request.args.get(param_name)
            if param_value == cert:
                selected_certificates.append(cert)
    
    if search_job:
        job_mapping = {
            'job_manager': 'مدير قسم',
            'job_developer': 'معاون مدير قسم',
            'job_designer': 'مسؤول شعبة',
            'job_analyst': 'موظف'
        }
        for param_name, job_value in job_mapping.items():
            param_value = request.args.get(param_name)
            if param_value == job_value:
                selected_jobs.append(job_value)
    
    if search_degree:
        for i in range(1, 13):
            param_name = f'degree_{i}'
            param_value = request.args.get(param_name)
            if param_value == str(i):
                selected_degrees.append(str(i))
    
    if search_stage:
        for i in range(1, 13):
            param_name = f'stage_{i}'
            param_value = request.args.get(param_name)
            if param_value == str(i):
                selected_stages.append(str(i))
    
    if search_job_title:
        for title in job_titles:
            param_name = f'title_{title.replace(" ", "_").replace("/", "_")}'
            param_value = request.args.get(param_name)
            if param_value == title:
                selected_job_titles.append(title)
    
    # تطبيق البحث والتصفية - نفس الكود بالضبط
    filtered_employees = []
    
    for employee in all_employees:
        match = True
        
        # البحث العام
        if search_query:
            query_lower = search_query.lower()
            found = False
            
            for field in ['name', 'dept', 'job', 'phone', 'certificate', 
                         'job_title', 'gender']:
                if field in employee and employee[field]:
                    if query_lower in str(employee[field]).lower():
                        found = True
                        break
            
            if not found:
                if search_query.isdigit():
                    if employee.get('degree') == int(search_query):
                        found = True
                    elif employee.get('stage') == int(search_query):
                        found = True
            
            if not found:
                match = False
        
        # تصفية الجنس
        if match and selected_genders:
            if employee.get('gender') not in selected_genders:
                match = False
        
        # تصفية الأقسام
        if match and selected_departments:
            emp_dept = employee.get('dept', '')
            if emp_dept not in selected_departments:
                match = False
        
        # تصفية الشهادات
        if match and selected_certificates:
            if employee.get('certificate') not in selected_certificates:
                match = False
        
        # تصفية المناصب
        if match and selected_jobs:
            emp_job = employee.get('job', '')
            job_matched = False
            for selected_job in selected_jobs:
                if selected_job in emp_job:
                    job_matched = True
                    break
            if not job_matched:
                match = False
        
        # تصفية الدرجات
        if match and selected_degrees:
            emp_degree = str(employee.get('degree', ''))
            if emp_degree not in selected_degrees:
                match = False
        
        # تصفية المراحل
        if match and selected_stages:
            emp_stage = str(employee.get('stage', ''))
            if emp_stage not in selected_stages:
                match = False
        
        # تصفية العناوين الوظيفية
        if match and selected_job_titles:
            if employee.get('job_title') not in selected_job_titles:
                match = False
        
        if match:
            filtered_employees.append(employee)
    
    # تطبيق الترتيب الخاص
    def sort_employee(emp):
        job = emp.get('job', '')
        dept = emp.get('dept', '')
        
        job_priority = len(job_sort_order)
        dept_priority = len(dept_sort_order)
        
        for i, job_title in enumerate(job_sort_order):
            if job_title in job:
                job_priority = i
                break
        
        for i, department in enumerate(dept_sort_order):
            if dept == department:
                dept_priority = i
                break
        
        return (job_priority, dept_priority, emp.get('name', ''))
    
    # ترتيب الموظفين
    filtered_employees.sort(key=sort_employee)
    
    # إذا لم يتم اختيار حقول، استخدم الافتراضية
    if not display_fields:
        display_fields = ['name', 'dept', 'job']
    
    # عرض صفحة الطباعة
    return render_template('print_employees.html',
                         employees=filtered_employees,
                         search_query=search_query,
                         display_fields=display_fields,
                         departments=DEPARTMENTS,
                         certificates=certificates,
                         jobs=jobs,
                         degrees=degrees,
                         stages=stages,
                         job_titles=job_titles,
                         job_sort_order=job_sort_order,
                         dept_sort_order=dept_sort_order,
                         search_gender=search_gender,
                         search_dept=search_dept,
                         search_certificate=search_certificate,
                         search_job=search_job,
                         search_degree=search_degree,
                         search_stage=search_stage,
                         search_job_title=search_job_title,
                         selected_genders=selected_genders,
                         selected_departments=selected_departments,
                         selected_certificates=selected_certificates,
                         selected_jobs=selected_jobs,
                         selected_degrees=selected_degrees,
                         selected_stages=selected_stages,
                         selected_job_titles=selected_job_titles,
                         now=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # تحقق من اسم المستخدم وكلمة المرور
        users = {
            "admin": "1234",
            "sh": "8888",
            "na": "1111",
            "s": "0000"
        }
        
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('index'))  # التوجيه للصفحة الرئيسية الجديدة
        else:
            error = "اسم المستخدم أو كلمة المرور خاطئ"
    
    return render_template('login.html', error=error)

@app.route("/index_employee")
def index_employee():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees ORDER BY id")
    employees = cur.fetchall()
    conn.close()
    return render_template("index_employee.html", employees=employees)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('welcome')) 

@app.route("/add", methods=["GET", "POST"])
def add_employee():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == "POST":
        name = request.form["name"]
        dept = request.form["dept"]
        certificate = request.form.get("certificate")
        gender = request.form["gender"]
        job = request.form.get("job")
        job_title = request.form.get("job_title")
        degree = request.form.get("degree")
        stage = request.form.get("stage")
        address = request.form.get("address")
        phone = request.form.get("phone")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        
        # التحقق من وجود الموظف - إضافة هذا الجزء فقط
        cur.execute("SELECT id FROM employees WHERE name = ?", (name,))
        if cur.fetchone():
            conn.close()
            flash("❌ الموظف موجود مسبقا", "error")
            return render_template("add_employee.html", departments=DEPARTMENTS)
        # نهاية الجزء المضاف

        cur.execute("""
            INSERT INTO employees (name, dept, certificate, gender, job, job_title,degree, stage, address, phone, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
        """, (name, dept, certificate, gender, job, job_title,degree, stage, address, phone, notes))
        emp_id = cur.lastrowid

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{emp_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["employees"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO employee_docs (employee_id, filename) VALUES (?, ?)", (emp_id, filename))

        conn.commit()
        conn.close()
        
        # التوجيه إلى صفحة القسم بعد الإضافة
        return redirect(url_for("department_employees", dept_name=dept))
    
    return render_template("add_employee.html", departments=DEPARTMENTS)

@app.route("/edit/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        dept = request.form["dept"]
        certificate = request.form.get("certificate")
        gender = request.form["gender"]
        job = request.form.get("job")
        job_title = request.form.get("job_title")
        degree = request.form.get("degree")
        stage = request.form.get("stage")
        address = request.form.get("address")
        phone = request.form.get("phone")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE employees 
            SET name=?, dept=?, certificate=?, gender=?, job=?, job_title=?,degree=?, stage=?, address=?, phone=?, notes=?
            WHERE id=?
        """, (name, dept, certificate, gender, job, job_title,degree, stage, address, phone, notes, emp_id))

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{emp_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["employees"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO employee_docs (employee_id, filename) VALUES (?, ?)", (emp_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("department_employees", dept_name=dept))

    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    cur.execute("SELECT * FROM employee_docs WHERE employee_id=?", (emp_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_employee.html", employee=employee, docs=docs, departments=DEPARTMENTS)


@app.route("/delete/<int:emp_id>")
def delete_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    cur = conn.cursor()

    # جلب اسم القسم قبل الحذف للتوجيه الصحيح
    cur.execute("SELECT dept FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    dept_name = employee['dept'] if employee else None

    # حذف كتب الموظف
    cur.execute("SELECT filename FROM book_docs WHERE book_id IN (SELECT id FROM books WHERE employee_id=?)", (emp_id,))
    book_files = cur.fetchall()
    for f in book_files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["books"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM book_docs WHERE book_id IN (SELECT id FROM books WHERE employee_id=?)", (emp_id,))
    cur.execute("DELETE FROM books WHERE employee_id=?", (emp_id,))

    # حذف الدورات
    cur.execute("SELECT filename FROM course_docs WHERE course_id IN (SELECT id FROM courses WHERE employee_id=?)", (emp_id,))
    course_files = cur.fetchall()
    for f in course_files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["courses"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM course_docs WHERE course_id IN (SELECT id FROM courses WHERE employee_id=?)", (emp_id,))
    cur.execute("DELETE FROM courses WHERE employee_id=?", (emp_id,))

    # حذف العقوبات
    cur.execute("SELECT filename FROM punishment_docs WHERE punishment_id IN (SELECT id FROM punishments WHERE employee_id=?)", (emp_id,))
    punishment_files = cur.fetchall()
    for f in punishment_files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["punishments"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM punishment_docs WHERE punishment_id IN (SELECT id FROM punishments WHERE employee_id=?)", (emp_id,))
    cur.execute("DELETE FROM punishments WHERE employee_id=?", (emp_id,))

    # حذف صور الموظف
    cur.execute("SELECT filename FROM employee_docs WHERE employee_id=?", (emp_id,))
    emp_files = cur.fetchall()
    for f in emp_files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["employees"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM employee_docs WHERE employee_id=?", (emp_id,))

    # حذف الموظف نفسه
    cur.execute("DELETE FROM employees WHERE id=?", (emp_id,))

    conn.commit()
    conn.close()
    
    # التوجيه إلى صفحة القسم بعد الحذف
    if dept_name:
        return redirect(url_for("department_employees", dept_name=dept_name))
    else:
        return redirect(url_for("index"))


@app.route("/view/<int:emp_id>")
def view_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    cur.execute("SELECT * FROM employee_docs WHERE employee_id=?", (emp_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("view_employee.html", employee=employee, docs=docs)


@app.route("/delete_doc/<int:doc_id>/<int:emp_id>")
def delete_doc_employee(doc_id, emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM employee_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["employees"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM employee_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_employee", emp_id=emp_id))

@app.route("/books/<int:emp_id>")
def index_book(emp_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    cur.execute("SELECT * FROM books WHERE employee_id=? ORDER BY id", (emp_id,))
    books = cur.fetchall()
    
    conn.close()
    return render_template("index_book.html", books=books, emp_id=emp_id, employee=employee)




@app.route("/view_book/<int:emp_id>/<int:book_id>")
def view_book(emp_id, book_id):
    conn = get_db()
    cur = conn.cursor()
    
    # جلب بيانات الكتاب
    cur.execute("SELECT * FROM books WHERE id=? AND employee_id=?", (book_id, emp_id))
    book = cur.fetchone()
    
    # جلب الملفات المرتبطة بالكتاب
    cur.execute("SELECT * FROM book_docs WHERE book_id=?", (book_id,))
    docs = cur.fetchall()
    
    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    conn.close()
    
    return render_template("view_book.html", book=book, docs=docs, emp_id=emp_id, employee=employee)

@app.route("/books/add/<int:emp_id>", methods=["GET", "POST"])
def add_book(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        notes = request.form.get("notes")  # ✅ إضافة الحقل الجديد

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO books (employee_id, book_number, book_date, book_title, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, book_title, notes))
        book_id = cur.lastrowid

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{book_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["books"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO book_docs (book_id, filename) VALUES (?, ?)", (book_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_book", emp_id=emp_id))
    return render_template("add_book.html", emp_id=emp_id)


@app.route("/books/edit/<int:book_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_book(book_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        notes = request.form.get("notes")  # ✅ إضافة الحقل الجديد

        cur.execute("""
            UPDATE books
            SET book_number=?, book_date=?, book_title=?, notes=?
            WHERE id=?
        """, (book_number, book_date, book_title, notes, book_id))

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{book_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["books"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO book_docs (book_id, filename) VALUES (?, ?)", (book_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_book", emp_id=emp_id))

    cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = cur.fetchone()
    cur.execute("SELECT * FROM book_docs WHERE book_id=?", (book_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_book.html", book=book, docs=docs, emp_id=emp_id)


@app.route("/books/delete/<int:book_id>/<int:emp_id>")
def delete_book(book_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM book_docs WHERE book_id=?", (book_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["books"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM book_docs WHERE book_id=?", (book_id,))
    cur.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_book", emp_id=emp_id))


@app.route("/books/delete_doc/<int:doc_id>/<int:book_id>/<int:emp_id>")
def delete_book_doc(doc_id, book_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM book_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["books"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM book_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_book", book_id=book_id, emp_id=emp_id))

@app.route("/copybooks/<int:emp_id>")
def index_copybook(emp_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    cur.execute("SELECT * FROM copybooks WHERE employee_id=? ORDER BY id", (emp_id,))
    copybooks = cur.fetchall()
    
    conn.close()
    return render_template("index_copybook.html", copybooks=copybooks, emp_id=emp_id, employee=employee)

@app.route("/view_copybook/<int:emp_id>/<int:copybook_id>")
def view_copybook(emp_id, copybook_id):
    conn = get_db()
    cur = conn.cursor()
    
    # جلب بيانات النسخة
    cur.execute("SELECT * FROM copybooks WHERE id=? AND employee_id=?", (copybook_id, emp_id))
    copybook = cur.fetchone()
    
    # جلب الملفات المرتبطة بالنسخة
    cur.execute("SELECT * FROM copybook_docs WHERE copybook_id=?", (copybook_id,))
    docs = cur.fetchall()
    
    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    conn.close()
    
    return render_template("view_copybook.html", copybook=copybook, docs=docs, emp_id=emp_id, employee=employee)

@app.route("/copybooks/add/<int:emp_id>", methods=["GET", "POST"])
def add_copybook(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO copybooks (employee_id, book_number, book_date, book_title, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, book_title, notes))
        copybook_id = cur.lastrowid

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{copybook_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["copybooks"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO copybook_docs (copybook_id, filename) VALUES (?, ?)", (copybook_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_copybook", emp_id=emp_id))
    return render_template("add_copybook.html", emp_id=emp_id)

@app.route("/copybooks/edit/<int:copybook_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_copybook(copybook_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE copybooks
            SET book_number=?, book_date=?, book_title=?, notes=?
            WHERE id=?
        """, (book_number, book_date, book_title, notes, copybook_id))

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{copybook_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["copybooks"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO copybook_docs (copybook_id, filename) VALUES (?, ?)", (copybook_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_copybook", emp_id=emp_id))

    cur.execute("SELECT * FROM copybooks WHERE id=?", (copybook_id,))
    copybook = cur.fetchone()
    cur.execute("SELECT * FROM copybook_docs WHERE copybook_id=?", (copybook_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_copybook.html", copybook=copybook, docs=docs, emp_id=emp_id)

@app.route("/copybooks/delete/<int:copybook_id>/<int:emp_id>")
def delete_copybook(copybook_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM copybook_docs WHERE copybook_id=?", (copybook_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["copybooks"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM copybook_docs WHERE copybook_id=?", (copybook_id,))
    cur.execute("DELETE FROM copybooks WHERE id=?", (copybook_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_copybook", emp_id=emp_id))

@app.route("/copybooks/delete_doc/<int:doc_id>/<int:copybook_id>/<int:emp_id>")
def delete_copybook_doc(doc_id, copybook_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM copybook_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["copybooks"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM copybook_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_copybook", copybook_id=copybook_id, emp_id=emp_id))

@app.route("/courses/<int:emp_id>")
def index_course(emp_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    cur.execute("SELECT * FROM courses WHERE employee_id=? ORDER BY id", (emp_id,))
    courses = cur.fetchall()
    
    conn.close()
    return render_template("index_course.html", courses=courses, emp_id=emp_id, employee=employee)


@app.route("/view_course/<int:emp_id>/<int:course_id>")
def view_course(emp_id, course_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM courses WHERE id=? AND employee_id=?", (course_id, emp_id))
    course = cur.fetchone()
    
    cur.execute("SELECT * FROM course_docs WHERE course_id=?", (course_id,))
    docs = cur.fetchall()
    
    conn.close()
    return render_template("view_course.html", course=course, docs=docs)


@app.route("/courses/add/<int:emp_id>", methods=["GET", "POST"])
def add_course(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        course_date = request.form.get("course_date")  # ✅ جديد
        course_title = request.form.get("course_title")
        course_time_date = request.form.get("course_time_date")  # ✅ جديد
        result = request.form.get("result")
        notes = request.form.get("notes")  # ✅ جديد

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO courses (employee_id, book_number, book_date, course_date, course_title, course_time_date, result, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, course_date, course_title, course_time_date, result, notes))
        course_id = cur.lastrowid

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{course_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["courses"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO course_docs (course_id, filename) VALUES (?, ?)", (course_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_course", emp_id=emp_id))
    return render_template("add_course.html", emp_id=emp_id)


@app.route("/courses/edit/<int:course_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_course(course_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        course_date = request.form.get("course_date")  # ✅ جديد
        course_title = request.form.get("course_title")
        course_time_date = request.form.get("course_time_date")  # ✅ جديد
        result = request.form.get("result")
        notes = request.form.get("notes")  # ✅ جديد

        cur.execute("""
            UPDATE courses
            SET book_number=?, book_date=?, course_date=?, course_title=?, course_time_date=?, result=?, notes=?
            WHERE id=?
        """, (book_number, book_date, course_date, course_title, course_time_date, result, notes, course_id))

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{course_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["courses"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO course_docs (course_id, filename) VALUES (?, ?)", (course_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_course", emp_id=emp_id))

    cur.execute("SELECT * FROM courses WHERE id=?", (course_id,))
    course = cur.fetchone()
    cur.execute("SELECT * FROM course_docs WHERE course_id=?", (course_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_course.html", course=course, docs=docs, emp_id=emp_id)


@app.route("/courses/delete/<int:course_id>/<int:emp_id>")
def delete_course(course_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM course_docs WHERE course_id=?", (course_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["courses"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM course_docs WHERE course_id=?", (course_id,))
    cur.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_course", emp_id=emp_id))


@app.route("/courses/delete_doc/<int:doc_id>/<int:course_id>/<int:emp_id>")
def delete_course_doc(doc_id, course_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM course_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["courses"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM course_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_course", course_id=course_id, emp_id=emp_id))

@app.route("/punishments/<int:emp_id>")
def index_punishment(emp_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()
    
    cur.execute("SELECT * FROM punishments WHERE employee_id=? ORDER BY id", (emp_id,))
    punishments = cur.fetchall()
    
    conn.close()
    return render_template("index_punishment.html", punishments=punishments, emp_id=emp_id, employee=employee)


@app.route("/view_punishment/<int:emp_id>/<int:punishment_id>")
def view_punishment(emp_id, punishment_id):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM punishments WHERE id=? AND employee_id=?", (punishment_id, emp_id))
    punishment = cur.fetchone()
    
    cur.execute("SELECT * FROM punishment_docs WHERE punishment_id=?", (punishment_id,))
    docs = cur.fetchall()
    
    conn.close()
    return render_template("view_punishment.html", punishment=punishment, docs=docs)


@app.route("/punishments/add/<int:emp_id>", methods=["GET", "POST"])
def add_punishment(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        punishment_type = request.form.get("punishment_type")
        notes = request.form.get("notes")  # ✅ حقل جديد

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO punishments (employee_id, book_number, book_date, book_title, punishment_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, book_title, punishment_type, notes))
        punishment_id = cur.lastrowid

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{punishment_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["punishments"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO punishment_docs (punishment_id, filename) VALUES (?, ?)", (punishment_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_punishment", emp_id=emp_id))
    return render_template("add_punishment.html", emp_id=emp_id)


@app.route("/punishments/edit/<int:punishment_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_punishment(punishment_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        book_title = request.form.get("book_title")
        punishment_type = request.form.get("punishment_type")
        notes = request.form.get("notes")  # ✅ حقل جديد

        cur.execute("""
            UPDATE punishments
            SET book_number=?, book_date=?, book_title=?, punishment_type=?, notes=?
            WHERE id=?
        """, (book_number, book_date, book_title, punishment_type, notes, punishment_id))

        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{punishment_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["punishments"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO punishment_docs (punishment_id, filename) VALUES (?, ?)", (punishment_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_punishment", emp_id=emp_id))

    cur.execute("SELECT * FROM punishments WHERE id=?", (punishment_id,))
    punishment = cur.fetchone()
    cur.execute("SELECT * FROM punishment_docs WHERE punishment_id=?", (punishment_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_punishment.html", punishment=punishment, docs=docs, emp_id=emp_id)


@app.route("/punishments/delete/<int:punishment_id>/<int:emp_id>")
def delete_punishment(punishment_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM punishment_docs WHERE punishment_id=?", (punishment_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["punishments"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM punishment_docs WHERE punishment_id=?", (punishment_id,))
    cur.execute("DELETE FROM punishments WHERE id=?", (punishment_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_punishment", emp_id=emp_id))


@app.route("/punishments/delete_doc/<int:doc_id>/<int:punishment_id>/<int:emp_id>")
def delete_punishment_doc(doc_id, punishment_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM punishment_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["punishments"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM punishment_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_punishment", punishment_id=punishment_id, emp_id=emp_id))


@app.route("/committees/<int:emp_id>")
def index_committee(emp_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()

    # جلب كل اللجان الخاصة بالموظف
    cur.execute("SELECT * FROM committees WHERE employee_id=? ORDER BY id", (emp_id,))
    committees = cur.fetchall()

    conn.close()
    return render_template("index_committee.html", committees=committees, emp_id=emp_id, employee=employee)


@app.route("/view_committee/<int:emp_id>/<int:committee_id>")
def view_committee(emp_id, committee_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب تفاصيل اللجنة
    cur.execute("SELECT * FROM committees WHERE id=? AND employee_id=?", (committee_id, emp_id))
    committee = cur.fetchone()

    # جلب الملفات المرتبطة باللجنة
    cur.execute("SELECT * FROM committee_docs WHERE committee_id=?", (committee_id,))
    docs = cur.fetchall()

    conn.close()
    return render_template("view_committee.html", committee=committee, docs=docs)


@app.route("/committees/add/<int:emp_id>", methods=["GET", "POST"])
def add_committee(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        committee_title = request.form.get("committee_title")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO committees (employee_id, book_number, book_date, committee_title, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, committee_title, notes))
        committee_id = cur.lastrowid

        # حفظ الملفات المرفقة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{committee_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["committees"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO committee_docs (committee_id, filename) VALUES (?, ?)", (committee_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_committee", emp_id=emp_id))
    return render_template("add_committee.html", emp_id=emp_id)


@app.route("/committees/edit/<int:committee_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_committee(committee_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        committee_title = request.form.get("committee_title")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE committees
            SET book_number=?, book_date=?, committee_title=?, notes=?
            WHERE id=?
        """, (book_number, book_date, committee_title, notes, committee_id))

        # حفظ الملفات الجديدة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{committee_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["committees"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO committee_docs (committee_id, filename) VALUES (?, ?)", (committee_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_committee", emp_id=emp_id))

    cur.execute("SELECT * FROM committees WHERE id=?", (committee_id,))
    committee = cur.fetchone()
    cur.execute("SELECT * FROM committee_docs WHERE committee_id=?", (committee_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_committee.html", committee=committee, docs=docs, emp_id=emp_id)


@app.route("/committees/delete/<int:committee_id>/<int:emp_id>")
def delete_committee(committee_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM committee_docs WHERE committee_id=?", (committee_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["committees"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM committee_docs WHERE committee_id=?", (committee_id,))
    cur.execute("DELETE FROM committees WHERE id=?", (committee_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_committee", emp_id=emp_id))


@app.route("/committees/delete_doc/<int:doc_id>/<int:committee_id>/<int:emp_id>")
def delete_committee_doc(doc_id, committee_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM committee_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["committees"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM committee_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_committee", committee_id=committee_id, emp_id=emp_id))


@app.route("/promotions/<int:emp_id>")
def index_promotion(emp_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()

    # جلب كل الترفيعات الخاصة بالموظف
    cur.execute("SELECT * FROM promotions WHERE employee_id=? ORDER BY id", (emp_id,))
    promotions = cur.fetchall()

    conn.close()
    return render_template("index_promotion.html", promotions=promotions, emp_id=emp_id, employee=employee)


@app.route("/view_promotion/<int:emp_id>/<int:promotion_id>")
def view_promotion(emp_id, promotion_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب تفاصيل الترفيع
    cur.execute("SELECT * FROM promotions WHERE id=? AND employee_id=?", (promotion_id, emp_id))
    promotion = cur.fetchone()

    # جلب الملفات المرتبطة بالترفيع
    cur.execute("SELECT * FROM promotion_docs WHERE promotion_id=?", (promotion_id,))
    docs = cur.fetchall()

    conn.close()
    return render_template("view_promotion.html", promotion=promotion, docs=docs)


@app.route("/promotions/add/<int:emp_id>", methods=["GET", "POST"])
def add_promotion(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        grade = request.form.get("grade")
        entitlement_date = request.form.get("entitlement_date")
        job_title = request.form.get("job_title")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO promotions (employee_id, book_number, book_date, grade, entitlement_date, job_title, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, grade, entitlement_date, job_title, notes))
        promotion_id = cur.lastrowid

        # حفظ الملفات المرفقة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{promotion_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["promotions"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO promotion_docs (promotion_id, filename) VALUES (?, ?)", (promotion_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_promotion", emp_id=emp_id))
    return render_template("add_promotion.html", emp_id=emp_id)


@app.route("/promotions/edit/<int:promotion_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_promotion(promotion_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        grade = request.form.get("grade")
        entitlement_date = request.form.get("entitlement_date")
        job_title = request.form.get("job_title")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE promotions
            SET book_number=?, book_date=?, grade=?, entitlement_date=?, job_title=?, notes=?
            WHERE id=?
        """, (book_number, book_date, grade, entitlement_date, job_title, notes, promotion_id))

        # حفظ الملفات الجديدة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{promotion_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["promotions"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO promotion_docs (promotion_id, filename) VALUES (?, ?)", (promotion_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_promotion", emp_id=emp_id))

    cur.execute("SELECT * FROM promotions WHERE id=?", (promotion_id,))
    promotion = cur.fetchone()
    cur.execute("SELECT * FROM promotion_docs WHERE promotion_id=?", (promotion_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_promotion.html", promotion=promotion, docs=docs, emp_id=emp_id)


@app.route("/promotions/delete/<int:promotion_id>/<int:emp_id>")
def delete_promotion(promotion_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM promotion_docs WHERE promotion_id=?", (promotion_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["promotions"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM promotion_docs WHERE promotion_id=?", (promotion_id,))
    cur.execute("DELETE FROM promotions WHERE id=?", (promotion_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_promotion", emp_id=emp_id))


@app.route("/promotions/delete_doc/<int:doc_id>/<int:promotion_id>/<int:emp_id>")
def delete_promotion_doc(doc_id, promotion_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM promotion_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["promotions"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM promotion_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_promotion", promotion_id=promotion_id, emp_id=emp_id))


@app.route("/allowances/<int:emp_id>")
def index_allowance(emp_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()

    # جلب كل العلاوات الخاصة بالموظف
    cur.execute("SELECT * FROM allowances WHERE employee_id=? ORDER BY id", (emp_id,))
    allowances = cur.fetchall()

    conn.close()
    return render_template("index_allowance.html", allowances=allowances, emp_id=emp_id, employee=employee)


@app.route("/view_allowance/<int:emp_id>/<int:allowance_id>")
def view_allowance(emp_id, allowance_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب تفاصيل العلاوة
    cur.execute("SELECT * FROM allowances WHERE id=? AND employee_id=?", (allowance_id, emp_id))
    allowance = cur.fetchone()

    # جلب الملفات المرتبطة بالعلاوة
    cur.execute("SELECT * FROM allowance_docs WHERE allowance_id=?", (allowance_id,))
    docs = cur.fetchall()

    conn.close()
    return render_template("view_allowance.html", allowance=allowance, docs=docs)


@app.route("/allowances/add/<int:emp_id>", methods=["GET", "POST"])
def add_allowance(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        grade = request.form.get("grade")
        stage = request.form.get("stage")
        entitlement_date = request.form.get("entitlement_date")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO allowances (employee_id, book_number, book_date, grade, stage, entitlement_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, grade, stage, entitlement_date, notes))
        allowance_id = cur.lastrowid

        # حفظ الملفات المرفقة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{allowance_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["allowances"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO allowance_docs (allowance_id, filename) VALUES (?, ?)", (allowance_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_allowance", emp_id=emp_id))
    return render_template("add_allowance.html", emp_id=emp_id)


@app.route("/allowances/edit/<int:allowance_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_allowance(allowance_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        grade = request.form.get("grade")
        stage = request.form.get("stage")
        entitlement_date = request.form.get("entitlement_date")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE allowances
            SET book_number=?, book_date=?, grade=?, stage=?, entitlement_date=?, notes=?
            WHERE id=?
        """, (book_number, book_date, grade, stage, entitlement_date, notes, allowance_id))

        # حفظ الملفات الجديدة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{allowance_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["allowances"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO allowance_docs (allowance_id, filename) VALUES (?, ?)", (allowance_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_allowance", emp_id=emp_id))

    cur.execute("SELECT * FROM allowances WHERE id=?", (allowance_id,))
    allowance = cur.fetchone()
    cur.execute("SELECT * FROM allowance_docs WHERE allowance_id=?", (allowance_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_allowance.html", allowance=allowance, docs=docs, emp_id=emp_id)


@app.route("/allowances/delete/<int:allowance_id>/<int:emp_id>")
def delete_allowance(allowance_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM allowance_docs WHERE allowance_id=?", (allowance_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["allowances"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM allowance_docs WHERE allowance_id=?", (allowance_id,))
    cur.execute("DELETE FROM allowances WHERE id=?", (allowance_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_allowance", emp_id=emp_id))


@app.route("/allowances/delete_doc/<int:doc_id>/<int:allowance_id>/<int:emp_id>")
def delete_allowance_doc(doc_id, allowance_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM allowance_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["allowances"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM allowance_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_allowance", allowance_id=allowance_id, emp_id=emp_id))


@app.route("/vacations/<int:emp_id>")
def index_vacation(emp_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()

    # جلب كل الإجازات الخاصة بالموظف
    cur.execute("SELECT * FROM vacations WHERE employee_id=? ORDER BY id", (emp_id,))
    vacations = cur.fetchall()

    conn.close()
    return render_template("index_vacation.html", vacations=vacations, emp_id=emp_id, employee=employee)


@app.route("/view_vacation/<int:emp_id>/<int:vacation_id>")
def view_vacation(emp_id, vacation_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب تفاصيل الإجازة
    cur.execute("SELECT * FROM vacations WHERE id=? AND employee_id=?", (vacation_id, emp_id))
    vacation = cur.fetchone()

    # جلب الملفات المرتبطة بالإجازة
    cur.execute("SELECT * FROM vacation_docs WHERE vacation_id=?", (vacation_id,))
    docs = cur.fetchall()

    conn.close()
    return render_template("view_vacation.html", vacation=vacation, docs=docs)


@app.route("/vacations/add/<int:emp_id>", methods=["GET", "POST"])
def add_vacation(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        vacation_type = request.form.get("vacation_type")
        duration = request.form.get("duration")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO vacations (employee_id, book_number, book_date, vacation_type, duration, start_date, end_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, vacation_type, duration, start_date, end_date, notes))
        vacation_id = cur.lastrowid

        # حفظ الملفات المرفقة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{vacation_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["vacations"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO vacation_docs (vacation_id, filename) VALUES (?, ?)", (vacation_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_vacation", emp_id=emp_id))
    return render_template("add_vacation.html", emp_id=emp_id)


@app.route("/vacations/edit/<int:vacation_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_vacation(vacation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        vacation_type = request.form.get("vacation_type")
        duration = request.form.get("duration")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE vacations
            SET book_number=?, book_date=?, vacation_type=?, duration=?, start_date=?, end_date=?, notes=?
            WHERE id=?
        """, (book_number, book_date, vacation_type, duration, start_date, end_date, notes, vacation_id))

        # حفظ الملفات الجديدة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{vacation_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["vacations"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO vacation_docs (vacation_id, filename) VALUES (?, ?)", (vacation_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_vacation", emp_id=emp_id))

    cur.execute("SELECT * FROM vacations WHERE id=?", (vacation_id,))
    vacation = cur.fetchone()
    cur.execute("SELECT * FROM vacation_docs WHERE vacation_id=?", (vacation_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_vacation.html", vacation=vacation, docs=docs, emp_id=emp_id)


@app.route("/vacations/delete/<int:vacation_id>/<int:emp_id>")
def delete_vacation(vacation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM vacation_docs WHERE vacation_id=?", (vacation_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["vacations"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM vacation_docs WHERE vacation_id=?", (vacation_id,))
    cur.execute("DELETE FROM vacations WHERE id=?", (vacation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_vacation", emp_id=emp_id))


@app.route("/vacations/delete_doc/<int:doc_id>/<int:vacation_id>/<int:emp_id>")
def delete_vacation_doc(doc_id, vacation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM vacation_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["vacations"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM vacation_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_vacation", vacation_id=vacation_id, emp_id=emp_id))


@app.route("/delegations/<int:emp_id>")
def index_delegation(emp_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب بيانات الموظف
    cur.execute("SELECT * FROM employees WHERE id=?", (emp_id,))
    employee = cur.fetchone()

    # جلب كل الإيفادات الخاصة بالموظف
    cur.execute("SELECT * FROM delegations WHERE employee_id=? ORDER BY id", (emp_id,))
    delegations = cur.fetchall()

    conn.close()
    return render_template("index_delegation.html", delegations=delegations, emp_id=emp_id, employee=employee)


@app.route("/view_delegation/<int:emp_id>/<int:delegation_id>")
def view_delegation(emp_id, delegation_id):
    conn = get_db()
    cur = conn.cursor()

    # جلب تفاصيل الإيفادة
    cur.execute("SELECT * FROM delegations WHERE id=? AND employee_id=?", (delegation_id, emp_id))
    delegation = cur.fetchone()

    # جلب الملفات المرتبطة بالإيفادة
    cur.execute("SELECT * FROM delegation_docs WHERE delegation_id=?", (delegation_id,))
    docs = cur.fetchall()

    conn.close()
    return render_template("view_delegation.html", delegation=delegation, docs=docs)


@app.route("/delegations/add/<int:emp_id>", methods=["GET", "POST"])
def add_delegation(emp_id):
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        delegation_destination = request.form.get("delegation_destination")
        duration = request.form.get("duration")
        return_date = request.form.get("return_date")
        notes = request.form.get("notes")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO delegations (employee_id, book_number, book_date, delegation_destination, duration, return_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, book_number, book_date, delegation_destination, duration, return_date, notes))
        delegation_id = cur.lastrowid

        # حفظ الملفات المرفقة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{delegation_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["delegations"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO delegation_docs (delegation_id, filename) VALUES (?, ?)", (delegation_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_delegation", emp_id=emp_id))
    return render_template("add_delegation.html", emp_id=emp_id)


@app.route("/delegations/edit/<int:delegation_id>/<int:emp_id>", methods=["GET", "POST"])
def edit_delegation(delegation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        book_number = request.form.get("book_number")
        book_date = request.form.get("book_date")
        delegation_destination = request.form.get("delegation_destination")
        duration = request.form.get("duration")
        return_date = request.form.get("return_date")
        notes = request.form.get("notes")

        cur.execute("""
            UPDATE delegations
            SET book_number=?, book_date=?, delegation_destination=?, duration=?, return_date=?, notes=?
            WHERE id=?
        """, (book_number, book_date, delegation_destination, duration, return_date, notes, delegation_id))

        # حفظ الملفات الجديدة
        files = request.files.getlist("docs")
        for file in files:
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{delegation_id}_{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(UPLOAD_FOLDERS["delegations"], filename)
                file.save(filepath)
                cur.execute("INSERT INTO delegation_docs (delegation_id, filename) VALUES (?, ?)", (delegation_id, filename))

        conn.commit()
        conn.close()
        return redirect(url_for("index_delegation", emp_id=emp_id))

    cur.execute("SELECT * FROM delegations WHERE id=?", (delegation_id,))
    delegation = cur.fetchone()
    cur.execute("SELECT * FROM delegation_docs WHERE delegation_id=?", (delegation_id,))
    docs = cur.fetchall()
    conn.close()
    return render_template("edit_delegation.html", delegation=delegation, docs=docs, emp_id=emp_id)


@app.route("/delegations/delete/<int:delegation_id>/<int:emp_id>")
def delete_delegation(delegation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM delegation_docs WHERE delegation_id=?", (delegation_id,))
    files = cur.fetchall()
    for f in files:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["delegations"], f[0]))
        except:
            pass
    cur.execute("DELETE FROM delegation_docs WHERE delegation_id=?", (delegation_id,))
    cur.execute("DELETE FROM delegations WHERE id=?", (delegation_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index_delegation", emp_id=emp_id))


@app.route("/delegations/delete_doc/<int:doc_id>/<int:delegation_id>/<int:emp_id>")
def delete_delegation_doc(doc_id, delegation_id, emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM delegation_docs WHERE id=?", (doc_id,))
    file = cur.fetchone()
    if file:
        try:
            os.remove(os.path.join(UPLOAD_FOLDERS["delegations"], file[0]))
        except:
            pass
    cur.execute("DELETE FROM delegation_docs WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_delegation", delegation_id=delegation_id, emp_id=emp_id))

@app.route("/export/all")
def export_all_system():
    import sqlite3, pandas as pd, os, io
    from flask import send_file

    DB_NAME = "emp.db"  # اسم قاعدة البيانات
    FILES_DIR = "uploads"  # مجلد الصور
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ترتيب الوظائف
    job_order = ["مدير القسم", "معاون مدير قسم", "مسؤول الشعبة", "الموظف"]

    # --- Export Employees with sort ---
    cur.execute("SELECT * FROM employees")
    employees = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in cur.description])

    if "job_title" in employees.columns:
        employees["job_order"] = employees["job_title"].apply(
            lambda x: job_order.index(x) if x in job_order else len(job_order)
        )
        employees = employees.sort_values("job_order").drop(columns=["job_order"])

    # --- Function to fetch docs & add hyperlink column safely ---
    def fetch_with_docs(main_table, foreign_key, docs_table):
        cur.execute(f"SELECT * FROM {main_table}")
        df = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in cur.description])
        if df.empty:
            return df

        # تحقق من وجود العمود foreign_key في جدول المستندات
        cur.execute(f"PRAGMA table_info({docs_table})")
        doc_cols = [col[1] for col in cur.fetchall()]
        if foreign_key not in doc_cols:
            df["documents"] = ""
            return df

        links = []
        for _, row in df.iterrows():
            cur.execute(f"SELECT filename FROM {docs_table} WHERE {foreign_key}=?", (row["id"],))
            files = cur.fetchall()

            file_links = []
            for f in files:
                full_path = os.path.abspath(os.path.join(FILES_DIR, f[0]))
                hyperlink = f'=HYPERLINK("{full_path}", "{f[0]}")'
                file_links.append(hyperlink)

            links.append(", ".join(file_links))

        df["documents"] = links
        return df

    # --- Related tables list with employee_id ---
    tables = [
        ("books", "employee_id", "book_docs"),
        ("copybooks", "employee_id", "copybook_docs"),
        ("courses", "employee_id", "course_docs"),
        ("punishments", "employee_id", "punishment_docs"),
        ("committees", "employee_id", "committee_docs"),
        ("promotions", "employee_id", "promotion_docs"),
        ("allowances", "employee_id", "allowance_docs"),
        ("vacations", "employee_id", "vacation_docs"),
        ("delegations", "employee_id", "delegation_docs")
    ]

    # --- قاموس ترجمة الأعمدة لكل جدول ---
    arabic_columns = {
        "employees": {
            "id": "رقم الموظف",
            "name": "الاسم",
            "dept": "القسم",
            "certificate": "الشهادة",
            "gender": "الجنس",
            "job": "الوظيفة",
            "job_title": "المسمى الوظيفي",
            "stage": "المرحلة",
            "address": "العنوان",
            "phone": "الهاتف",
            "notes": "ملاحظات",
            "degree": "الدرجة",
            "documents": "المستندات"
        },
        "books": {
            "id": "رقم الكتاب",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "book_title": "عنوان الكتاب",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "copybooks": {
            "id": "رقم نسخة الكتاب",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "book_title": "عنوان الكتاب",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "courses": {
            "id": "رقم الدورة",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "course_date": "تاريخ الدورة",
            "course_title": "عنوان الدورة",
            "course_time_date": "وقت الدورة",
            "result": "النتيجة",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "punishments": {
            "id": "رقم العقوبة",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "book_title": "عنوان الكتاب",
            "punishment_type": "نوع العقوبة",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "committees": {
            "id": "رقم اللجنة",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "committee_title": "عنوان اللجنة",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "promotions": {
            "id": "رقم الترقية",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "grade": "الدرجة",
            "entitlement_date": "تاريخ الاستحقاق",
            "job_title": "المسمى الوظيفي",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "allowances": {
            "id": "رقم البدل",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "grade": "الدرجة",
            "degree": "الدرجة العلمية",
            "stage": "المرحلة",
            "entitlement_date": "تاريخ الاستحقاق",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "vacations": {
            "id": "رقم الإجازة",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "vacation_type": "نوع الإجازة",
            "duration": "المدة",
            "start_date": "تاريخ البدء",
            "end_date": "تاريخ الانتهاء",
            "notes": "ملاحظات",
            "documents": "المستندات"
        },
        "delegations": {
            "id": "رقم الإيفاد",
            "employee_id": "رقم الموظف",
            "book_number": "رقم الكتاب",
            "book_date": "تاريخ الكتاب",
            "delegation_destination": "جهة الإيفاد",
            "duration": "المدة",
            "return_date": "تاريخ العودة",
            "notes": "ملاحظات",
            "documents": "المستندات"
        }
    }

    # --- Create Excel file ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # تصدير الموظفين مع أسماء الأعمدة بالعربي
        employees.rename(columns=arabic_columns["employees"], inplace=True)
        employees.to_excel(writer, sheet_name="الموظفين", index=False)

        for table, fk, docs_table in tables:
            df = fetch_with_docs(table, fk, docs_table)
            if not df.empty:
                if table in arabic_columns:
                    df.rename(columns=arabic_columns[table], inplace=True)
                    writer.sheets = writer.sheets  # ضروري لتجنب overwrite
                    df.to_excel(writer, sheet_name=table.capitalize() if table != "books" else "الكتب", index=False)

    output.seek(0)
    conn.close()

    return send_file(
        output,
        as_attachment=True,
        download_name="system_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





@app.route("/backup", methods=["POST"])
def backup():
    success, message = create_backup()
    flash(message, "success" if success else "danger")
    return redirect(url_for("backup_page"))
@app.route("/restore/<backup_name>", methods=["POST"])
def restore(backup_name):
    success, message = restore_backup(backup_name)
    flash(message, "success" if success else "danger")
    return redirect(url_for("backup_page"))
@app.route("/backup-page")
def backup_page():
    backups = sorted(
        [b.name for b in BACKUP_DIR.iterdir() if b.is_dir()],
        reverse=True
    )
    return render_template("backup.html", backups=backups)
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response
@app.route("/delete-backup/<backup_name>", methods=["POST"])
def delete_backup(backup_name):
    backup_path = BACKUP_DIR / backup_name
    if backup_path.exists():
        try:
            shutil.rmtree(backup_path)
            flash(f"تم حذف النسخة الاحتياطية: {backup_name}", "success")
        except Exception as e:
            flash(f"خطأ أثناء الحذف: {e}", "danger")
    else:
        flash("النسخة غير موجودة", "warning")
    return redirect(url_for("backup_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


