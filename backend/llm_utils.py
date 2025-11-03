from openai import OpenAI
import os
from dotenv import load_dotenv
import json

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
    You are an expert career coach. Based on the candidate's profile and their career goal, provide a structured career plan.

    Here is the candidate's profile (in JSON):
    {profile_json}

    Their dream role is: {role}
    Their experience level is: {level}

    Generate a response in the following JSON format. The "learning_path" should be a list of objects, where each object represents a week of study.

    {{
      "career_advice": "string - A paragraph of tailored advice on how to bridge the gap between their current profile and their dream role.",
      "missing_skills": ["string - A skill the candidate is missing", "string - Another missing skill"],
      "learning_path": [
        {{
          "week": 1,
          "topic": "string - The main theme or technology for this week's learning (e.g., 'Introduction to TensorFlow')",
          "learning_objectives": [
              "string - A specific, actionable learning goal for the week (e.g., 'Build a basic neural network')", 
              "string - Another learning goal for the week"
          ],
          "project_idea": "string - A small, practical project to apply the skills learned during the week (e.g., 'Create an image classifier for cats and dogs')"
        }},
        {{
          "week": 2,
          "topic": "string - Theme for the second week",
          "learning_objectives": ["string - Goal 1 for week 2", "string - Goal 2 for week 2"],
          "project_idea": "string - Project idea for week 2"
        }}
      ],
      "role_fit_score": "number - A score from 0 to 100 representing how ready they are for the goal right now."
    }}

    CRITICAL: Only return valid JSON. Do not add any text or explanations before or after the JSON object.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a career coach bot that provides structured advice in JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


def generate_resource_recommendation(learning_objective: str, sources: list):
    if not sources:
        return {
            "recommended_title": "No specific resource found",
            "recommended_url": "",
            "reason": f"No relevant resources were found in the database for the topic: '{learning_objective}'."
        }
        
    source_texts = []
    for s in sources:
        truncated_content = s['content'][:1000]
        source_texts.append(f"Title: {s['title']}\nURL: {s['url']}\nContent: {truncated_content}...")
    source_text = "\n\n".join(source_texts)

    prompt = f"""
    You are an expert career coach helping a user learn the topic: "{learning_objective}".
    I have found several resources. Based on the provided content snippets, analyze them and recommend the single best one to start with.
    Here are the available resources:
    ---
    {source_text}
    ---
    Now, output a JSON object with your recommendation. The reason should be concise and explain why this resource is a good starting point.
    {{
      "recommended_title": "string - The title of the best resource",
      "recommended_url": "string - The URL of the best resource",
      "reason": "string - A brief explanation of why you chose this resource"
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        response_format={"type": "json_object"}
    )

    llm_response_string = response.choices[0].message.content

    try:
        return json.loads(llm_response_string)
    except json.JSONDecodeError:
        return {
            "recommended_title": "Error processing recommendation",
            "recommended_url": "",
            "reason": "Could not parse the recommendation from the AI model."
        }
        
