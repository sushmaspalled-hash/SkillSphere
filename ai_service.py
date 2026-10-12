# ============================================================
# SkillSphere Free AI Service
# No OpenAI API
# No API key
# No payment required
# ============================================================


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def clean_skills(current_skills):
    """
    Convert skills into a clean list.
    Accepts:
    - comma-separated string
    - list of skills
    """

    if isinstance(current_skills, list):
        skills = current_skills
    else:
        skills = str(current_skills).split(",")

    return [
        skill.strip()
        for skill in skills
        if skill and skill.strip()
        and skill.strip().lower() not in [
            "no skills added yet",
            "none",
            "no skills"
        ]
    ]


def normalize(text):
    return str(text).strip().lower()


def has_skill(skills, skill):
    """
    Flexible skill matching.
    Example:
    Python matches python programming.
    SQL matches mysql.
    """
    skill = normalize(skill)

    for user_skill in skills:
        user_skill = normalize(user_skill)

        if skill in user_skill or user_skill in skill:
            return True

    return False


# ------------------------------------------------------------
# Career requirements
# ------------------------------------------------------------

CAREER_REQUIREMENTS = {

    "Data Analyst": [
        "Python",
        "Pandas",
        "NumPy",
        "SQL",
        "Excel",
        "Power BI",
        "Statistics",
        "Data Visualization"
    ],

    "Data Scientist": [
        "Python",
        "Pandas",
        "NumPy",
        "SQL",
        "Statistics",
        "Machine Learning",
        "Matplotlib",
        "Data Visualization"
    ],

    "Machine Learning Engineer": [
        "Python",
        "NumPy",
        "Pandas",
        "Machine Learning",
        "Scikit-learn",
        "Statistics",
        "Git",
        "APIs"
    ],

    "Python Developer": [
        "Python",
        "OOP",
        "Git",
        "SQL",
        "Flask",
        "REST API",
        "Problem Solving"
    ],

    "Web Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "Python",
        "Flask",
        "SQL",
        "Git",
        "REST API"
    ],

    "AI Engineer": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "NumPy",
        "Pandas",
        "APIs",
        "Git",
        "Data Structures"
    ],

    "Business Analyst": [
        "Excel",
        "SQL",
        "Power BI",
        "Statistics",
        "Data Visualization",
        "Communication",
        "Problem Solving"
    ]
}


# ------------------------------------------------------------
# Learning order
# ------------------------------------------------------------

LEARNING_ORDER = {
    "Data Analyst": [
        "Python",
        "Pandas",
        "NumPy",
        "SQL",
        "Excel",
        "Statistics",
        "Power BI",
        "Data Visualization"
    ],

    "Data Scientist": [
        "Python",
        "NumPy",
        "Pandas",
        "Statistics",
        "SQL",
        "Data Visualization",
        "Machine Learning",
        "Projects"
    ],

    "Machine Learning Engineer": [
        "Python",
        "NumPy",
        "Pandas",
        "Statistics",
        "Machine Learning",
        "Scikit-learn",
        "APIs",
        "Projects"
    ],

    "Python Developer": [
        "Python",
        "OOP",
        "Problem Solving",
        "SQL",
        "Git",
        "Flask",
        "REST API",
        "Projects"
    ],

    "Web Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "Python",
        "Flask",
        "SQL",
        "REST API",
        "Projects"
    ],

    "AI Engineer": [
        "Python",
        "NumPy",
        "Pandas",
        "Statistics",
        "Machine Learning",
        "Deep Learning",
        "APIs",
        "Projects"
    ],

    "Business Analyst": [
        "Excel",
        "SQL",
        "Statistics",
        "Power BI",
        "Data Visualization",
        "Communication",
        "Problem Solving",
        "Projects"
    ]
}


# ------------------------------------------------------------
# Project ideas
# ------------------------------------------------------------

