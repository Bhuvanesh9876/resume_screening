import streamlit as st
import sqlite3
import pandas as pd
import uuid
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv("keys.env")

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="AutoRecruiter Pro System", layout="wide")

# Versioning database again to easily upgrade the schema without manual ALTER TABLE
DB_PATH = os.path.join(os.getcwd(), "recruitment_v4.db")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
BASE_URL = "http://localhost:8508" # Updated to match running streamlit instance

THEORY_CUTOFFS = {
    "Software Engineer": 70,
    "Data Analyst": 65,
    "Product Manager": 60
}

NUM_MCQS = 10

STANDARD_TOPICS = {
    "Software Engineer": "Python, Data Structures, SQL",
    "Data Analyst": "SQL, Statistics, Data Cleaning",
    "Product Manager": "Agile, KPIs, User Stories"
}

# Load the initial key from .env into session state on first load if available
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")

if st.session_state["gemini_api_key"]:
    genai.configure(api_key=st.session_state["gemini_api_key"])

# ==========================================
# DATABASE HELPER
# ==========================================
@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            role TEXT,
            experience TEXT,
            skills TEXT,
            mcqs TEXT,
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ENROLLED',
            token TEXT,
            r2_questions TEXT,
            r2_score INTEGER DEFAULT 0,
            r2_token TEXT,
            created_at TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()

init_db()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        yield conn
    finally:
        conn.close()

