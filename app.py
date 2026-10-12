from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from markupsafe import escape
import sqlite3
import os
import io
from dotenv import load_dotenv

# AI services
from ai_service import career_advisor, ai_skill_gap, generate_project, interview_assistant

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
            user_id INTEGER,
            skill_name TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # SKILLS DATABASE MIGRATION
    # Add user_id to older skills tables so skills belong to
    # the logged-in student instead of being shared globally.
    # Existing skills are kept safely with user_id = NULL.
    # -----------------------------------------------------
    cur.execute("PRAGMA table_info(skills)")
    skill_columns = [column[1] for column in cur.fetchall()]

    if "user_id" not in skill_columns:
        cur.execute("""
            ALTER TABLE skills
            ADD COLUMN user_id INTEGER
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

    cur.execute("""
        SELECT id, skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))

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
        (user_id, skill_name)
        VALUES (?, ?)
    """, (session["user_id"], skill_name))

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
        AND user_id = ?
    """, (skill_id, session["user_id"]))

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

    cur.execute("""
        SELECT id, skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))
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
# AI CAREER ADVISOR
# =========================================================

@app.route("/ai_career_advisor", methods=["GET", "POST"])
def ai_career_advisor():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))

    skill_rows = cur.fetchall()
    conn.close()

    current_skills = [
        row[0].strip()
        for row in skill_rows
        if row[0] and row[0].strip()
    ]

    ai_result = None

    if request.method == "POST":

        target_role = request.form.get(
            "target_role", ""
        ).strip()

        experience_level = request.form.get(
            "experience_level", ""
        ).strip()

        interests = request.form.get(
            "interests", ""
        ).strip()

        if not target_role:

            flash("Please select a target career.")

        else:

            try:

                ai_result = career_advisor(
                    current_skills=(
                        ", ".join(current_skills)
                        if current_skills
                        else "No skills added yet"
                    ),
                    target_role=target_role,
                    experience_level=(
                        experience_level
                        if experience_level
                        else "College student / Beginner"
                    ),
                    interests=(
                        interests
                        if interests
                        else "General technology and career development"
                    )
                )

            except Exception as e:

                ai_result = (
                    "AI service error:\n\n"
                    + str(e)
                )

    return render_template(
        "ai_career_advisor.html",
        current_skills=current_skills,
        ai_result=ai_result
    )


# =========================================================
# AI SKILL GAP ANALYZER
# =========================================================


@app.route("/skill_gap", methods=["GET", "POST"])
def skill_gap():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    career_skills = {
        "Data Scientist": [
            "Python", "SQL", "Pandas", "NumPy",
            "Matplotlib", "Machine Learning", "Statistics"
        ],
        "Data Analyst": [
            "Python", "SQL", "Excel", "Pandas",
            "Power BI", "Statistics", "Data Visualization"
        ],
        "Machine Learning Engineer": [
            "Python", "SQL", "NumPy", "Pandas",
            "Machine Learning", "Deep Learning", "TensorFlow"
        ],
        "Python Developer": [
            "Python", "OOP", "SQL", "Git",
            "Flask", "APIs", "Testing"
        ],
        "Web Developer": [
            "HTML", "CSS", "JavaScript",
            "Git", "Flask", "APIs", "SQL"
        ],
        "AI Engineer": [
            "Python", "SQL", "Machine Learning",
            "Deep Learning", "TensorFlow", "NLP", "APIs"
        ],
        "Business Analyst": [
            "Excel", "SQL", "Power BI",
            "Statistics", "Data Visualization",
            "Business Analysis"
        ]
    }

    result = None
    ai_result = None
    target_role = ""
    additional_skills = ""
    recommended_courses = []

    course_catalog = {
        "Python Programming": [
            "python", "oop", "flask", "apis", "testing"
        ],
        "SQL for Data Analysis": [
            "sql"
        ],
        "Excel for Data Analytics": [
            "excel"
        ],
        "Pandas & NumPy for Data Science": [
            "pandas", "numpy"
        ],
        "Power BI Fundamentals": [
            "power bi"
        ],
        "Statistics for Data Science": [
            "statistics"
        ],
        "Data Visualization": [
            "data visualization", "matplotlib"
        ],
        "Machine Learning": [
            "machine learning"
        ],
        "Deep Learning with TensorFlow": [
            "deep learning", "tensorflow"
        ],
        "Natural Language Processing": [
            "nlp"
        ],
        "Web Development": [
            "html", "css", "javascript"
        ],
        "Git & Version Control": [
            "git"
        ],
        "API Development": [
            "apis"
        ],
        "Business Analysis": [
            "business analysis"
        ]
    }

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))

    skill_rows = cur.fetchall()
    conn.close()

    current_skills = [
        row[0].strip()
        for row in skill_rows
        if row[0] and row[0].strip()
    ]

    if request.method == "POST":

        target_role = request.form.get("target_role", "").strip()
        additional_skills = request.form.get(
            "additional_skills", ""
        ).strip()

        if additional_skills:

            extra_skills = [
                skill.strip()
                for skill in additional_skills.split(",")
                if skill.strip()
            ]

            existing_lower = {
                skill.lower().strip()
                for skill in current_skills
            }

            for skill in extra_skills:

                if skill.lower().strip() not in existing_lower:

                    current_skills.append(skill)

                    existing_lower.add(
                        skill.lower().strip()
                    )

        required_skills = career_skills.get(
            target_role, []
        )

        current_lower = {
            skill.lower().strip()
            for skill in current_skills
        }

        matched_skills = [
            skill
            for skill in required_skills
            if skill.lower() in current_lower
        ]

        missing_skills = [
            skill
            for skill in required_skills
            if skill.lower() not in current_lower
        ]

        match_percentage = (
            round(
                (
                    len(matched_skills)
                    / len(required_skills)
                ) * 100
            )
            if required_skills
            else 0
        )

        # Recommend courses for missing skills.
        for course_name, course_skills in course_catalog.items():

            teaches_missing_skill = any(
                missing_skill.lower() in course_skills
                for missing_skill in missing_skills
            )

            if teaches_missing_skill:
                recommended_courses.append(course_name)

        recommended_courses = recommended_courses[:6]

        result = {
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_percentage": match_percentage,
            "recommended_courses": recommended_courses
        }

        # AI-powered analysis.
        try:

            ai_result = ai_skill_gap(
                current_skills=(
                    ", ".join(current_skills)
                    if current_skills
                    else "No skills added yet"
                ),
                target_role=(
                    target_role
                    if target_role
                    else "Career not specified"
                )
            )

        except Exception as e:

            ai_result = (
                "AI analysis could not be generated.\n\n"
                f"Error: {str(e)}"
            )

    return render_template(
        "ai_skill_gap.html",
        result=result,
        target_role=target_role,
        current_skills=current_skills,
        additional_skills=additional_skills,
        recommended_courses=recommended_courses,
        ai_result=ai_result
    )



# =========================================================
# CAREER ROADMAP
# =========================================================

@app.route("/career_roadmap", methods=["GET", "POST"])
def career_roadmap():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    roadmaps = {
        "Data Analyst": [
            {
                "title": "Foundation",
                "description": "Build a strong foundation in programming and data concepts.",
                "skills": ["Python", "Basic SQL", "Statistics"],
                "project": "Analyze a small student performance dataset using Python."
            },
            {
                "title": "Data Handling",
                "description": "Learn how to clean, transform, and work with real-world datasets.",
                "skills": ["Pandas", "NumPy", "Excel"],
                "project": "Clean and analyze a real-world CSV dataset."
            },
            {
                "title": "Data Visualization",
                "description": "Turn data into clear and useful visual insights.",
                "skills": ["Power BI", "Matplotlib", "Data Visualization"],
                "project": "Create an interactive sales or HR analytics dashboard."
            },
            {
                "title": "Projects",
                "description": "Apply your skills to practical data analytics projects.",
                "skills": ["EDA", "Business Insights", "Dashboard Design"],
                "project": "Build an end-to-end business analytics project."
            },
            {
                "title": "Career Preparation",
                "description": "Prepare your portfolio and skills for internships and entry-level roles.",
                "skills": ["GitHub", "Resume", "Interview Preparation"],
                "project": "Publish 2–3 data analytics projects on GitHub."
            }
        ],

        "Data Scientist": [
            {
                "title": "Programming Foundation",
                "description": "Develop strong programming and data fundamentals.",
                "skills": ["Python", "SQL", "Statistics"],
                "project": "Perform exploratory data analysis on a public dataset."
            },
            {
                "title": "Data Science Tools",
                "description": "Learn the core libraries used for data science.",
                "skills": ["Pandas", "NumPy", "Matplotlib", "Seaborn"],
                "project": "Create a complete EDA notebook."
            },
            {
                "title": "Machine Learning",
                "description": "Learn how machine learning models are built and evaluated.",
                "skills": ["Machine Learning", "Scikit-learn", "Model Evaluation"],
                "project": "Build a prediction model using a public dataset."
            },
            {
                "title": "Advanced Skills",
                "description": "Develop deeper knowledge through practical projects.",
                "skills": ["Feature Engineering", "Model Tuning", "Deployment"],
                "project": "Deploy a machine learning prediction application."
            },
            {
                "title": "Career Preparation",
                "description": "Build a portfolio that demonstrates practical data science skills.",
                "skills": ["GitHub", "Portfolio", "Interview Preparation"],
                "project": "Create and publish multiple end-to-end data science projects."
            }
        ],

        "Machine Learning Engineer": [
            {
                "title": "Programming Foundation",
                "description": "Build strong programming and mathematical foundations.",
                "skills": ["Python", "SQL", "Statistics", "Linear Algebra"],
                "project": "Build a Python data analysis project."
            },
            {
                "title": "Machine Learning",
                "description": "Learn supervised and unsupervised machine learning.",
                "skills": ["Scikit-learn", "Machine Learning", "Model Evaluation"],
                "project": "Build a classification or regression model."
            },
            {
                "title": "Deep Learning",
                "description": "Learn neural networks and modern deep learning workflows.",
                "skills": ["Deep Learning", "TensorFlow", "Neural Networks"],
                "project": "Build an image or text classification model."
            },
            {
                "title": "Deployment",
                "description": "Learn how to turn models into usable applications.",
                "skills": ["APIs", "Flask", "Model Deployment"],
                "project": "Deploy a machine learning model as a web API."
            },
            {
                "title": "Career Preparation",
                "description": "Build production-oriented projects and prepare for interviews.",
                "skills": ["GitHub", "MLOps Basics", "Interview Preparation"],
                "project": "Create an end-to-end deployed ML project."
            }
        ],

        "Python Developer": [
            {
                "title": "Python Foundation",
                "description": "Master Python programming fundamentals.",
                "skills": ["Python", "Data Structures", "Functions"],
                "project": "Build a command-line Python application."
            },
            {
                "title": "Object-Oriented Programming",
                "description": "Learn how to structure larger Python applications.",
                "skills": ["OOP", "Classes", "Modules"],
                "project": "Build a Python-based management system."
            },
            {
                "title": "Web Development",
                "description": "Learn how Python is used to build web applications.",
                "skills": ["Flask", "HTML", "CSS", "APIs"],
                "project": "Build a Flask web application."
            },
            {
                "title": "Database & APIs",
                "description": "Connect applications with databases and external services.",
                "skills": ["SQL", "SQLite", "REST APIs"],
                "project": "Build a CRUD application with a database."
            },
            {
                "title": "Career Preparation",
                "description": "Prepare a portfolio and demonstrate practical Python skills.",
                "skills": ["Git", "GitHub", "Testing", "Resume"],
                "project": "Publish a complete Python project on GitHub."
            }
        ],

        "Web Developer": [
            {
                "title": "Web Foundation",
                "description": "Learn the core technologies behind websites.",
                "skills": ["HTML", "CSS", "JavaScript"],
                "project": "Create a responsive personal portfolio website."
            },
            {
                "title": "Frontend Development",
                "description": "Build interactive and responsive user interfaces.",
                "skills": ["JavaScript", "Responsive Design", "DOM"],
                "project": "Build an interactive frontend application."
            },
            {
                "title": "Backend Development",
                "description": "Learn how web applications handle data and requests.",
                "skills": ["Python", "Flask", "APIs"],
                "project": "Build a full-stack Flask application."
            },
            {
                "title": "Database",
                "description": "Store and manage application data.",
                "skills": ["SQL", "SQLite", "CRUD"],
                "project": "Build a database-backed web application."
            },
            {
                "title": "Career Preparation",
                "description": "Prepare a portfolio and demonstrate full-stack skills.",
                "skills": ["GitHub", "Deployment", "Portfolio"],
                "project": "Deploy a complete full-stack project."
            }
        ],

        "AI Engineer": [
            {
                "title": "Programming Foundation",
                "description": "Build the programming and data foundations needed for AI.",
                "skills": ["Python", "SQL", "Statistics"],
                "project": "Create a Python data analysis project."
            },
            {
                "title": "Machine Learning",
                "description": "Learn the fundamentals of machine learning.",
                "skills": ["Machine Learning", "Scikit-learn", "Model Evaluation"],
                "project": "Build a machine learning prediction system."
            },
            {
                "title": "Deep Learning",
                "description": "Learn neural networks and deep learning frameworks.",
                "skills": ["Deep Learning", "TensorFlow", "Neural Networks"],
                "project": "Build an image or text classification model."
            },
            {
                "title": "AI Applications",
                "description": "Apply AI to real-world applications.",
                "skills": ["NLP", "APIs", "AI Application Development"],
                "project": "Build an AI-powered web application."
            },
            {
                "title": "Career Preparation",
                "description": "Build practical AI projects and prepare for technical interviews.",
                "skills": ["GitHub", "Deployment", "Portfolio"],
                "project": "Deploy an AI application and publish the project."
            }
        ],

        "Business Analyst": [
            {
                "title": "Business Foundation",
                "description": "Understand business problems and analytical thinking.",
                "skills": ["Business Analysis", "Problem Solving", "Statistics"],
                "project": "Analyze a simple business case study."
            },
            {
                "title": "Data Analysis",
                "description": "Learn to work with business data.",
                "skills": ["Excel", "SQL", "Data Cleaning"],
                "project": "Analyze a sales dataset and identify trends."
            },
            {
                "title": "Visualization",
                "description": "Communicate business insights using dashboards.",
                "skills": ["Power BI", "Data Visualization", "Reporting"],
                "project": "Create a business intelligence dashboard."
            },
            {
                "title": "Business Insights",
                "description": "Convert analysis into useful recommendations.",
                "skills": ["KPI Analysis", "Business Insights", "Presentation"],
                "project": "Prepare a complete business performance report."
            },
            {
                "title": "Career Preparation",
                "description": "Build a portfolio and prepare for analyst roles.",
                "skills": ["Resume", "Portfolio", "Interview Preparation"],
                "project": "Publish a complete business analytics case study."
            }
        ]
    }

    # Project workspace templates. These make the "Start Building This Project"
    # section specific to the selected career instead of showing one generic plan.
    workspace_templates = {
        "Data Analyst": {
            "folder": "data_analyst_project/\n├── README.md\n├── requirements.txt\n├── data/\n│   └── dataset.csv\n├── notebooks/\n│   └── analysis.ipynb\n├── reports/\n│   └── insights.md\n├── dashboard/\n│   └── dashboard.pbix\n└── screenshots/",
            "tools": ["Python", "Pandas", "NumPy", "Matplotlib", "Excel", "Power BI"],
            "steps": [
                "Choose a real-world dataset and define 3–5 business questions.",
                "Load and inspect the dataset using Pandas.",
                "Clean missing values, duplicates and inconsistent data.",
                "Perform exploratory data analysis and calculate useful metrics.",
                "Create charts and an interactive Power BI dashboard.",
                "Write the key business insights and recommendations.",
                "Document the project and publish it on GitHub."
            ],
            "output": "A cleaned dataset, EDA notebook, visualizations and a business dashboard with clear insights."
        },
        "Data Scientist": {
            "folder": "data_science_project/\n├── README.md\n├── requirements.txt\n├── data/\n│   └── dataset.csv\n├── notebooks/\n│   └── eda.ipynb\n├── src/\n│   ├── preprocessing.py\n│   └── model.py\n├── models/\n└── screenshots/",
            "tools": ["Python", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Scikit-learn"],
            "steps": [
                "Select a public dataset and define the prediction or analysis problem.",
                "Explore the data and identify missing values, outliers and patterns.",
                "Clean and preprocess the data.",
                "Create useful features and split the data into training and testing sets.",
                "Train and evaluate suitable machine learning models.",
                "Compare results and explain the important findings.",
                "Document the complete workflow and publish the project on GitHub."
            ],
            "output": "A complete data science project containing EDA, preprocessing, a trained model and evaluation results."
        },
        "Machine Learning Engineer": {
            "folder": "ml_engineering_project/\n├── README.md\n├── requirements.txt\n├── data/\n├── src/\n│   ├── train.py\n│   ├── predict.py\n│   └── preprocessing.py\n├── models/\n│   └── model.pkl\n├── app.py\n└── tests/",
            "tools": ["Python", "Pandas", "Scikit-learn", "TensorFlow", "Flask", "REST API"],
            "steps": [
                "Define the ML problem and success metric.",
                "Prepare and validate the training data.",
                "Build a reproducible preprocessing pipeline.",
                "Train and evaluate the model.",
                "Save the trained model for inference.",
                "Create a Flask API that accepts input and returns predictions.",
                "Test the API and document deployment instructions."
            ],
            "output": "A trained ML model exposed through a working prediction API with basic testing and documentation."
        },
        "Python Developer": {
            "folder": "python_project/\n├── README.md\n├── requirements.txt\n├── app.py\n├── database/\n│   └── app.db\n├── templates/\n│   └── index.html\n├── static/\n│   └── style.css\n├── src/\n│   └── services.py\n└── tests/",
            "tools": ["Python", "Flask", "SQLite", "HTML", "CSS", "REST APIs"],
            "steps": [
                "Define the application features and database entities.",
                "Create the Flask application and project structure.",
                "Design the SQLite database and CRUD operations.",
                "Build the HTML/CSS user interface.",
                "Connect forms and API routes to the database.",
                "Add validation and test the main features.",
                "Create a README and publish the project on GitHub."
            ],
            "output": "A working Python web application with database-backed CRUD functionality and a clean user interface."
        },
        "Web Developer": {
            "folder": "web_project/\n├── README.md\n├── requirements.txt\n├── app.py\n├── templates/\n│   └── index.html\n├── static/\n│   ├── style.css\n│   └── script.js\n├── database/\n└── screenshots/",
            "tools": ["HTML", "CSS", "JavaScript", "Python", "Flask", "SQLite"],
            "steps": [
                "Plan the pages and user flow.",
                "Build the HTML structure and responsive CSS.",
                "Add JavaScript interactions and form validation.",
                "Create Flask routes and backend logic.",
                "Connect the application to SQLite.",
                "Test the application on desktop and mobile layouts.",
                "Document and deploy the finished web application."
            ],
            "output": "A responsive full-stack web application with frontend interactions, Flask backend and persistent data."
        },
        "AI Engineer": {
            "folder": "ai_application/\n├── README.md\n├── requirements.txt\n├── app.py\n├── models/\n├── src/\n│   ├── preprocessing.py\n│   └── inference.py\n├── templates/\n│   └── index.html\n├── static/\n│   └── style.css\n└── tests/",
            "tools": ["Python", "Machine Learning", "TensorFlow", "NLP", "Flask", "APIs"],
            "steps": [
                "Choose an AI use case and define the expected output.",
                "Collect and prepare suitable training or reference data.",
                "Build or integrate an AI model.",
                "Create an inference pipeline for user input.",
                "Connect the model to a Flask web interface or API.",
                "Test responses and handle invalid input safely.",
                "Document the architecture and publish the project."
            ],
            "output": "An AI-powered application that accepts user input, processes it with an AI model and returns a useful result."
        },
        "Business Analyst": {
            "folder": "business_analytics/\n├── README.md\n├── data/\n│   └── sales_data.xlsx\n├── analysis/\n│   └── analysis.xlsx\n├── dashboard/\n│   └── dashboard.pbix\n├── report/\n│   └── business_report.pdf\n└── screenshots/",
            "tools": ["Excel", "SQL", "Power BI", "Statistics", "Data Visualization"],
            "steps": [
                "Define the business problem and key performance indicators.",
                "Collect and inspect the business dataset.",
                "Clean and organize the data in Excel or SQL.",
                "Calculate KPIs and identify important trends.",
                "Build a Power BI dashboard for decision makers.",
                "Write findings, risks and actionable recommendations.",
                "Package the dashboard and business report for your portfolio."
            ],
            "output": "A business analytics case study containing KPIs, an interactive dashboard and actionable recommendations."
        }
    }

    target_role = ""
    roadmap = None

    if request.method == "POST":
        target_role = request.form.get("target_role", "").strip()
        roadmap = roadmaps.get(target_role)

        if roadmap:
            workspace = workspace_templates.get(target_role, {})

            for stage in roadmap:
                stage["project_info"] = {
                    "objective": stage.get("project", "Build a practical project for this roadmap stage."),
                    "tools": stage.get("skills", []) or workspace.get("tools", []),
                    "folder": workspace.get("folder", "project/\n├── README.md\n├── requirements.txt\n├── src/\n└── screenshots/"),
                    "steps": workspace.get("steps", []),
                    "output": workspace.get("output", "A working project that demonstrates the skills from this roadmap stage."),
                    "resume_tip": "Add the project name, technologies, GitHub link and 2–3 measurable features to your resume."
                }

    return render_template(
        "career_roadmap.html",
        target_role=target_role,
        roadmap=roadmap
    )


# =========================================================
# AI PROJECT GENERATOR
# =========================================================

@app.route("/ai_project_generator", methods=["GET", "POST"])
def ai_project_generator():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    project_result = None

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))

    skill_rows = cur.fetchall()
    conn.close()

    current_skills = [
        row[0].strip()
        for row in skill_rows
        if row[0] and row[0].strip()
    ]

    if request.method == "POST":

        target_role = request.form.get(
            "target_role",
            ""
        ).strip()

        form_skills = request.form.get(
            "current_skills",
            ""
        ).strip()

        difficulty = request.form.get(
            "difficulty",
            "Medium"
        ).strip()

        if form_skills:
            skills_for_ai = form_skills
        elif current_skills:
            skills_for_ai = ", ".join(current_skills)
        else:
            skills_for_ai = "No skills added yet"

        if not target_role:

            flash("Please select a target career.")

        else:

            try:

                project_result = generate_project(
                    target_role=target_role,
                    current_skills=skills_for_ai,
                    difficulty=difficulty
                )

            except Exception as e:

                project_result = (
                    "Project generation error:\n\n"
                    + str(e)
                )

    return render_template(
        "ai_project_generator.html",
        project_result=project_result
    )



# =========================================================
# AI INTERVIEW ASSISTANT
# =========================================================

@app.route("/ai_interview", methods=["GET", "POST"])
def ai_interview():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    interview_result = None

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],))

    skill_rows = cur.fetchall()
    conn.close()

    current_skills = [
        row[0].strip()
        for row in skill_rows
        if row[0] and row[0].strip()
    ]

    if request.method == "POST":

        target_role = request.form.get(
            "target_role",
            ""
        ).strip()

        form_skills = request.form.get(
            "current_skills",
            ""
        ).strip()

        experience_level = request.form.get(
            "experience_level",
            "Beginner"
        ).strip()

        if form_skills:
            skills_for_ai = form_skills
        elif current_skills:
            skills_for_ai = ", ".join(current_skills)
        else:
            skills_for_ai = "No skills added yet"

        if not target_role:

            flash("Please select a target career.")

        else:

            try:

                interview_result = interview_assistant(
                    target_role=target_role,
                    current_skills=skills_for_ai,
                    experience_level=experience_level
                )

            except Exception as e:

                interview_result = (
                    "Interview preparation error:\n\n"
                    + str(e)
                )

    return render_template(
        "ai_interview.html",
        current_skills=current_skills,
        interview_result=interview_result
    )

# =========================================================
# =========================================================
# AI RESUME BUILDER
# =========================================================

@app.route("/ai_resume_builder", methods=["GET", "POST"])
def ai_resume_builder():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    resume_result = None

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        career = request.form.get("career", "").strip()
        education = request.form.get("education", "").strip()
        skills = request.form.get("skills", "").strip()
        projects = request.form.get("projects", "").strip()
        experience = request.form.get("experience", "").strip()
        certifications = request.form.get("certifications", "").strip()
        achievements = request.form.get("achievements", "").strip()

        if not name or not email or not career or not education or not skills:
            flash("Please fill in all required fields.")
        else:
            def safe(value):
                return str(escape(value)).replace("\n", "<br>")

            contact_parts = [value for value in [email, phone, location] if value]
            contact = " | ".join(safe(value) for value in contact_parts)

            skills_list = [
                item.strip()
                for item in skills.replace("\n", ",").split(",")
                if item.strip()
            ]

            skills_html = "".join(
                f"<li>{safe(skill)}</li>" for skill in skills_list
            )

            sections = []

            sections.append(f"""
                <div class="resume-section">
                    <h3>Career Objective</h3>
                    <p>Motivated candidate seeking opportunities as a <strong>{safe(career)}</strong>, with a strong interest in building practical skills, solving real-world problems and contributing to professional projects.</p>
                </div>
            """)

            sections.append(f"""
                <div class="resume-section">
                    <h3>Education</h3>
                    <p>{safe(education)}</p>
                </div>
            """)

            sections.append(f"""
                <div class="resume-section">
                    <h3>Technical Skills</h3>
                    <ul>{skills_html}</ul>
                </div>
            """)

            if projects:
                sections.append(f"""
                    <div class="resume-section">
                        <h3>Projects</h3>
                        <p>{safe(projects)}</p>
                    </div>
                """)

            if experience:
                sections.append(f"""
                    <div class="resume-section">
                        <h3>Internship / Experience</h3>
                        <p>{safe(experience)}</p>
                    </div>
                """)

            if certifications:
                sections.append(f"""
                    <div class="resume-section">
                        <h3>Certifications</h3>
                        <p>{safe(certifications)}</p>
                    </div>
                """)

            if achievements:
                sections.append(f"""
                    <div class="resume-section">
                        <h3>Achievements</h3>
                        <p>{safe(achievements)}</p>
                    </div>
                """)

            resume_result = f"""
                <h2>{safe(name)}</h2>
                <div class="resume-contact">{contact}</div>
                {''.join(sections)}
            """

    return render_template(
        "ai_resume_builder.html",
        resume_result=resume_result
    )



# =========================================================
# DOWNLOAD RESUME AS PDF
# =========================================================

@app.route("/download_resume", methods=["POST"])
def download_resume():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    except ImportError:
        flash("PDF support is not installed. Run: pip install reportlab")
        return redirect("/ai_resume_builder")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    location = request.form.get("location", "").strip()
    career = request.form.get("career", "").strip()
    education = request.form.get("education", "").strip()
    skills = request.form.get("skills", "").strip()
    projects = request.form.get("projects", "").strip()
    experience = request.form.get("experience", "").strip()
    certifications = request.form.get("certifications", "").strip()
    achievements = request.form.get("achievements", "").strip()

    if not name or not email or not career or not education or not skills:
        flash("Please fill in all required fields before downloading the resume.")
        return redirect("/ai_resume_builder")

    def pdf_text(value):
        value = str(value or "")
        return (
            value.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace("\n", "<br/>")
        )

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{name} - Resume",
        author="SkillSphere"
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=6
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "ResumeHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=5,
        textColor=colors.HexColor("#1d4ed8")
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=5
    )

    story = []

    story.append(Paragraph(pdf_text(name), name_style))

    contact_parts = [x for x in [email, phone, location] if x]
    story.append(Paragraph(pdf_text(" | ".join(contact_parts)), contact_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.grey, spaceAfter=8))

    story.append(Paragraph("CAREER OBJECTIVE", heading_style))
    story.append(Paragraph(
        "Motivated candidate seeking opportunities as a "
        f"<b>{pdf_text(career)}</b>, with a strong interest in building "
        "practical skills, solving real-world problems and contributing "
        "to professional projects.",
        body_style
    ))

    story.append(Paragraph("EDUCATION", heading_style))
    story.append(Paragraph(pdf_text(education), body_style))

    story.append(Paragraph("TECHNICAL SKILLS", heading_style))
    skills_list = [
        item.strip()
        for item in skills.replace("\n", ",").split(",")
        if item.strip()
    ]
    for skill in skills_list:
        story.append(Paragraph(f"• {pdf_text(skill)}", body_style))

    optional_sections = [
        ("PROJECTS", projects),
        ("INTERNSHIP / EXPERIENCE", experience),
        ("CERTIFICATIONS", certifications),
        ("ACHIEVEMENTS", achievements)
    ]

    for title, value in optional_sections:
        if value:
            story.append(Paragraph(title, heading_style))
            story.append(Paragraph(pdf_text(value), body_style))

    document.build(story)
    buffer.seek(0)

    safe_filename = "".join(
        character if character.isalnum() or character in "-_ " else "_"
        for character in name
    ).strip().replace(" ", "_")

    if not safe_filename:
        safe_filename = "SkillSphere_Resume"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{safe_filename}_Resume.pdf"
    )


# =========================================================
# AI RESUME ANALYZER
# =========================================================

@app.route("/resume_analyzer", methods=["GET", "POST"])
def resume_analyzer():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    analysis_result = None

    if request.method == "POST":

        target_role = request.form.get("target_role", "").strip()
        resume_file = request.files.get("resume_file")

        if not target_role:
            flash("Please select a target career.")

        elif not resume_file or not resume_file.filename:
            flash("Please upload your resume.")

        else:
            filename = resume_file.filename.lower()

            if not filename.endswith((".pdf", ".docx", ".txt")):
                flash("Please upload a PDF, DOCX or TXT resume.")
            else:
                resume_text = ""

                try:
                    if filename.endswith(".pdf"):
                        from PyPDF2 import PdfReader
                        reader = PdfReader(resume_file)
                        resume_text = "\n".join(
                            page.extract_text() or ""
                            for page in reader.pages
                        )

                    elif filename.endswith(".docx"):
                        from docx import Document
                        document = Document(resume_file)
                        resume_text = "\n".join(
                            paragraph.text
                            for paragraph in document.paragraphs
                        )

                    else:
                        resume_text = resume_file.read().decode(
                            "utf-8", errors="ignore"
                        )

                except Exception:
                    flash(
                        "Could not read this resume. Please upload a valid "
                        "PDF, DOCX or TXT file."
                    )

                if resume_text.strip():

                    career_requirements = {
                        "Data Scientist": [
                            "python", "sql", "pandas", "numpy",
                            "matplotlib", "machine learning", "statistics"
                        ],
                        "Data Analyst": [
                            "python", "sql", "excel", "pandas",
                            "power bi", "statistics", "data visualization"
                        ],
                        "Machine Learning Engineer": [
                            "python", "sql", "numpy", "pandas",
                            "machine learning", "deep learning", "tensorflow"
                        ],
                        "Python Developer": [
                            "python", "oop", "sql", "git",
                            "flask", "apis", "testing"
                        ],
                        "Web Developer": [
                            "html", "css", "javascript",
                            "git", "flask", "apis", "sql"
                        ],
                        "AI Engineer": [
                            "python", "sql", "machine learning",
                            "deep learning", "tensorflow", "nlp", "apis"
                        ],
                        "Business Analyst": [
                            "excel", "sql", "power bi",
                            "statistics", "data visualization",
                            "business analysis"
                        ]
                    }

                    text_lower = resume_text.lower()
                    required = career_requirements.get(target_role, [])

                    aliases = {
                        "apis": ["api", "apis", "rest api", "restful"],
                        "oop": ["oop", "object oriented", "object-oriented"],
                        "machine learning": [
                            "machine learning", "machine-learning", "ml"
                        ],
                        "deep learning": [
                            "deep learning", "deep-learning", "dl"
                        ],
                        "data visualization": [
                            "data visualization", "data visualisation",
                            "visualization", "visualisation"
                        ],
                        "power bi": ["power bi", "powerbi"],
                        "business analysis": [
                            "business analysis", "business analyst"
                        ]
                    }

                    def skill_found(skill):
                        terms = aliases.get(skill, [skill])
                        return any(term in text_lower for term in terms)

                    matched = [
                        skill for skill in required
                        if skill_found(skill)
                    ]

                    missing = [
                        skill for skill in required
                        if not skill_found(skill)
                    ]

                    score = round(
                        (len(matched) / len(required)) * 100
                    ) if required else 0

                    sections = {
                        "Education": any(
                            word in text_lower
                            for word in [
                                "education", "degree", "b.e", "b.tech",
                                "bachelor", "college", "university"
                            ]
                        ),
                        "Skills": any(
                            word in text_lower
                            for word in [
                                "skills", "technical skills",
                                "python", "sql", "java"
                            ]
                        ),
                        "Projects": "project" in text_lower,
                        "Experience": any(
                            word in text_lower
                            for word in [
                                "experience", "internship",
                                "intern", "work experience"
                            ]
                        ),
                        "Certifications": any(
                            word in text_lower
                            for word in [
                                "certification", "certifications",
                                "certificate"
                            ]
                        )
                    }

                    strengths = []

                    if len(resume_text.split()) >= 150:
                        strengths.append(
                            "Your resume contains a reasonable amount of detail."
                        )

                    if sections["Education"]:
                        strengths.append(
                            "Education information appears to be included."
                        )

                    if sections["Skills"]:
                        strengths.append(
                            "A skills section or technical skills are present."
                        )

                    if sections["Projects"]:
                        strengths.append("Project experience is included.")

                    if sections["Experience"]:
                        strengths.append(
                            "Internship or work experience appears to be included."
                        )

                    if sections["Certifications"]:
                        strengths.append("Certifications are mentioned.")

                    if not strengths:
                        strengths.append(
                            "Your resume has been received and can be improved "
                            "by adding clear sections and relevant skills."
                        )

                    improvements = []

                    if not sections["Education"]:
                        improvements.append(
                            "Add a clear Education section with degree, college "
                            "and graduation details."
                        )

                    if not sections["Skills"]:
                        improvements.append(
                            "Add a dedicated Technical Skills section."
                        )

                    if not sections["Projects"]:
                        improvements.append(
                            "Add 2–3 relevant projects and mention the technologies used."
                        )

                    if not sections["Experience"]:
                        improvements.append(
                            "Add internships, training, freelance work or practical experience if available."
                        )

                    if not sections["Certifications"]:
                        improvements.append(
                            "Add relevant certifications if you have completed any."
                        )

                    word_count = len(resume_text.split())

                    if word_count < 100:
                        improvements.append(
                            "Your resume appears short. Add meaningful project, "
                            "education and experience details rather than unnecessary text."
                        )

                    if word_count > 900:
                        improvements.append(
                            "Consider shortening the resume and keeping the most "
                            "relevant information for the target role."
                        )

                    if not improvements:
                        improvements.append(
                            "Your resume contains the main sections. Focus next "
                            "on measurable achievements and role-specific keywords."
                        )

                    skill_html = "".join(
                        f"<li>{escape(skill.title())}</li>"
                        for skill in matched
                    )

                    missing_html = "".join(
                        f"<li>{escape(skill.title())}</li>"
                        for skill in missing
                    )

                    strengths_html = "".join(
                        f"<li>{escape(item)}</li>"
                        for item in strengths
                    )

                    improvements_html = "".join(
                        f"<li>{escape(item)}</li>"
                        for item in improvements
                    )

                    if score >= 80:
                        score_message = (
                            "Excellent skill alignment for the selected career."
                        )
                    elif score >= 60:
                        score_message = (
                            "Good alignment, but adding a few important skills "
                            "could strengthen your resume."
                        )
                    elif score >= 40:
                        score_message = (
                            "Moderate alignment. Focus on the missing skills "
                            "before applying for this role."
                        )
                    else:
                        score_message = (
                            "Low alignment at the moment. Build the missing "
                            "skills and update your resume."
                        )

                    analysis_result = f"""
                        <div class="score-box">
                            <div class="score">{score}%</div>
                            <div class="score-label">
                                Career Skill Match for {escape(target_role)}
                            </div>
                            <p>{escape(score_message)}</p>
                        </div>

                        <div class="section">
                            <h3>📄 Resume Analyzed</h3>
                            <p>
                                <strong>{escape(resume_file.filename)}</strong>
                                &nbsp; • &nbsp; {word_count} words detected
                            </p>
                        </div>

                        <div class="section">
                            <h3>🎯 Target Career</h3>
                            <p><strong>{escape(target_role)}</strong></p>
                        </div>

                        <div class="section">
                            <h3>✅ Matching Skills</h3>
                            <ul>
                                {skill_html if skill_html else
                                 "<li>No matching target-role skills were detected.</li>"}
                            </ul>
                        </div>

                        <div class="section">
                            <h3>⚠️ Missing Skills</h3>
                            <ul>
                                {missing_html if missing_html else
                                 "<li>No major target-role skills are missing from the detected list.</li>"}
                            </ul>
                        </div>

                        <div class="section">
                            <h3>💪 Resume Strengths</h3>
                            <ul>{strengths_html}</ul>
                        </div>

                        <div class="section">
                            <h3>💡 Improvement Suggestions</h3>
                            <ul>{improvements_html}</ul>
                        </div>

                        <div class="section">
                            <h3>📌 Next Step</h3>
                            <div class="tip">
                                Update your resume using these suggestions and then
                                use SkillSphere's <strong>AI Resume Builder</strong>
                                to create a cleaner version.
                            </div>
                        </div>
                    """

    return render_template(
        "resume_analyzer.html",
        analysis_result=analysis_result
    )


# STUDENT FORGOT PASSWORD
# =========================================================

# =========================================================
# JOB DESCRIPTION MATCHER
# =========================================================

@app.route("/job_matcher", methods=["GET", "POST"])
def job_matcher():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    analysis_result = None

    career_skills = {
        "Data Analyst": ["python", "sql", "excel", "pandas", "numpy", "power bi", "tableau", "statistics", "data visualization"],
        "Data Scientist": ["python", "sql", "pandas", "numpy", "matplotlib", "machine learning", "statistics", "data visualization", "scikit-learn"],
        "Machine Learning Engineer": ["python", "sql", "numpy", "pandas", "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn"],
        "Python Developer": ["python", "oop", "sql", "git", "flask", "django", "apis", "testing"],
        "Web Developer": ["html", "css", "javascript", "git", "flask", "apis", "sql", "react"],
        "AI Engineer": ["python", "sql", "machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "apis"],
        "Business Analyst": ["excel", "sql", "power bi", "tableau", "statistics", "data visualization", "business analysis"]
    }

    if request.method == "POST":
        target_role = request.form.get("target_role", "").strip()
        job_description = request.form.get("job_description", "").strip()

        if not target_role:
            flash("Please select a target career.")
        elif not job_description:
            flash("Please paste the job description.")
        else:
            required = career_skills.get(target_role, [])
            text = job_description.lower()
            matched = [skill for skill in required if skill in text]
            missing = [skill for skill in required if skill not in text]
            score = round((len(matched) / len(required)) * 100) if required else 0

            conn = sqlite3.connect("users.db")
            cur = conn.cursor()
            cur.execute("SELECT skill_name FROM skills WHERE user_id = ?", (session["user_id"],))
            rows = cur.fetchall()
            conn.close()

            student_skills = {row[0].strip().lower() for row in rows if row[0] and row[0].strip()}
            student_matched = [skill for skill in matched if skill.lower() in student_skills]

            if score >= 80:
                readiness = "<div class=\"ready\"><strong>🟢 Strong Job Match</strong><br>You have a strong match for this role. Prepare for the interview and consider applying.</div>"
            elif score >= 60:
                readiness = "<div class=\"ready\"><strong>🟡 Good Job Match</strong><br>You have a good match. Strengthen the missing areas before applying.</div>"
            else:
                readiness = "<div class=\"not-ready\"><strong>🟠 More Preparation Recommended</strong><br>Focus on the missing skills before applying.</div>"

            def items(values, empty):
                return "".join(f"<li>{escape(v.title())}</li>" for v in values) or f"<li>{empty}</li>"

            analysis_result = f"""
                <div class=\"score-box\">
                    <div class=\"score\">{score}%</div>
                    <div class=\"score-label\">Job Match for {escape(target_role)}</div>
                    <p>{len(matched)} of {len(required)} commonly expected skills were detected.</p>
                </div>
                {readiness}
                <div class=\"section\"><h3>🎯 Target Career</h3><p><strong>{escape(target_role)}</strong></p></div>
                <div class=\"section\"><h3>✅ Skills Found in Job Description</h3><ul>{items(matched, "No matching career skills were detected.")}</ul></div>
                <div class=\"section\"><h3>⚠️ Important Skills to Learn</h3><ul>{items(missing, "No major missing skills were detected.")}</ul></div>
                <div class=\"section\"><h3>👤 Your Matching SkillSphere Skills</h3><ul>{items(student_matched, "No matching skills were found in your saved SkillSphere skills.")}</ul></div>
                <div class=\"section\"><h3>📚 Recommended Next Step</h3><div class=\"tip\">Focus on the missing skills, update your resume, and use the <strong>AI Resume Analyzer</strong> before applying.</div></div>
            """

    return render_template("job_matcher.html", analysis_result=analysis_result)


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
# STUDENT PERFORMANCE ANALYTICS
# =========================================================

@app.route("/student_analytics")
def student_analytics():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "student":
        return redirect("/dashboard")

    user_id = session["user_id"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Skills saved by this student
    cur.execute("""
        SELECT COUNT(*)
        FROM skills
        WHERE user_id = ?
    """, (user_id,))
    total_skills = cur.fetchone()[0]

    # Courses started and completed by this student
    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0)
        FROM course_progress
        WHERE user_id = ?
    """, (user_id,))
    course_row = cur.fetchone()
    courses_started = course_row[0] or 0
    courses_completed = course_row[1] or 0

    # Topics completed by this student
    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0)
        FROM topic_progress
        WHERE user_id = ?
    """, (user_id,))
    topic_row = cur.fetchone()
    topics_tracked = topic_row[0] or 0
    topics_completed = topic_row[1] or 0

    # Build a simple, transparent progress score from existing records.
    # Skills contribute up to 40 points; course completion up to 40;
    # topic completion up to 20. This is a learning activity indicator,
    # not a validated measure of employability.
    skill_points = min(total_skills, 8) / 8 * 40
    course_points = (courses_completed / courses_started * 40) if courses_started else 0
    topic_points = (topics_completed / topics_tracked * 20) if topics_tracked else 0
    readiness_score = round(skill_points + course_points + topic_points)
    readiness_score = min(100, max(0, readiness_score))

    # Course completion percentage
    course_completion = round(
        courses_completed / courses_started * 100
    ) if courses_started else 0

    # Topic completion percentage
    topic_completion = round(
        topics_completed / topics_tracked * 100
    ) if topics_tracked else 0

    # Latest saved skills
    cur.execute("""
        SELECT skill_name
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))
    skills_list = [row[0] for row in cur.fetchall() if row[0]]

    conn.close()

    suggestions = []

    if total_skills < 5:
        suggestions.append("Add more of your completed technical skills in My Skills.")
    if courses_started == 0:
        suggestions.append("Start a course to begin tracking your learning progress.")
    elif courses_completed < courses_started:
        suggestions.append("Continue your started courses and mark each course complete when finished.")
    if topics_tracked == 0:
        suggestions.append("Open a course and mark the topics you finish to track topic-level progress.")
    elif topics_completed < topics_tracked:
        suggestions.append("Complete the remaining tracked topics in your courses.")
    if not suggestions:
        suggestions.append("Keep learning, add new skills, and build portfolio projects to strengthen your profile.")

    return render_template(
        "student_analytics.html",
        total_skills=total_skills,
        courses_started=courses_started,
        courses_completed=courses_completed,
        topics_tracked=topics_tracked,
        topics_completed=topics_completed,
        course_completion=course_completion,
        topic_completion=topic_completion,
        readiness_score=readiness_score,
        skills_list=skills_list,
        suggestions=suggestions
    )


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

    # Delete student's skills
    cur.execute("""
        DELETE FROM skills
        WHERE user_id = ?
    """, (user_id,))

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
    app.run(host="0.0.0.0", port=5000, debug=True)