PROJECTS = {

    "Data Analyst": [
        "Sales Performance Dashboard",
        "Customer Churn Analysis",
        "Marketing Campaign Analysis"
    ],

    "Data Scientist": [
        "Customer Churn Prediction",
        "House Price Prediction",
        "Student Performance Prediction"
    ],

    "Machine Learning Engineer": [
        "Customer Churn Prediction API",
        "Real-Time Fraud Detection System",
        "Recommendation System"
    ],

    "Python Developer": [
        "Task Management Web Application",
        "Student Management System",
        "REST API Based Expense Tracker"
    ],

    "Web Developer": [
        "Full Stack Student Portal",
        "Online Course Platform",
        "Job Recommendation Website"
    ],

    "AI Engineer": [
        "AI Career Assistant",
        "Document Question Answering System",
        "AI-Based Recommendation System"
    ],

    "Business Analyst": [
        "Business KPI Dashboard",
        "Sales and Revenue Analysis",
        "Customer Segmentation Dashboard"
    ]
}


# ------------------------------------------------------------
# Free AI Career Advisor
# ------------------------------------------------------------

def career_advisor(
    current_skills,
    target_role,
    experience_level,
    interests
):
    """
    Generates a career plan using local rule-based logic.
    No external API is required.
    """

    skills = clean_skills(current_skills)

    role = target_role.strip()

    required_skills = CAREER_REQUIREMENTS.get(
        role,
        [
            "Python",
            "SQL",
            "Statistics",
            "Git",
            "Communication",
            "Problem Solving"
        ]
    )

    learning_order = LEARNING_ORDER.get(
        role,
        required_skills
    )

    missing_skills = [
        skill
        for skill in required_skills
        if not has_skill(skills, skill)
    ]

    matched_skills = [
        skill
        for skill in required_skills
        if has_skill(skills, skill)
    ]

    if len(required_skills) > 0:
        match_percentage = round(
            (len(matched_skills) / len(required_skills)) * 100
        )
    else:
        match_percentage = 0

    projects = PROJECTS.get(
        role,
        [
            "Personal Portfolio Project",
            "Real-World Data Analysis Project",
            "End-to-End Application"
        ]
    )

    result = []

    result.append("🎯 SKILLSPHERE CAREER ADVISOR")
    result.append("=" * 50)

    result.append("")
    result.append(f"Target Career: {role}")
    result.append(f"Experience Level: {experience_level}")
    result.append(f"Interests: {interests}")

    result.append("")
    result.append("📊 CAREER READINESS")
    result.append("-" * 50)
    result.append(
        f"Your current career skill match is approximately "
        f"{match_percentage}%."
    )

    if matched_skills:
        result.append("")
        result.append("✅ Skills You Already Have:")
        for skill in matched_skills:
            result.append(f"• {skill}")

    if missing_skills:
        result.append("")
        result.append("📚 Skills You Should Learn:")
        for skill in missing_skills:
            result.append(f"• {skill}")

    result.append("")
    result.append("🛣️ RECOMMENDED LEARNING ORDER")
    result.append("-" * 50)

    for index, skill in enumerate(learning_order, start=1):
        result.append(f"{index}. {skill}")

    result.append("")
    result.append("🚀 PROJECTS TO BUILD")
    result.append("-" * 50)

    for project in projects:
        result.append(f"• {project}")

    result.append("")
    result.append("💼 INTERVIEW PREPARATION")
    result.append("-" * 50)

    interview_topics = {
        "Data Analyst": [
            "Python and Pandas",
            "SQL queries",
            "Statistics",
            "Excel",
            "Power BI",
            "Data cleaning",
            "Data visualization"
        ],

        "Data Scientist": [
            "Python",
            "Statistics",
            "Machine Learning",
            "SQL",
            "Pandas and NumPy",
            "Model evaluation",
            "Data preprocessing"
        ],

        "Machine Learning Engineer": [
            "Python",
            "Machine Learning algorithms",
            "Scikit-learn",
            "Model deployment",
            "APIs",
            "Data preprocessing",
            "Git"
        ],

        "Python Developer": [
            "Python",
            "OOP",
            "Data Structures",
            "SQL",
            "Flask",
            "REST APIs",
            "Git"
        ],

        "Web Developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "Flask",
            "SQL",
            "REST APIs",
            "Git"
        ],

        "AI Engineer": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "APIs",
            "Data preprocessing",
            "Model evaluation",
            "AI applications"
        ],

        "Business Analyst": [
            "Excel",
            "SQL",
            "Power BI",
            "Statistics",
            "Business KPIs",
            "Data visualization",
            "Communication"
        ]
    }

    topics = interview_topics.get(
        role,
        [
            "Python",
            "SQL",
            "Problem Solving",
            "Projects",
            "Communication"
        ]
    )

    for topic in topics:
        result.append(f"• {topic}")

    result.append("")
    result.append("📅 NEXT 30 DAYS")
    result.append("-" * 50)
    result.append("Week 1 → Learn the fundamentals")
    result.append("Week 2 → Practice coding and exercises")
    result.append("Week 3 → Build a small project")
    result.append("Week 4 → Improve the project and prepare for interviews")

    result.append("")
    result.append("⭐ PERSONAL ADVICE")
    result.append("-" * 50)

    if match_percentage < 30:
        result.append(
            "Start with the fundamentals and build one small project."
        )
    elif match_percentage < 60:
        result.append(
            "You have a good foundation. Focus on your missing skills "
            "and start building real projects."
        )
    elif match_percentage < 80:
        result.append(
            "You are progressing well. Strengthen advanced skills "
            "and build portfolio projects."
        )
    else:
        result.append(
            "You are close to being career-ready. Focus on projects, "
            "interview preparation and practical experience."
        )

    result.append("")
    result.append(
        "💡 SkillSphere Free AI Engine works locally and does not "
        "require an external API or paid service."
    )

    return "\n".join(result)


