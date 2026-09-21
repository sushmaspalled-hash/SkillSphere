from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Please create a .env file with SECRET_KEY=your-secret-key")


# =========================================================
# DATABASE SETUP
# =========================================================

def init_db():

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # MENTORS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mentors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            skills TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # MENTOR ACCOUNTS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mentor_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mentor_id INTEGER UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # COURSE PROGRESS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            UNIQUE(user_id, course_name)
        )
    """)

    # -----------------------------------------------------
    # TOPIC PROGRESS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            UNIQUE(user_id, course_name, topic_name)
        )
    """)

    # -----------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_user_id INTEGER,
            mentor_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            sender_type TEXT DEFAULT 'student',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # DATABASE MIGRATION
    # Add sender_type if old messages table exists
    # -----------------------------------------------------

    cur.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cur.fetchall()]

    if "sender_type" not in columns:
        cur.execute("""
            ALTER TABLE messages
            ADD COLUMN sender_type TEXT DEFAULT 'student'
        """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# STUDENT SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                password
            ))

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered. Please use another email."

    return render_template("signup.html")


# =========================================================
# STUDENT LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
        """, (
            email,
            password
        ))

        user = cur.fetchone()

        conn.close()

        if user:

            session.clear()

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = "student"

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/mentor_dashboard")

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name")
    )


# =========================================================
# SKILLS
# =========================================================

@app.route("/skills")
def skills():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM skills")

    skills_list = cur.fetchall()

    conn.close()

    return render_template(
        "skills.html",
        skills=skills_list
    )


@app.route("/add_skill", methods=["POST"])
def add_skill():

    if "user_id" not in session:
        return redirect("/login")

    skill_name = request.form["skill_name"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO skills
        (skill_name)
        VALUES (?)
    """, (skill_name,))

    conn.commit()
    conn.close()

    return redirect("/skills")


@app.route("/delete_skill/<int:skill_id>", methods=["POST"])
def delete_skill(skill_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM skills
        WHERE id = ?
    """, (skill_id,))

    conn.commit()
    conn.close()

    return redirect("/skills")


# =========================================================
# MENTORS
# =========================================================

@app.route("/mentors")
def mentors():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM mentors
    """)

    mentors_list = cur.fetchall()

    conn.close()

    return render_template(
        "mentors.html",
        mentors=mentors_list
    )


@app.route("/add_mentor", methods=["POST"])
def add_mentor():

    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    specialization = request.form["specialization"]
    skills = request.form["skills"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO mentors
        (name, specialization, skills)
        VALUES (?, ?, ?)
    """, (
        name,
        specialization,
        skills
    ))

    conn.commit()
    conn.close()

    return redirect("/mentors")


@app.route("/delete_mentor/<int:mentor_id>", methods=["POST"])
def delete_mentor(mentor_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM mentor_accounts
        WHERE mentor_id = ?
    """, (mentor_id,))

    cur.execute("""
        DELETE FROM messages
        WHERE mentor_id = ?
    """, (mentor_id,))

    cur.execute("""
        DELETE FROM mentors
        WHERE id = ?
    """, (mentor_id,))

    conn.commit()
    conn.close()

    return redirect("/mentors")


# =========================================================
# STUDENT → MENTOR MESSAGE
# =========================================================

@app.route("/message_mentor/<int:mentor_id>", methods=["GET", "POST"])
def message_mentor(mentor_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/mentor_dashboard")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM mentors
        WHERE id = ?
    """, (mentor_id,))

    mentor = cur.fetchone()

    if not mentor:

        conn.close()

        return "Mentor not found."

    if request.method == "POST":

        message_text = request.form["message"]

        cur.execute("""
            INSERT INTO messages
            (
                sender_user_id,
                mentor_id,
                message_text,
                sender_type
            )
            VALUES (?, ?, ?, 'student')
        """, (
            session["user_id"],
            mentor_id,
            message_text
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "message_mentor",
                mentor_id=mentor_id
            )
        )

    cur.execute("""
        SELECT
            messages.message_text,
            messages.sent_at,
            messages.sender_type,
            users.name
        FROM messages
        LEFT JOIN users
        ON messages.sender_user_id = users.id
        WHERE messages.mentor_id = ?
        ORDER BY messages.id ASC
    """, (mentor_id,))

    message_list = cur.fetchall()

    conn.close()

    return render_template(
        "message_mentor.html",
        mentor=mentor,
        messages=message_list
    )


# =========================================================
# MENTOR SIGNUP
# =========================================================

@app.route("/mentor_signup", methods=["GET", "POST"])
def mentor_signup():

    if request.method == "POST":

        name = request.form["name"]
        specialization = request.form["specialization"]
        skills = request.form["skills"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO mentors
                (name, specialization, skills)
                VALUES (?, ?, ?)
            """, (
                name,
                specialization,
                skills
            ))

            mentor_id = cur.lastrowid

            cur.execute("""
                INSERT INTO mentor_accounts
                (mentor_id, email, password)
                VALUES (?, ?, ?)
            """, (
                mentor_id,
                email,
                password
            ))

            conn.commit()
            conn.close()

            return redirect("/mentor_login")

        except sqlite3.IntegrityError:

            conn.rollback()
            conn.close()

            return "Email already registered."

    return render_template("mentor_signup.html")


