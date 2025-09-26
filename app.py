from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import time
import sqlite3
import os
import json
from werkzeug.utils import secure_filename
from twilio.rest import Client
from offline_chatbot import offline_chatbot

# -------------------- Google Gemini Config --------------------
from google import genai
GOOGLE_API_KEY = "AIzaSyBobsRtxNyUxHZf2Fm4g8Zq7eRGpQyj7Ao"
client = genai.Client(api_key=GOOGLE_API_KEY)

# -------------------- Translations --------------------
translations = {
    'en': {
        'title': 'EduConnect',
        'home': 'Home',
        'features': 'Features',
        'contact': 'Contact',
        'faqs': 'FAQs',
        'about': 'About',
        'student': 'Student',
        'admin': 'Admin',
        'welcome_title': 'Welcome to EduConnect',
        'welcome_subtitle': 'Empowering Rural Education with Technology',
        'admin_panel': 'Admin Panel',
        'student_panel': 'Student Panel',
        'key_features': 'Key Features',
        'features_desc': 'Making learning engaging and accessible for every student',
        'voice_chatbot': '🎙 Voice Chatbot',
        'voice_desc': 'AI-powered assistant to help students learn anytime.',
        'materials': '📚 Learning Materials',
        'materials_desc': 'Teachers can upload resources for students to access easily.',
        'quizzes': '🏆 Gamified Quizzes',
        'quizzes_desc': 'Interactive quizzes & rewards for better engagement.',
        'chatbot_name': 'Educonnector',
        'chat_greeting': 'Hello! How can I help you?',
        'chat_placeholder': 'Type or speak...',
        'footer': '© 2025 EduConnect | Building Brighter Futures',
        'language': 'Language',
        'login': 'Login',
        'welcome_back_student': 'Welcome Back, Student!',
        'login_description': 'Log in with your email and password to access your personalized learning dashboard.',
        'student_login': 'Student Login',
        'name': 'Name',
        'password': 'Password',
        'dont_have_account': 'Don’t have an account?',
        'sign_up_here': 'Sign up here',
        'welcome_back_teacher': 'Welcome Back, Teacher!',
        'teacher_login': 'Teacher Login',
        'email': 'Email',
        'register_student': 'Student Registration',
        'register_teacher': 'Teacher Registration',
        'full_name': 'Full Name',
        'phone': 'Phone',
        'class': 'Class',
        'confirm_password': 'Confirm Password',
        'register': 'Register',
        'already_have_account': 'Already have an account?',
        'login_here': 'Login here',
        'create_account': 'Create Your Account',
        'student_signup_desc': 'Students can use this form to sign up and access learning modules',
        'parent_phone': 'Parent\'s Mobile Number',
        'create_password': 'Create Password',
        'sign_up': 'Sign Up',
        'terms_agreement': 'By clicking Sign Up, you agree to our terms of use.',
        'teacher_signup_desc': 'Teachers can use this form to sign up and access learning modules'
    },
    # Add other languages here (e.g., Punjabi)
}

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
CORS(app)
app.secret_key = '6b67a2220e341756e9a57f91241bad6f'

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'en')
    return dict(translations=translations[lang], lang=lang)

