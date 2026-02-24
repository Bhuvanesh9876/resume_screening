import streamlit as st
from supabase_client import supabase
from utils.auth_manager import restore_session, track_activity
from utils.navbar import render_navbar

restore_session()
track_activity()

if "user" not in st.session_state:
    st.switch_page("pages/0_🔐_Login.py")

render_navbar()

st.header("📄 Job Configuration")

# Create a placeholder at the top for error messages
error_placeholder = st.empty()

# Predefined skill options for dropdown
SKILL_OPTIONS = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin",
    "R", "MATLAB", "Scala", "Perl", "HTML", "CSS",
    
    # Web Development
    "React", "Angular", "Vue.js", "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "ASP.NET", "Laravel", "Ruby on Rails", "Next.js", "Svelte", "jQuery", "Bootstrap", "Tailwind CSS",
    
    # Mobile Development
    "React Native", "Flutter", "Android Development", "iOS Development", "Xamarin", "Ionic",
    
    # Databases
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Oracle", "SQLite", "Cassandra", "DynamoDB",
    "Firebase", "Elasticsearch", "Neo4j", "MS SQL Server",
    
    # Cloud & DevOps
    "AWS", "Azure", "Google Cloud Platform", "Docker", "Kubernetes", "CI/CD", "Jenkins", "GitLab CI",
    "GitHub Actions", "Terraform", "Ansible", "Linux", "Unix", "Shell Scripting",
    
    # Data Science & AI
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Apache Spark", "Hadoop", "NLP",
    "Computer Vision", "Statistical Analysis",
    
    # Other Technical
    "Git", "REST APIs", "GraphQL", "Microservices", "Agile", "Scrum", "JIRA", "Testing", "Unit Testing",
    "Integration Testing", "Selenium", "Jest", "Pytest", "API Development", "System Design",
    "Object-Oriented Programming", "Data Structures", "Algorithms",
    
    # Soft Skills
    "Communication", "Leadership", "Problem Solving", "Team Collaboration", "Project Management",
    "Time Management", "Critical Thinking", "Analytical Skills", "Creativity", "Adaptability"
]

# Sync widgets with job_data if loaded from history
if st.session_state.get("config_loaded_from_history"):
    st.success("✅ Configuration loaded from history! Review the data below and click 'Save & Continue' to process.")
    
    # Pre-populate widget session state keys
    job_data = st.session_state.get("job_data", {})
    st.session_state["input_job_title"] = job_data.get("job_title", "")
    st.session_state["input_job_desc"] = job_data.get("job_description", "")
    st.session_state["input_qualification"] = job_data.get("qualification", "")
    st.session_state["input_experience"] = job_data.get("required_experience", 0)
    st.session_state["input_good_to_have"] = ", ".join(job_data.get("good_to_have_skills", [])) if isinstance(job_data.get("good_to_have_skills"), list) else job_data.get("good_to_have_skills", "")
    
    # Handle Must Have Skills (complex list vs string)
    saved_skills = job_data.get("must_have_skills", [])
    if isinstance(saved_skills, str):
        saved_skills = [s.strip() for s in saved_skills.split(",") if s.strip()]
        
    # Separate skills
    dropdown_skills = [s for s in saved_skills if s in SKILL_OPTIONS]
    custom_skills = [s for s in saved_skills if s not in SKILL_OPTIONS]
    
    st.session_state["input_skills_dropdown"] = dropdown_skills
    st.session_state["input_custom_skills"] = ", ".join(custom_skills)
    
    st.session_state["config_loaded_from_history"] = False  # Clear flag

# Clear any previous validation error on page load if not triggered by button
if "validation_error" not in st.session_state:
    st.session_state.validation_error = None

# Display validation error at the top if present
if st.session_state.validation_error:
    error_placeholder.error(st.session_state.validation_error)
    st.session_state.validation_error = None  # Clear after displaying

job_title = st.text_input("Job Title", key="input_job_title")
job_description = st.text_area("Job Description", height=150, key="input_job_desc")

# Display word count with color coding
current_word_count = len(job_description.split()) if job_description else 0
if current_word_count < 30:
    word_count_color = "🔴"
    word_count_message = f"{word_count_color} Word count: **{current_word_count}** / 30-2500 (minimum 30 words required)"
elif current_word_count > 2500:
    word_count_color = "🔴"
    word_count_message = f"{word_count_color} Word count: **{current_word_count}** / 30-2500 (exceeds maximum limit)"
else:
    word_count_color = "🟢"
    word_count_message = f"{word_count_color} Word count: **{current_word_count}** / 30-2500"

st.caption(word_count_message)

st.divider()

# Job Requirements Section
st.subheader("📋 Job Requirements")

