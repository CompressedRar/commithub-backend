import requests
from utils import FileStorage
import os
import json

def download_file_from_s3(file_name):
    url = FileStorage.get_file(file_name)
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    return None


import google.generativeai as genai
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)

def evaluate_relevance_with_gemini(file_bytes, mime_type, task_text):
    print("Evaluating relevance with Gemini...")
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    response = model.generate_content([
        {
            "mime_type": mime_type,
            "data": file_bytes
        },
        f"""
        You are an auditor assistant.

        TASK:
        {task_text}

        Analyze the attached document.

        Rate relevance from 0 to 100.

        STRICT RULES:
        - Return ONLY raw JSON
        - Do NOT wrap in markdown
        - Do NOT add explanation outside JSON

        Format:
        {{
            "score": number,
            "reason": "short explanation"
        }}
        """
    ])

    print("Gemini response:", response.text)

    return response.text


def get_relevance_score(file_name, mime_type, task_text):
    file_bytes = download_file_from_s3(file_name)
    if file_bytes is None:
        return None

    relevance_result = evaluate_relevance_with_gemini(file_bytes, mime_type, task_text)
    parsed = json.loads(relevance_result)
    print("Parsed relevance result:", parsed)
    return parsed

def determine_models():
    for m in genai.list_models():
        print(m.name, m.supported_generation_methods)