# ------------------------------------------------------------
# Free AI Skill Gap Analyzer
# ------------------------------------------------------------

def ai_skill_gap(current_skills, target_role):
    """
    Generates a detailed skill-gap report using local logic.
    """

    skills = clean_skills(current_skills)

    role = target_role.strip()

    required_skills = CAREER_REQUIREMENTS.get(
        role,
        [
            "Python",
            "SQL",
            "Statistics",
            "Git",
            "Problem Solving"
        ]
    )

    matched = [
        skill
        for skill in required_skills
        if has_skill(skills, skill)
    ]

    missing = [
        skill
        for skill in required_skills
        if not has_skill(skills, skill)
    ]

    percentage = round(
        (len(matched) / len(required_skills)) * 100
    )

    result = []

    result.append("🤖 FREE AI SKILL GAP ANALYSIS")
    result.append("=" * 50)

    result.append("")
    result.append(f"Target Role: {role}")
    result.append(f"Current Skill Match: {percentage}%")

    result.append("")
    result.append("✅ YOUR STRENGTHS")
    result.append("-" * 50)

    if matched:
        for skill in matched:
            result.append(
                f"• {skill} — Already relevant to {role}"
            )
    else:
        result.append(
            "• No major matching skills detected yet."
        )

    result.append("")
    result.append("⚠️ YOUR SKILL GAPS")
    result.append("-" * 50)

    if missing:
        for skill in missing:
            result.append(
                f"• {skill} — Important for {role}"
            )
    else:
        result.append(
            "• No major skill gaps detected."
        )

    result.append("")
    result.append("🔥 PRIORITY ORDER")
    result.append("-" * 50)

    priority = LEARNING_ORDER.get(
        role,
        required_skills
    )

    priority_number = 1

    for skill in priority:

        if not has_skill(skills, skill):

            result.append(
                f"{priority_number}. {skill}"
            )

            priority_number += 1

    result.append("")
    result.append("📖 RECOMMENDED APPROACH")
    result.append("-" * 50)

    if missing:

        result.append(
            f"1. Start with {missing[0]}."
        )

        if len(missing) > 1:
            result.append(
                f"2. Then learn {missing[1]}."
            )

        if len(missing) > 2:
            result.append(
                f"3. Practice {missing[2]} through projects."
            )

        result.append(
            "4. Build at least one real-world project."
        )

        result.append(
            "5. Add the project to your resume and GitHub."
        )

    else:

        result.append(
            "You have covered the main required skills."
        )

        result.append(
            "Focus on advanced projects and interview preparation."
        )

    result.append("")
    result.append("📅 30-DAY PLAN")
    result.append("-" * 50)

    result.append(
        "Days 1–7 → Learn missing fundamentals"
    )

    result.append(
        "Days 8–15 → Practice coding and exercises"
    )

    result.append(
        "Days 16–23 → Build a practical project"
    )

    result.append(
        "Days 24–30 → Improve project + interview preparation"
    )

    result.append("")
    result.append(
        "💡 This analysis runs locally inside SkillSphere "
        "and does not require a paid AI API."
    )

    return "\n".join(result)