# -------------------- Twilio Config --------------------
TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH = "YOUR_TWILIO_AUTH"
TWILIO_PHONE = "+1234567890"
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# -------------------- Upload Folder --------------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------- Database Initialization --------------------
def init_db():
    with sqlite3.connect('edu.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class INTEGER,
            phone TEXT,
            password TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            title TEXT,
            subject TEXT,
            file_path TEXT,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            title TEXT,
            questions TEXT,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            title TEXT,
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id)
        )''')
    print("✅ Database Initialized Successfully")

def get_db_connection():
    conn = sqlite3.connect('edu.db')
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- Home & Language --------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in translations:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

# -------------------- Chatbot --------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"response": "Please enter a message."})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            chat_session = client.chats.create(model="gemini-2.5-flash")
            response = chat_session.send_message(user_input)
            if response.candidates and len(response.candidates) > 0:
                reply_parts = response.candidates[0].content.parts
                if reply_parts and len(reply_parts) > 0:
                    reply = reply_parts[0].text
                    return jsonify({"response": reply})
            return jsonify({"response": "⚠️ Sorry, no response generated."})
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                time.sleep(2)
            else:
                return jsonify({"response": f"⚠️ Exception: {str(e)}"})
    return jsonify({"response": "⚠️ Service is currently overloaded. Please try again later."})

# -------------------- Student Routes --------------------
@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form['name']
        student_class = request.form['class']
        phone = request.form['phone']
        password = request.form['password']
        with sqlite3.connect("edu.db") as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO students (name, class, phone, password) VALUES (?, ?, ?, ?)",
                        (name, student_class, phone, password))
            conn.commit()
        flash("✅ Student Registered Successfully!", "success")
        return redirect(url_for('student_login'))
    return render_template('register_student.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']

        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE name=? AND password=?",
                               (username, password)).fetchone()
        conn.close()

        if student:
            session['student_id'] = student['id']
            flash(f"🎉 Welcome, {student['name']}!", "success")
            return redirect(url_for('student_dashboard'))
        else:
            flash("❌ Invalid credentials", "danger")

    return render_template('student_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    conn = get_db_connection()

    modules = conn.execute("""
        SELECT modules.id, modules.title, modules.subject, teachers.name AS teacher_name
        FROM modules
        JOIN teachers ON modules.teacher_id = teachers.id
    """).fetchall()

    quizzes = conn.execute("""
        SELECT quizzes.id, quizzes.title, teachers.name AS teacher_name
        FROM quizzes
        JOIN teachers ON quizzes.teacher_id = teachers.id
    """).fetchall()

    announcements = conn.execute("""
        SELECT announcements.title, announcements.content, teachers.name AS teacher_name, announcements.date
        FROM announcements
        JOIN teachers ON announcements.teacher_id = teachers.id
        ORDER BY announcements.date DESC
    """).fetchall()

    conn.close()

    return render_template('student_dashboard.html',
                           modules=modules,
                           quizzes=quizzes,
                           announcements=announcements)

@app.route("/student_dashboard/chat", methods=["POST"])
def student_dashboard_chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"response": "ਕਿਰਪਾ ਕਰਕੇ ਕੁਝ ਲਿਖੋ 🙂"})

    reply = offline_chatbot(user_message)
    return jsonify({"response": reply})

# -------------------- Teacher Routes --------------------
@app.route('/register_teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        with sqlite3.connect("edu.db") as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO teachers (name, email, phone, password) VALUES (?, ?, ?, ?)",
                        (name, email, phone, password))
            conn.commit()
        flash("✅ Teacher Registered Successfully!", "success")
        return redirect(url_for('teacher_login'))
    return render_template('register_teacher.html')

@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect("edu.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM teachers WHERE email=? AND password=?", (email, password))
            teacher = cur.fetchone()
        if teacher:
            session['teacher_id'] = teacher[0]
            flash(f"🎉 Welcome, {teacher[1]}!", "success")
            return redirect(url_for('teacher_dashboard'))
        else:
            flash("❌ Invalid email or password", "danger")
    return render_template('teacher_login.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    teacher_id = session['teacher_id']
    with sqlite3.connect("edu.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, email FROM teachers WHERE id=?", (teacher_id,))
        teacher = cur.fetchone()
        activity_data = [5, 12, 8, 15, 10]  # placeholder
        quizzes = []
        quiz_scores = []
    return render_template('teacher_dashboard.html',
                           teacher_name=teacher[0],
                           teacher_email=teacher[1],
                           activity_data=activity_data,
                           quizzes=quizzes,
                           quiz_scores=quiz_scores)

# -------------------- Teacher Functionalities --------------------
@app.route('/upload_module', methods=['GET', 'POST'])
def upload_module():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    if request.method == 'POST':
        title = request.form['title']
        subject = request.form['subject']
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        with sqlite3.connect('edu.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO modules (teacher_id, title, subject, file_path) VALUES (?, ?, ?, ?)",
                        (session['teacher_id'], title, subject, filepath))
            conn.commit()
        flash("✅ Module uploaded successfully!", "success")
        return redirect(url_for('teacher_dashboard'))
    return render_template('upload_module.html')

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    if request.method == 'POST':
        title = request.form['quiz_title']
        questions = {}
        for key in request.form:
            if key.startswith('question_'):
                q_num = key.split('_')[1]
                questions[request.form[key]] = request.form[f'answer_{q_num}']
        with sqlite3.connect('edu.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO quizzes (teacher_id, title, questions) VALUES (?, ?, ?)",
                        (session['teacher_id'], title, json.dumps(questions)))
            conn.commit()
        flash("✅ Quiz created successfully!", "success")
        return redirect(url_for('teacher_dashboard'))
    return render_template('create_quiz.html')

@app.route('/post_announcement', methods=['GET', 'POST'])
def post_announcement():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        with sqlite3.connect('edu.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO announcements (teacher_id, title, content) VALUES (?, ?, ?)",
                        (session['teacher_id'], title, content))
            conn.commit()
        flash("✅ Announcement posted successfully!", "success")
        return redirect(url_for('teacher_dashboard'))
    return render_template('post_announcement.html')

@app.route('/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    conn = get_db_connection()
    quiz = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    conn.close()

    if not quiz:
        flash("Quiz not found.", "danger")
        return redirect(url_for('student_dashboard'))

    questions_data = json.loads(quiz['questions'])

    if request.method == 'POST':
        # Process answers
        score = 0
        total = len(questions_data)
        for i, (q, a) in enumerate(questions_data.items(), 1):
            user_answer = request.form.get(f'q{i}')
            if user_answer == a:
                score += 1
        flash(f"You scored {score}/{total}", "info")
        return redirect(url_for('student_dashboard'))

    # For GET, prepare questions for template
    # Since stored as {q: a}, convert to list of dicts with options
    questions = []
    for q, a in questions_data.items():
        questions.append({
            'question': q,
            'options': [a, 'Wrong Option 1', 'Wrong Option 2', 'Wrong Option 3']  # Placeholder
        })

    return render_template('take_quiz.html', quiz=quiz, questions=questions)

# -------------------- Extra Learning Modules --------------------
@app.route('/digital_literacy')
def digital_literacy():
    return render_template('digital_literacy.html')

@app.route('/career_guidance')
def career_guidance():
    return render_template('career_guidance.html')

@app.route('/life_skills')
def life_skills():
    return render_template('life_skills.html')

@app.route('/explore_knowledge')
def explore_knowledge():
    return render_template('explore_knowledge.html')

@app.route('/local_stories')
def local_stories():
    return render_template('local_stories.html')

# -------------------- Logout --------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("✅ Logged out successfully!", "info")
    return redirect(url_for('home'))

# -------------------- Run App --------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