# =========================================================
# MENTOR LOGIN
# =========================================================

@app.route("/mentor_login", methods=["GET", "POST"])
def mentor_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("""
            SELECT
                mentor_accounts.mentor_id,
                mentors.name
            FROM mentor_accounts
            JOIN mentors
            ON mentor_accounts.mentor_id = mentors.id
            WHERE mentor_accounts.email = ?
            AND mentor_accounts.password = ?
        """, (
            email,
            password
        ))

        mentor = cur.fetchone()

        conn.close()

        if mentor:

            session.clear()

            session["mentor_id"] = mentor[0]
            session["mentor_name"] = mentor[1]
            session["role"] = "mentor"

            return redirect("/mentor_dashboard")

        return "Invalid mentor email or password."

    return render_template("mentor_login.html")


# =========================================================
# MENTOR DASHBOARD
# =========================================================

@app.route("/mentor_dashboard")
def mentor_dashboard():

    if "mentor_id" not in session:
        return redirect("/mentor_login")

    if session.get("role") != "mentor":
        return redirect("/dashboard")

    return render_template(
        "mentor_dashboard.html",
        mentor_name=session.get("mentor_name")
    )


# =========================================================
# MENTOR MESSAGES
# =========================================================

@app.route("/mentor_messages")
def mentor_messages():

    if "mentor_id" not in session:
        return redirect("/mentor_login")

    mentor_id = session["mentor_id"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            messages.id,
            messages.message_text,
            messages.sent_at,
            users.name,
            users.id
        FROM messages
        JOIN users
        ON messages.sender_user_id = users.id
        WHERE messages.mentor_id = ?
        ORDER BY messages.id ASC
    """, (mentor_id,))

    message_list = cur.fetchall()

    conn.close()

    return render_template(
        "mentor_messages.html",
        messages=message_list,
        mentor_name=session.get("mentor_name")
    )


# =========================================================
# MENTOR REPLY
# =========================================================

@app.route("/mentor_reply/<int:student_id>", methods=["POST"])
def mentor_reply(student_id):

    if "mentor_id" not in session:
        return redirect("/mentor_login")

    mentor_id = session["mentor_id"]

    message_text = request.form["message"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages
        (
            sender_user_id,
            mentor_id,
            message_text,
            sender_type
        )
        VALUES (?, ?, ?, 'mentor')
    """, (
        student_id,
        mentor_id,
        message_text
    ))

    conn.commit()
    conn.close()

    return redirect("/mentor_messages")


# =========================================================
# MENTOR LOGOUT
# =========================================================

@app.route("/mentor_logout")
def mentor_logout():

    session.clear()

    return redirect("/mentor_login")


# =========================================================
# COURSES
# =========================================================

@app.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("courses.html")


# =========================================================
# COURSE DETAILS
# =========================================================

@app.route("/course/<course_name>")
def course(course_name):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT completed
        FROM course_progress
        WHERE user_id = ?
        AND course_name = ?
    """, (
        user_id,
        course_name
    ))

    progress = cur.fetchone()

    cur.execute("""
        SELECT
            topic_name,
            completed
        FROM topic_progress
        WHERE user_id = ?
        AND course_name = ?
    """, (
        user_id,
        course_name
    ))

    topic_data = cur.fetchall()

    conn.close()

    completed = progress[0] if progress else 0

    completed_topics = {}

    for topic in topic_data:
        completed_topics[topic[0]] = topic[1]

    return render_template(
        "course_detail.html",
        course_name=course_name,
        completed=completed,
        completed_topics=completed_topics
    )


# =========================================================
# SAVE TOPIC PROGRESS
# =========================================================

@app.route("/save_topic", methods=["POST"])
def save_topic():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    course_name = request.form["course_name"]
    topic_name = request.form["topic_name"]
    completed = int(request.form["completed"])

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO topic_progress
        (
            user_id,
            course_name,
            topic_name,
            completed
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(
            user_id,
            course_name,
            topic_name
        )

        DO UPDATE SET
            completed = excluded.completed
    """, (
        user_id,
        course_name,
        topic_name,
        completed
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "course",
            course_name=course_name
        )
    )


# =========================================================
# COMPLETE COURSE
# =========================================================