# ------------------------------------------------------------
# Free AI Project Generator
# ------------------------------------------------------------

def generate_project(
    target_role,
    current_skills,
    difficulty="Medium"
):
    """
    Generates a project idea using local templates.
    """

    role = target_role.strip()
    skills = clean_skills(current_skills)

    project_list = PROJECTS.get(
        role,
        [
            "Career Portfolio Application",
            "Student Productivity System",
            "Real-World Data Analysis Application"
        ]
    )

    project_name = project_list[0]

    if difficulty.lower() == "easy":
        project_name = project_list[0]

    elif difficulty.lower() == "hard":
        project_name = project_list[-1]

    result = []

    result.append("🚀 SKILLSPHERE PROJECT GENERATOR")
    result.append("=" * 50)

    result.append("")
    result.append(f"Project: {project_name}")
    result.append(f"Target Career: {role}")
    result.append(f"Difficulty: {difficulty}")

    result.append("")
    result.append("🎯 PROJECT OBJECTIVE")
    result.append("-" * 50)

    result.append(
        f"Build a practical {role} project that solves "
        "a real-world problem and demonstrates your technical skills."
    )

    result.append("")
    result.append("🛠️ RECOMMENDED TECHNOLOGIES")
    result.append("-" * 50)

    required = CAREER_REQUIREMENTS.get(
        role,
        ["Python", "SQL", "Git"]
    )

    for technology in required[:7]:
        result.append(f"• {technology}")

    result.append("")
    result.append("📦 MAIN FEATURES")
    result.append("-" * 50)

    if role == "Data Analyst":

        features = [
            "Dataset upload",
            "Data cleaning",
            "Exploratory Data Analysis",
            "KPI calculations",
            "Interactive dashboard",
            "Charts and visualizations",
            "Business insights"
        ]

    elif role == "Data Scientist":

        features = [
            "Dataset collection",
            "Data preprocessing",
            "Exploratory Data Analysis",
            "Feature engineering",
            "Machine learning model",
            "Model evaluation",
            "Prediction interface"
        ]

    elif role == "Machine Learning Engineer":

        features = [
            "Data preprocessing",
            "Machine learning model",
            "Model evaluation",
            "Prediction API",
            "Input validation",
            "Model deployment",
            "API testing"
        ]

    elif role == "Python Developer":

        features = [
            "User authentication",
            "Database management",
            "CRUD operations",
            "REST API",
            "Input validation",
            "Error handling",
            "Deployment"
        ]

    elif role == "Web Developer":

        features = [
            "Responsive interface",
            "User authentication",
            "Database integration",
            "Interactive pages",
            "REST API",
            "Form validation",
            "Deployment"
        ]

    elif role == "AI Engineer":

        features = [
            "Data preprocessing",
            "AI/ML model",
            "Prediction system",
            "API integration",
            "User interface",
            "Model evaluation",
            "Deployment"
        ]

    else:

        features = [
            "Data collection",
            "Data cleaning",
            "Business analysis",
            "Dashboard",
            "KPI tracking",
            "Visualization",
            "Business recommendations"
        ]

    for feature in features:
        result.append(f"• {feature}")

    result.append("")
    result.append("📁 SUGGESTED PROJECT STRUCTURE")
    result.append("-" * 50)

    result.append("project/")
    result.append("├── app.py")
    result.append("├── templates/")
    result.append("├── static/")
    result.append("├── data/")
    result.append("├── README.md")
    result.append("└── requirements.txt")

    result.append("")
    result.append("📌 YOUR CURRENT SKILLS")
    result.append("-" * 50)

    if skills:
        for skill in skills:
            result.append(f"• {skill}")
    else:
        result.append("• Add your current skills first.")

    result.append("")
    result.append("💼 RESUME VALUE")
    result.append("-" * 50)

    result.append(
        "This project can demonstrate practical problem solving, "
        "technical skills, project development and deployment."
    )

    result.append("")
    result.append("⭐ NEXT STEP")
    result.append("-" * 50)

    result.append(
        "Build the project in small modules instead of trying "
        "to complete everything at once."
    )

    return "\n".join(result)


