from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic
import json
import re
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
class TopicRequest(BaseModel):
    topic: str

@app.post("/generate")
def generate_quiz(request: TopicRequest):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Generate 5 multiple choice questions about: {request.topic}

Return ONLY a JSON array, no markdown, no code blocks, no extra text. Just the raw JSON array starting with [ and ending with ]

Format:
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "answer": "A"
  }}
]"""
            }
        ]
    )

    raw = response.content[0].text
    print("Claude raw response:", raw)
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not match:
        return {"error": "Could not parse response", "raw": raw}

    questions = json.loads(match.group())
    return {"questions": questions}


class SubmitRequest(BaseModel):
    topic: str
    questions: list
    user_answers: dict

@app.post("/explain")
def explain_answers(request: SubmitRequest):
    wrong = []
    for i, q in enumerate(request.questions):
        user_ans = request.user_answers.get(str(i), "Not answered")
        if user_ans != q["answer"]:
            wrong.append({
                "question": q["question"],
                "correct_answer": q["answer"],
                "user_answer": user_ans,
                "options": q["options"]
            })

    if not wrong:
        return {"explanation": None, "all_correct": True}

    wrong_text = ""
    for i, w in enumerate(wrong):
        wrong_text += f"""
Question: {w['question']}
Options: {', '.join(w['options'])}
Correct answer: {w['correct_answer']}
User answered: {w['user_answer']}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""A student just took a quiz on "{request.topic}" and got some answers wrong.

For each wrong answer below, explain in simple terms:
1. Why the correct answer is right
2. Why their choice was wrong (if they answered)

Keep each explanation to 2-3 sentences. Be encouraging.

{wrong_text}

Return ONLY a JSON array, no markdown. Format:
[
  {{
    "question": "...",
    "explanation": "..."
  }}
]"""
            }
        ]
    )

    raw = response.content[0].text
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not match:
        return {"explanation": None, "all_correct": False}

    explanations = json.loads(match.group())
    return {"explanations": explanations, "all_correct": False}