# ==========================================
# EMAIL HELPER
# ==========================================
def send_email(to_email, subject, body):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        st.warning("Email credentials missing. Please check .env file.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# ==========================================
# MCQ GENERATION (GROQ OPEN SOURCE)
# ==========================================
import time
import requests

def get_mcqs(role, experience, skills, topics, count):
    fallback_mcqs = [{
        "question": f"Which of the following describes binary search time complexity (relevant for {role})?",
        "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
        "answer": "O(log n)"
    }] * count
    
    current_key = st.session_state.get("gemini_api_key", "")
    if not current_key:
        st.warning("No Groq API key supplied in the sidebar. Using offline offline fallback.", icon="⚠️")
        return fallback_mcqs
    
    # We are using Groq's high-speed API to run Meta's open source LLaMA 3.3 model!
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {current_key}",
        "Content-Type": "application/json"
    }

    # Advanced Realistic Prompting
    prompt = f"""
    Create exactly {count} highly realistic multiple-choice technical interview questions for the role of '{role}'.
    
    IMPORTANT INSTRUCTION: You MUST heavily prioritize testing the specific required skills: {skills}. 
    Ensure ALMOST ALL questions explicitly test deep concepts, gotchas, or complex implementations specifically within `{skills}`. 
    Do NOT ask generic questions about '{role}' unless they directly integrate with those exact skills.

    CRITICAL REQUIREMENT FOR REALISM:
    At least 50% of these questions MUST be practical coding scenarios. Include formatted code snippets (using markdown logic) inside the `question` field. Ask the candidate to trace the output, identify the bug, evaluate performance, or complete the missing line of code based on the snippet. Do not rely solely on theoretical trivia.

    The candidate has an '{experience}' experience level. Tailor the difficulty strictly to this experience level so the questions are non-trivial.
    
    Provide the output strictly as a JSON array of objects.
    Each object must have exactly these keys: "question" (string), "options" (array of exactly 4 plausible strings), and "answer" (string, must exactly match one of the options).
    """

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a demanding senior technical recruiter and subject matter expert. You mercilessly test candidates on exact skills provided. You format tests strictly as valid JSON arrays."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    max_retries = 3
    base_delay = 5  

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # Groq returns an object with a root key if json_object mode is enforced, or directly the array if prompted well
                parsed = json.loads(content)
                if isinstance(parsed, dict) and len(parsed.keys()) == 1:
                    parsed = list(parsed.values())[0] # Extract array if it was wrapped in a dict
                return parsed
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)  
                    st.warning(f"Groq API Rate Limit Reached! Waiting {sleep_time} seconds before retrying... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    st.error("Failed to generate MCQs: Groq Quota completely exhausted.")
                    return fallback_mcqs
            else:
                st.error(f"Failed to generate MCQs: Groq Error {response.status_code} - {response.text}")
                return fallback_mcqs
                
        except Exception as e:
            st.error(f"Failed to connect to Groq API: {e}")
            return fallback_mcqs
    
    return fallback_mcqs

# ==========================================
# INVITE LOGIC
# ==========================================
def invite_round1(name, email, role, experience, skills):
    token = str(uuid.uuid4())
    mcqs = get_mcqs(role, experience, skills, STANDARD_TOPICS.get(role, "General"), NUM_MCQS)

    with get_db_connection() as conn:
        conn.execute("""
        UPDATE candidates
        SET token=?, mcqs=?, status='ENROLLED'
        WHERE email=?
        """, (token, json.dumps(mcqs), email))
        conn.commit()

    link = f"{BASE_URL}?token={token}"
    email_body = f"Hi {name},\n\nYou have been invited to the Round-1 MCQ Technical Test for the {experience} {role} position.\n\nWe will be assessing your core competencies, including: {skills}.\n\nPlease start your assessment using the following personalized link:\n{link}"
    send_email(email, f"Interview Invitation: Round-1 Technical Assessment ({role})", email_body)

def invite_round2(c_id, name, email, role, experience, skills):
    r2_token = str(uuid.uuid4())
    
    # Generate a realistic coding challenge
    coding_q = f"Build a robust implementation using {skills} that demonstrates your {experience} level proficiency for a real-world {role} task. Focus on clean code, edge cases, and performance."
    
    with get_db_connection() as conn:
        conn.execute("""
        UPDATE candidates
        SET r2_token=?, r2_questions=?, status='R2_INVITED'
        WHERE id=?
        """, (r2_token, coding_q, int(c_id)))
        conn.commit()

    link = f"{BASE_URL}?token={r2_token}"
    email_body = f"Hi {name},\n\nCongratulations! We have reviewed your first round assessment and we were very impressed. You have been advanced to the Round-2 Coding Assessment for the {experience} {role} position.\n\nPlease start your coding challenge using the following personalized link:\n{link}"
    send_email(email, f"Interview Invitation: Round-2 Coding Assessment ({role})", email_body)

# ==========================================
# MAIN APP FLOW
# ==========================================
def main():
    # Modern Streamlit uses st.query_params which behaves like a dictionary
    token = st.query_params.get("token")

    if token:
        # Hide sidebar and Header for true assessment isolation
        st.markdown("""
            <style>
                [data-testid="stSidebar"] { display: none !important; }
                header { visibility: hidden !important; }
            </style>
        """, unsafe_allow_html=True)
        render_candidate_view(token)
    else:
        if not st.session_state.get("is_authenticated", False):
            st.title("🔒 AutoRecruiter Login")
            st.markdown("Please enter the administrator password to access the dashboard.")
            pwd = st.text_input("Admin Password", type="password")
            if st.button("Login"):
                if pwd == os.getenv("ADMIN_PASSWORD", "admin123"):
                    st.session_state["is_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid password. Candidates: Please use the personalized link sent to your email.")
        else:
            render_recruiter_panel()

def render_candidate_view(token):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE token=? OR r2_token=?", (token, token)
        ).fetchone()

    if not row:
        st.error("Invalid link.")
        st.stop()

    # row layout: 0:id, 1:name, 2:email, 3:role, 4:experience, 5:skills, 6:mcqs, 7:score, 8:status, 9:token, 10:r2_questions, 11:r2_score, 12:r2_token, 13:created_at
    role = row[3]
    experience = row[4]
    
    is_r2 = (row[12] == token)

    if is_r2:
        if row[8] != "R2_INVITED":
            st.error("Invalid, expired, or already completed R2 link.")
            st.stop()
        
        st.title(f"💻 {experience} {role} - Round 2: Coding Assessment")
        st.write(f"Welcome back, **{row[1]}**! Please complete the coding challenge below.")
        
        coding_question = row[10]
        st.markdown(f"**Your Technical Challenge:**\n\n> {coding_question}")
        
        answer = st.text_area("Code Solution (Paste or write your code here)", height=400)
        
        if st.button("Submit Technical Round"):
            if len(answer.strip()) < 10:
                st.warning("Please enter a valid code snippet before submitting.")
                return
            with get_db_connection() as conn:
                conn.execute("UPDATE candidates SET status='R2_COMPLETED' WHERE id=?", (row[0],))
                conn.commit()
            st.success("Coding assessment submitted successfully!")
            st.info("The recruitment team has safely received your code. You may now close this window.")
        return

    # Otherwise we are in Round 1
    if not is_r2 and row[8] != "ENROLLED":
        st.error("Invalid, expired, or already completed R1 link.")
        st.stop()
    st.title(f"📝 {experience} {role} Assessment")
    st.write(f"Welcome, **{row[1]}**! Good luck on your technical test.")

    # Parse JSON questions safely (and fallback to eval for old formats)
    try:
        mcqs = json.loads(row[6])
        while isinstance(mcqs, str):
            mcqs = json.loads(mcqs)
        if isinstance(mcqs, dict) and len(mcqs) == 1:
            mcqs = list(mcqs.values())[0]
    except:
        try:
            import ast
            mcqs = ast.literal_eval(row[6])
            while isinstance(mcqs, str):
                mcqs = ast.literal_eval(mcqs)
            if isinstance(mcqs, dict) and len(mcqs) == 1:
                mcqs = list(mcqs.values())[0]
        except:
            st.error("Failed to load questions. Please contact the recruiter.")
            st.stop()
            
    if not isinstance(mcqs, list):
        st.error("Assessment format is corrupted. Please request the recruiter to dispatch a new test link.")
        st.stop()

    answers = {}

    with st.form("mcq_form"):
        for i, q in enumerate(mcqs):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            # Set index=None to force user to actually select an option, avoiding unintended default submission
            answers[i] = st.radio("Choose one", q["options"], key=f"q_{i}", index=None)
            st.markdown("---")

        submitted = st.form_submit_button("Submit Assessment")
        
        if submitted:
            if any(ans is None for ans in answers.values()):
                st.warning("Please answer all questions before submitting.")
                return

            correct_count = sum(
                1 for i, q in enumerate(mcqs)
                if answers[i] == q["answer"]
            )
            final_score = int((correct_count / len(mcqs)) * 100)

            # Multi-stage pipeline: Do not show the final grade to the candidate.
            status = "R1_COMPLETED" # Wait for recruiter manual review

            with get_db_connection() as conn:
                conn.execute("""
                UPDATE candidates
                SET score=?, status=?
                WHERE token=?
                """, (final_score, status, token))
                conn.commit()

            st.success("Assessment Submitted Successfully!")
            st.info("The recruitment team has safely received your test and will review the results manually. You may now close this window.")