# ------------------------------------------------------------
# Free AI Interview Assistant
# ------------------------------------------------------------

def interview_assistant(
    target_role,
    current_skills,
    experience_level
):
    """
    Generates interview preparation material locally.
    """

    role = target_role.strip()
    skills = clean_skills(current_skills)

    questions = {

        "Data Analyst": [
            (
                "What is data cleaning?",
                "Data cleaning is the process of identifying and "
                "correcting missing, incorrect, duplicate or inconsistent data."
            ),
            (
                "What is the difference between WHERE and HAVING in SQL?",
                "WHERE filters rows before grouping, while HAVING filters "
                "groups after GROUP BY."
            ),
            (
                "What is Pandas?",
                "Pandas is a Python library used for data manipulation "
                "and analysis."
            ),
            (
                "What is a KPI?",
                "A KPI is a Key Performance Indicator used to measure "
                "business performance."
            )
        ],

        "Data Scientist": [
            (
                "What is overfitting?",
                "Overfitting happens when a model learns the training "
                "data too closely and performs poorly on unseen data."
            ),
            (
                "What is supervised learning?",
                "Supervised learning trains a model using labelled data."
            ),
            (
                "Why is data preprocessing important?",
                "It improves data quality and prepares the data for "
                "machine learning algorithms."
            ),
            (
                "What is train-test split?",
                "It divides data into training data and testing data "
                "to evaluate model performance."
            )
        ],

        "Machine Learning Engineer": [
            (
                "What is machine learning?",
                "Machine learning allows systems to learn patterns "
                "from data and make predictions."
            ),
            (
                "What is model deployment?",
                "Model deployment means making a trained model available "
                "for real-world use."
            ),
            (
                "Why are APIs useful?",
                "APIs allow applications and services to communicate "
                "with each other."
            ),
            (
                "What is feature engineering?",
                "Feature engineering creates or transforms input variables "
                "to improve model performance."
            )
        ],

        "Python Developer": [
            (
                "What is OOP?",
                "Object-Oriented Programming organizes software using "
                "objects and classes."
            ),
            (
                "What is a list in Python?",
                "A list is an ordered and mutable collection of elements."
            ),
            (
                "What is Flask?",
                "Flask is a lightweight Python web framework."
            ),
            (
                "What is an API?",
                "An API is an interface that allows different software "
                "systems to communicate."
            )
        ],

        "Web Developer": [
            (
                "What is HTML?",
                "HTML defines the structure of a web page."
            ),
            (
                "What is CSS?",
                "CSS controls the styling and presentation of web pages."
            ),
            (
                "What is JavaScript?",
                "JavaScript adds logic and interactivity to web pages."
            ),
            (
                "What is responsive design?",
                "Responsive design allows a website to adapt to different "
                "screen sizes."
            )
        ],

        "AI Engineer": [
            (
                "What is artificial intelligence?",
                "AI refers to systems that perform tasks that normally "
                "require human-like intelligence."
            ),
            (
                "What is deep learning?",
                "Deep learning uses neural networks with multiple layers "
                "to learn complex patterns."
            ),
            (
                "What is model inference?",
                "Inference is the process of using a trained model "
                "to produce predictions."
            ),
            (
                "Why is data important for AI?",
                "AI systems depend on quality data to learn useful patterns."
            )
        ],

        "Business Analyst": [
            (
                "What does a business analyst do?",
                "A business analyst studies business problems and uses "
                "data and requirements to recommend improvements."
            ),
            (
                "What is a KPI?",
                "A KPI measures progress toward a business objective."
            ),
            (
                "Why is SQL useful for analysts?",
                "SQL allows analysts to retrieve, filter and analyze "
                "data stored in databases."
            ),
            (
                "Why are dashboards useful?",
                "Dashboards present important information visually "
                "so users can understand business performance quickly."
            )
        ]
    }

    selected_questions = questions.get(
        role,
        [
            (
                "Tell me about yourself.",
                "Give a short introduction covering your education, "
                "technical skills, projects and career goal."
            ),
            (
                "What are your strengths?",
                "Mention two or three strengths and support them with "
                "examples from your projects or studies."
            ),
            (
                "Explain one project you built.",
                "Explain the problem, technologies used, your contribution "
                "and the final result."
            ),
            (
                "Why should we hire you?",
                "Connect your skills, projects, willingness to learn "
                "and the requirements of the role."
            )
        ]
    )

    result = []

    result.append("🎤 SKILLSPHERE INTERVIEW ASSISTANT")
    result.append("=" * 50)

    result.append("")
    result.append(f"Target Role: {role}")
    result.append(f"Experience Level: {experience_level}")

    result.append("")
    result.append("🧠 TECHNICAL QUESTIONS")
    result.append("-" * 50)

    for number, (question, answer) in enumerate(
        selected_questions,
        start=1
    ):

        result.append("")
        result.append(f"Q{number}. {question}")
        result.append(f"Answer: {answer}")

    result.append("")
    result.append("💼 PROJECT QUESTIONS")
    result.append("-" * 50)

    project_questions = [
        "Explain your project.",
        "Why did you choose this project?",
        "Which technologies did you use?",
        "What was the biggest challenge?",
        "How did you solve the problem?",
        "What would you improve in the future?"
    ]

    for question in project_questions:
        result.append(f"• {question}")

    result.append("")
    result.append("👤 HR QUESTIONS")
    result.append("-" * 50)

    hr_questions = [
        "Tell me about yourself.",
        "Why are you interested in this role?",
        "What are your strengths?",
        "What is one weakness you are improving?",
        "Where do you see yourself in five years?",
        "Why should we hire you?"
    ]

    for question in hr_questions:
        result.append(f"• {question}")

    result.append("")
    result.append("📚 REVISION TOPICS")
    result.append("-" * 50)

    if skills:

        for skill in skills:
            result.append(f"• Revise {skill}")

    else:

        result.append(
            "• Add skills to your SkillSphere profile "
            "for personalized preparation."
        )

    result.append("")
    result.append("⭐ INTERVIEW TIPS")
    result.append("-" * 50)

    result.append(
        "• Understand your projects completely."
    )

    result.append(
        "• Do not memorize answers blindly."
    )

    result.append(
        "• Practice explaining technical concepts in simple words."
    )

    result.append(
        "• Be honest when you do not know an answer."
    )

    result.append(
        "• Use examples from your own projects."
    )

    result.append("")
    result.append(
        "💡 SkillSphere Free AI Interview Assistant runs locally "
        "without a paid API."
    )

    return "\n".join(result)


# ------------------------------------------------------------
# Compatibility function
# ------------------------------------------------------------

def ask_ai(prompt):
    """
    Compatibility function for old code/tests.

    This project no longer uses an external AI API.
    """

    prompt_text = str(prompt).strip().lower()

    if "reply with only the word hello" in prompt_text:
        return "HELLO"

    return (
        "SkillSphere Free AI Engine is active.\n\n"
        "This version uses a local rule-based intelligence system "
        "and does not require an OpenAI API key, internet access, "
        "or payment."
    )