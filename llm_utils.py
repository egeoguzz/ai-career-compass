from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def extract_profile_from_cv(cv_text: str) -> dict:
    print(cv_text)
    prompt = f"""
    You are a technical recruiter reviewing a candidate's CV.
    
    Extract the following structured JSON data:
    
    {{ "personal_info": {{ "name": "", "email": "", "location": "", "linkedin": "", "github": "" }},
      "skills": [{{ "name": "Python", "level": "expert" }}],
      "experience": [{{ "position": "", "company": "", "start_date": "", "end_date": "", "description": "" }}],
      "education": [{{ "school": "", "degree": "", "field": "", "start_year": "", "end_year": "" }}]
    }}
    
    If you are unsure about a field, set it as null.
    Now here is the raw CV text:
    \"\"\"  
    {cv_text}
    \"\"\"
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content


def generate_career_advice(profile_json, role, level):
    prompt = f"""
    Here is the candidate's profile (in JSON):
    {profile_json}

    Their dream role is: {role}
    Their experience level is: {level}

    Please do two things:
    1. Give a detailed, personalized career roadmap for this user.
    2. Also, give a 'role_fit_score' between 0 and 100 indicating how ready they are for this dream role.

    Respond in this exact JSON format:
    {{
      "career_advice": "...",
      "role_fit_score": 73
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a career coach that help people achieve their goals."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

