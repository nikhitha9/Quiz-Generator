import anthropic
import os


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))  # paste your key

topic = input("Enter a topic: ")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": f"""Generate 5 multiple choice questions about: {topic}

Return ONLY a JSON array, no extra text. Format:
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

print(response.content[0].text)