@app.route(
    "/complete_course/<course_name>",
    methods=["POST"]
)
def complete_course(course_name):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO course_progress
        (
            user_id,
            course_name,
            completed
        )
        VALUES (?, ?, 1)

        ON CONFLICT(
            user_id,
            course_name
        )

        DO UPDATE SET
            completed = 1
    """, (user_id, course_name))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "course",
            course_name=course_name
        )
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.route("/recommendations")
def recommendations():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM skills")
    user_skills = cur.fetchall()

    cur.execute("SELECT * FROM mentors")
    all_mentors = cur.fetchall()

    conn.close()

    recommended_mentors = []

    for mentor in all_mentors:

        mentor_skills = mentor[3].lower()

        for skill in user_skills:

            student_skill = skill[1].lower().strip()

            if student_skill in mentor_skills:

                if mentor not in recommended_mentors:
                    recommended_mentors.append(mentor)

                break

    recommended_courses = []

    for skill in user_skills:

        student_skill = skill[1].lower().strip()

        if "python" in student_skill:

            if "Python Programming" not in recommended_courses:

                recommended_courses.append(
                    "Python Programming"
                )

        if (
            "html" in student_skill
            or "css" in student_skill
            or "javascript" in student_skill
        ):

            if "Web Development" not in recommended_courses:

                recommended_courses.append(
                    "Web Development"
                )

        if (
            "machine learning" in student_skill
            or "machinelearning" in student_skill
            or student_skill == "ml"
            or "data science" in student_skill
        ):

            if "Machine Learning" not in recommended_courses:

                recommended_courses.append(
                    "Machine Learning"
                )

    return render_template(
        "recommendations.html",
        user_skills=user_skills,
        recommended_mentors=recommended_mentors,
        recommended_courses=recommended_courses
    )


# =========================================================
# STUDENT FORGOT PASSWORD
# =========================================================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip()

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM users
            WHERE email = ?
        """, (email,))

        user = cur.fetchone()
        conn.close()

        if user:
            session["reset_user_id"] = user[0]
            session["reset_role"] = "student"
            return redirect("/reset_password")

        flash("No student account was found with that email address.")

    return render_template("forgot_password.html")


# =========================================================
# RESET STUDENT PASSWORD
# =========================================================

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    if session.get("reset_role") != "student" or "reset_user_id" not in session:
        return redirect("/forgot_password")

    if request.method == "POST":

        new_password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return render_template("reset_password.html")

        if len(new_password) < 6:
            flash("Password must contain at least 6 characters.")
            return render_template("reset_password.html")

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (new_password, session["reset_user_id"]))

        conn.commit()
        conn.close()

        session.pop("reset_user_id", None)
        session.pop("reset_role", None)

        flash("Your password has been changed successfully. Please log in.")
        return redirect("/login")

    return render_template("reset_password.html")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Demo admin credentials
        if (
            email == "admin@skillsphere.com"
            and password == "admin123"
        ):

            session.clear()

            session["admin"] = True
            session["role"] = "admin"

            return redirect("/admin_dashboard")

        return "Invalid admin email or password."

    return render_template("admin_login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin_dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect("/admin_login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Total students
    cur.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total_students = cur.fetchone()[0]

    # Total mentors
    cur.execute("""
        SELECT COUNT(*)
        FROM mentors
    """)

    total_mentors = cur.fetchone()[0]

    # Total messages
    cur.execute("""
        SELECT COUNT(*)
        FROM messages
    """)

    total_messages = cur.fetchone()[0]

    # Total courses started
    cur.execute("""
        SELECT COUNT(*)
        FROM course_progress
    """)

    total_course_progress = cur.fetchone()[0]

    # Students
    cur.execute("""
        SELECT id, name, email
        FROM users
        ORDER BY id DESC
    """)

    students = cur.fetchall()

    # Mentors
    cur.execute("""
        SELECT id, name, specialization, skills
        FROM mentors
        ORDER BY id DESC
    """)

    mentors_list = cur.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_mentors=total_mentors,
        total_messages=total_messages,
        total_course_progress=total_course_progress,
        students=students,
        mentors=mentors_list
    )


# =========================================================
# ADMIN DELETE STUDENT
# =========================================================

@app.route(
    "/admin_delete_student/<int:user_id>",
    methods=["POST"]
)
def admin_delete_student(user_id):

    if not session.get("admin"):
        return redirect("/admin_login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Delete student's topic progress
    cur.execute("""
        DELETE FROM topic_progress
        WHERE user_id = ?
    """, (user_id,))

    # Delete student's course progress
    cur.execute("""
        DELETE FROM course_progress
        WHERE user_id = ?
    """, (user_id,))

    # Delete student's messages
    cur.execute("""
        DELETE FROM messages
        WHERE sender_user_id = ?
    """, (user_id,))

    # Delete student
    cur.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")


# =========================================================
# ADMIN DELETE MENTOR
# =========================================================

@app.route(
    "/admin_delete_mentor/<int:mentor_id>",
    methods=["POST"]
)
def admin_delete_mentor(mentor_id):

    if not session.get("admin"):
        return redirect("/admin_login")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Delete mentor account
    cur.execute("""
        DELETE FROM mentor_accounts
        WHERE mentor_id = ?
    """, (mentor_id,))

    # Delete mentor messages
    cur.execute("""
        DELETE FROM messages
        WHERE mentor_id = ?
    """, (mentor_id,))

    # Delete mentor
    cur.execute("""
        DELETE FROM mentors
        WHERE id = ?
    """, (mentor_id,))

    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin_logout")
def admin_logout():

    session.clear()

    return redirect("/admin_login")


# =========================================================
# STUDENT LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)