col1, col2 = st.columns(2)

with col1:
    qualification = st.text_input(
        "Required Qualification",
        placeholder="e.g., Bachelor's in Computer Science, MBA, PhD",
        key="input_qualification"
    )

with col2:
    required_experience = st.number_input(
        "Required Experience (Years)", 
        min_value=0, 
        step=1,
        key="input_experience"
    )

st.divider()

# Skills Section
st.subheader("🔧 Skills Requirements")



# Required Skills - Multiselect dropdown
# Get saved skills and separate into dropdown-available and custom skills
saved_must_have_skills = st.session_state.get("job_data", {}).get("must_have_skills", [])

# Handle if saved as string (from old records)
if isinstance(saved_must_have_skills, str):
    saved_must_have_skills = [s.strip() for s in saved_must_have_skills.split(",") if s.strip()]

# Separate skills that are in dropdown vs custom skills
dropdown_skills_default = [s for s in saved_must_have_skills if s in SKILL_OPTIONS]
custom_skills_saved = [s for s in saved_must_have_skills if s not in SKILL_OPTIONS]

# Initialize session state if not already set (avoid default vs state conflict)
if "input_skills_dropdown" not in st.session_state:
    st.session_state.input_skills_dropdown = dropdown_skills_default

must_have_skills_selected = st.multiselect(
    "Required Skills",
    options=sorted(SKILL_OPTIONS),
    help="Select the primary skills required for this position",
    key="input_skills_dropdown"
)

# Option to add custom skills not in the list
custom_skills_str = ", ".join(custom_skills_saved) if custom_skills_saved else ""
if "input_custom_skills" not in st.session_state:
    st.session_state.input_custom_skills = custom_skills_str

custom_must_have = st.text_input(
    "Complementary Skills (comma separated)",
    placeholder="e.g., SAP, Salesforce, domain-specific tools...",
    help="Add any additional skills not listed in the dropdown",
    key="input_custom_skills"
)

# Handle good_to_have_skills - could be string or list
# Already handled in pre-fill block for 'input_good_to_have'

good_to_have_skills = st.text_input(
    "Preferred Qualifications (comma separated)",
    key="input_good_to_have"
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save & Continue", type="primary", use_container_width=True):
        if not job_title or not job_description:
            st.session_state.validation_error = "⚠️ Job title and description are required."
            st.rerun()
        else:
            # Validate job description word count
            word_count = len(job_description.split())
            
            if word_count < 30:
                st.session_state.validation_error = f"⚠️ Job description must be between 30 to 2500 words.\n\nCurrent word count: **{word_count}** words\n\nPlease add at least **{30 - word_count}** more words."
                st.rerun()
            elif word_count > 2500:
                st.session_state.validation_error = f"⚠️ Job description must be between 30 to 2500 words.\n\nCurrent word count: **{word_count}** words\n\nPlease remove at least **{word_count - 2500}** words."
                st.rerun()
            else:
                # Combine dropdown selections with custom skills
                must_list = list(must_have_skills_selected)  # Skills from dropdown
                
                # Add additional competencies if provided
                if custom_must_have:
                    custom_skills = [s.strip() for s in custom_must_have.split(",") if s.strip()]
                    must_list.extend(custom_skills)
                
                # Remove duplicates while preserving order
                must_list = list(dict.fromkeys(must_list))
                
                good_list = [s.strip() for s in good_to_have_skills.split(",") if s.strip()]
                
                st.session_state["job_data"] = {
                    "job_title": job_title,
                    "job_description": job_description,
                    "qualification": qualification,
                    "required_experience": required_experience,
                    "must_have_skills": must_list,
                    "good_to_have_skills": good_list
                }
                
                if supabase is not None:
                    try:
                        job_res = supabase.table("job_configs").insert({
                            "user_id": st.session_state["user"].id,
                            "job_title": job_title,
                            "job_description": job_description,
                            "required_qualification": qualification,
                            "required_experience": required_experience,
                            "must_have_skills": must_list,  # Passed as list (Postgres Text Array)
                            "good_to_have_skills": good_list  # Passed as list (Postgres Text Array)
                        }).execute()
                        
                        # Capture and store the Job Config ID
                        if job_res.data:
                            st.session_state["job_data"]["job_id"] = job_res.data[0]["id"]
                            
                    except Exception as e:
                        print(f"Error saving job config: {e}")
                        st.error(f"❌ Database Error: {str(e)}")
                        pass
                
                st.success("Job configuration saved!")
                st.switch_page("pages/2_⚙️_Processing.py")

with col2:
    if st.button("📊 View History", use_container_width=True):
        st.switch_page("pages/4_📊_History.py")
