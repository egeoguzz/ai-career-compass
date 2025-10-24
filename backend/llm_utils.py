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

    Based on this, generate the following in JSON format:
    {{
      "career_advice": "string - a paragraph of tailored advice",
      "missing_skills": ["string", "string"],
      "learning_path": ["string - step 1", "string - step 2", "..."],
      "role_fit_score": number - from 0 to 100 (how ready are they for the goal?)
    }}
    
    Only return valid JSON. Do not add explanations.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a career coach."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

