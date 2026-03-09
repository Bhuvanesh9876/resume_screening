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

job_data_cache = st.session_state.get("job_data", {})

# Initialize session state keys for all widgets if we have job_data_cache and the widgets aren't set
# (This handles both 'loaded from history' and 'navigated back from another page')
if "config_loaded_from_history" in st.session_state and st.session_state.config_loaded_from_history:
    st.success("✅ Configuration loaded from history! Review the data below and click 'Save & Continue' to process.")
    st.session_state.config_loaded_from_history = False  # Clear flag

if job_data_cache:
    if "input_job_title" not in st.session_state:
        st.session_state.input_job_title = job_data_cache.get("job_title", "")
    if "input_job_desc" not in st.session_state:
        st.session_state.input_job_desc = job_data_cache.get("job_description", "")
    if "input_qualification" not in st.session_state:
        # Load from history (could be string or list now)
        saved_qual = job_data_cache.get("qualification", ["None"])
        if isinstance(saved_qual, str):
            saved_qual = [saved_qual]
        st.session_state.input_qualification = saved_qual
    
    if "input_year_of_passing" not in st.session_state:
        saved_years = job_data_cache.get("year_of_passing", [])
        st.session_state.input_year_of_passing = ", ".join(map(str, saved_years)) if isinstance(saved_years, list) else str(saved_years)
        
    if "input_experience" not in st.session_state:
        st.session_state.input_experience = job_data_cache.get("required_experience", 0)
    
    saved_skills = job_data_cache.get("must_have_skills", [])
    if isinstance(saved_skills, str):
        saved_skills = [s.strip() for s in saved_skills.split(",") if s.strip()]
        
    dropdown_skills = [s for s in saved_skills if s in SKILL_OPTIONS]
    custom_skills = [s for s in saved_skills if s not in SKILL_OPTIONS]
    
    if "input_skills_dropdown" not in st.session_state:
        st.session_state.input_skills_dropdown = dropdown_skills
    if "input_custom_skills" not in st.session_state:
        st.session_state.input_custom_skills = ", ".join(custom_skills)
        
    if "input_good_to_have" not in st.session_state:
        saved_good = job_data_cache.get("good_to_have_skills", [])
        st.session_state.input_good_to_have = ", ".join(saved_good) if isinstance(saved_good, list) else str(saved_good)

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
    qual_options = ["None", "BTech", "MTech", "MCA", "MBA", "BCA", "Any Bachelor's", "Any Master's"]
    qualification = st.multiselect(
        "Required Qualification(s)",
        options=qual_options,
        default=["None"],
        key="input_qualification"
    )
    
    # Year of Passing becomes mandatory if qualification is NOT None
    year_of_passing_str = ""
    # Check if anything other than "None" is selected
    if qualification and "None" not in qualification:
        year_of_passing_str = st.text_input(
            "Allowed Years of Passing (comma separated)",
            placeholder="e.g., 2022, 2023, 2024",
            key="input_year_of_passing",
            help="Enter one or more years. Candidates not matching these specifically will be rejected."
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



must_have_skills_selected = st.multiselect(
    "Required Skills",
    options=sorted(SKILL_OPTIONS),
    help="Select the primary skills required for this position",
    key="input_skills_dropdown"
)

# Option to add custom skills not in the list
custom_must_have = st.text_input(
    "Complementary Skills (comma separated)",
    placeholder="e.g., SAP, Salesforce, domain-specific tools...",
    help="Add any additional skills not listed in the dropdown",
    key="input_custom_skills"
)

good_to_have_skills = st.text_input(
    "Preferred Qualifications (comma separated)",
    key="input_good_to_have"
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save & Continue", type="primary", use_container_width=True):
        if not job_title or not job_description:
            error_placeholder.error("⚠️ Job title and description are required.")
        else:
            # Validate job description word count
            word_count = len(job_description.split())
            
            if word_count < 30:
                error_placeholder.error(f"⚠️ Job description must be between 30 to 2500 words.\n\nCurrent word count: **{word_count}** words\n\nPlease add at least **{30 - word_count}** more words.")
            elif word_count > 2500:
                error_placeholder.error(f"⚠️ Job description must be between 30 to 2500 words.\n\nCurrent word count: **{word_count}** words\n\nPlease remove at least **{word_count - 2500}** words.")
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
                
                # Parse years of passing
                year_list = []
                if year_of_passing_str:
                    year_list = [int(y.strip()) for y in year_of_passing_str.split(",") if y.strip().isdigit()]

                st.session_state["job_data"] = {
                    "job_title": job_title,
                    "job_description": job_description,
                    "qualification": qualification,
                    "year_of_passing": year_list,
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
                            "required_year_of_passing": year_list,
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
                
                st.session_state["autosave_done"] = False
                st.success("Job configuration saved!")
                st.switch_page("pages/2_⚙️_Processing.py")

with col2:
    if st.button("📊 View History", use_container_width=True):
        st.switch_page("pages/4_📊_History.py")