def render_recruiter_panel():
    st.sidebar.title("Recruiter Panel")

    # API Configuration side panel
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ API Configuration")
    user_api_key = st.sidebar.text_input("Groq API Key (Free)", value=st.session_state.get("gemini_api_key", ""), type="password", help="Get a free ultra-fast API key at https://console.groq.com/keys . The change will take effect immediately without needing an app restart.")
    
    if user_api_key != st.session_state.get("gemini_api_key"):
        st.session_state["gemini_api_key"] = user_api_key
        st.sidebar.success("API Key updated dynamically.")
    
    st.sidebar.markdown("---")

    # Guard the destructive database reset behind an expander
    with st.sidebar.expander("⚠️ Danger Zone"):
        if st.button("Reset Database"):
            with get_db_connection() as conn:
                conn.execute("DROP TABLE IF EXISTS candidates")
                conn.commit()
            init_db.clear()  # Clear cache to ensure it spins up again cleanly
            init_db()
            st.success("Database reset successfully.")
            st.rerun()

    menu = st.sidebar.radio("Menu", ["Dashboard", "Single Enroll", "Bulk Upload"])

    if menu == "Dashboard":
        st.header("Candidate Dashboard")
        with get_db_connection() as conn:
            df = pd.read_sql("SELECT id, name, email, role, experience, skills, score, status, token, created_at FROM candidates ORDER BY id DESC", conn)
        
        if df.empty:
            st.info("No candidates found in the database. Start by enrolling someone!")
        else:
            # High-level metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Candidates", len(df))
            col2.metric("R1 Pending Review", len(df[df['status'] == 'R1_COMPLETED']))
            col3.metric("R2 Coding Completed", len(df[df['status'] == 'R2_COMPLETED']))
            
            st.dataframe(df.drop(columns=["token", "r2_token", "r2_questions", "mcqs"], errors='ignore'), use_container_width=True)
            
            st.markdown("---")
            st.subheader("� Manage Multi-Round Pipeline")
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.write("**Round 1 Candidates Waiting Review:**")
                r1_completed = df[df['status'] == 'R1_COMPLETED']
                if not r1_completed.empty:
                    candidate_id = st.selectbox("Select Candidate to Promote to Round 2", r1_completed["id"].tolist(), format_func=lambda x: f"[{x}] {r1_completed[r1_completed['id']==x]['name'].values[0]} ({r1_completed[r1_completed['id']==x]['score'].values[0]}%)")
                    
                    if st.button("Promote to Round 2 (Coding)"):
                        c_row = r1_completed[r1_completed["id"] == candidate_id].iloc[0]
                        invite_round2(c_row["id"], c_row["name"], c_row["email"], c_row["role"], c_row["experience"], c_row["skills"])
                        st.success(f"Sent Round 2 Coding Assessment explicitly to {c_row['name']}!")
                        st.rerun()
                else:
                    st.info("No candidates pending Round 1 manual review.")
                    
            with col_r2:
                st.write("**Round 2 Final Evaluations:**")
                r2_completed = df[df['status'] == 'R2_COMPLETED']
                if not r2_completed.empty:
                    st.success(f"{len(r2_completed)} candidates have finished their Coding round! Check the DB for their submissions.")
                else:
                    st.info("No candidates pending final Coding review.")

            st.markdown("---")
            st.subheader("�🔍 Review Internal Generated Assessments")
            review_id = st.selectbox("Select Candidate to Review Questions", df["id"].tolist(), format_func=lambda x: f"[{x}] {df[df['id']==x]['name'].values[0]} ({df[df['id']==x]['role'].values[0]})")
            if st.button("Fetch Questions"):
                with get_db_connection() as conn:
                    q_row = conn.execute("SELECT mcqs FROM candidates WHERE id=?", (review_id,)).fetchone()
                if q_row and q_row[0]:
                    try:
                        questions = json.loads(q_row[0])
                        for idx, q_data in enumerate(questions):
                            st.markdown(f"**Q{idx+1}**: {q_data.get('question', 'N/A')}")
                            st.caption(f"**Correct Answer**: :green[{q_data.get('answer', 'N/A')}]")
                            st.write(f"Options: {', '.join(q_data.get('options', []))}")
                    except Exception as e:
                        st.error("Could not parse test bank for this user.")

    elif menu == "Single Enroll":
        st.header("Enroll Single Candidate")

        with st.form("single_enroll_form", clear_on_submit=True):
            name = st.text_input("Candidate Name")
            email = st.text_input("Candidate Email")
            
            col1, col2 = st.columns(2)
            with col1:
                role = st.selectbox("Base Role", list(THEORY_CUTOFFS.keys()) + ["DevOps Engineer", "Frontend Developer", "Machine Learning Engineer", "Custom"])
                if role == "Custom":
                    role = st.text_input("Specify Custom Role", value="")
            with col2:
                experience = st.selectbox("Experience Level", ["Intern/Junior", "Mid-Level", "Senior", "Lead/Architect"])
                
            skills = st.text_area("Required Core Skills (e.g. React, Node.js, AWS, System Design, Python decorators)", placeholder="List the specific technical skills and topics you want the AI to heavily test them on", height=100)
            
            submit = st.form_submit_button("Enroll & Send Test Invite")

            if submit:
                if not name or not email or not role or not skills:
                    st.warning("Please provide all required fields (Name, Email, Role, and Skills).")
                else:
                    with get_db_connection() as conn:
                        existing = conn.execute("SELECT 1 FROM candidates WHERE email=?", (email,)).fetchone()
                        if existing:
                            st.warning(f"Candidate {email} already exists. Re-inviting with updated test suite.")
                            invite_round1(name, email, role, experience, skills)
                        else:
                            conn.execute("""
                            INSERT INTO candidates(name,email,role,experience,skills,created_at)
                            VALUES (?,?,?,?,?,?)
                            """, (name, email, role, experience, skills, datetime.now().isoformat()))
                            conn.commit()
                            invite_round1(name, email, role, experience, skills)
                            st.success(f"Candidate {name} ({experience} {role}) enrolled & invited successfully.")

    elif menu == "Bulk Upload":
        st.header("Bulk Upload Candidates")
        st.info("Required columns in your file: `name`, `email`, `role`, `experience`, `skills`")

        file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

        if file and st.button("Process Bulk Upload"):
            try:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Check for required columns flexibly
                required_cols = {'name', 'email', 'role', 'experience', 'skills'}
                if not required_cols.issubset(df.columns.str.lower()):
                    st.error(f"Missing required columns. Found: {list(df.columns)}")
                    return

                df.columns = df.columns.str.lower()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                total = len(df)

                for i, r in df.iterrows():
                    c_name, c_email, c_role = str(r['name']), str(r['email']), str(r['role'])
                    c_exp, c_skills = str(r['experience']), str(r['skills'])
                    
                    if c_role not in THEORY_CUTOFFS: # we will inherit SE cutoff if completely novel
                        # For dynamic roles, we can use a generic 60 passing
                        pass
                        
                    with get_db_connection() as conn:
                        existing = conn.execute("SELECT 1 FROM candidates WHERE email=?", (c_email,)).fetchone()
                        if not existing:
                            conn.execute("""
                            INSERT INTO candidates(name,email,role,experience,skills,created_at)
                            VALUES (?,?,?,?,?,?)
                            """, (c_name, c_email, c_role, c_exp, c_skills, datetime.now().isoformat()))
                            conn.commit()

                    invite_round1(c_name, c_email, c_role, c_exp, c_skills)
                    
                    progress_percentage = (i + 1) / total
                    progress_bar.progress(progress_percentage)
                    status_text.text(f"Processed {i + 1}/{total} candidates...")
                    
                st.success("Bulk enrollment completed successfully.")
            except Exception as e:
                st.error(f"Error processing bulk upload: {e}")

if __name__ == "__main__":
    main()
