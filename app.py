from flask import Flask, render_template, request, session, redirect, url_for
import os
import requests

app = Flask(__name__)
app.secret_key = os.urandom(16)  # Automatically generate a secret key

# Replace with your actual Awan API key
AWAN_API_KEY = "3b38e8c8-5a6b-4e7e-a373-f85048d14675"  # Replace with your Awan API key
AWAN_API_URL = "https://api.awanllm.com/v1/completions"  # Awan API endpoint

def build_prompt(question, edu_type, subject, marks, class_level, semester, conversation_history=None):
    if edu_type == "School":
        level_detail = f"Class {class_level}"
    else:
        level_detail = f"Semester {semester}"
        
    marks_value = marks.split()[0] if marks else "5"
    
    prompt = (
        "You are an experienced teacher and exam preparation expert. "
        "Provide a clear, concise, and exam-oriented answer and include relevant source links at the end.\n\n"
    )
    
    if conversation_history:
        prompt += "Conversation history:\n"
        for line in conversation_history:
            prompt += line + "\n"
        prompt += "\n"
    
    prompt += (
        f"A student from {level_detail} studying {subject} has asked:\n"
        f"Question: {question}\n\n"
        f"Please provide an answer suitable for a {marks_value}-mark question. "
        "Ensure the answer is clear, well-structured, and includes a separate section for source links.\n"
        "Answer:"
    )
    return prompt

@app.route("/", methods=["GET", "POST"])
def index():
    if "conversation" not in session:
        session["conversation"] = []

    answer = None
    error = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        edu_type = request.form.get("edu_type", "")
        subject = request.form.get("subject", "").strip()
        marks = request.form.get("marks", "")
        class_level = request.form.get("class_level", "")
        semester = request.form.get("semester", "")
        
        if not question:
            error = "Please provide a question."
        elif not subject:
            error = "Please provide a subject."
        else:
            conversation_history = session.get("conversation", [])
            prompt = build_prompt(question, edu_type, subject, marks, class_level, semester, conversation_history)
            try:
                headers = {
                    "Authorization": f"Bearer {AWAN_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "Meta-Llama-3.1-70B-Instruct",  # Updated model name
                    "prompt": prompt,
                    "max_tokens": 500,  # Adjust based on your needs and free tier limits
                    "temperature": 0.7
                }
                response = requests.post(AWAN_API_URL, json=payload, headers=headers)
                response.raise_for_status()  # Raise an exception for bad status codes
                response_data = response.json()
                
                if response_data and "choices" in response_data and len(response_data["choices"]) > 0:
                    answer = response_data["choices"][0]["text"].strip()
                else:
                    answer = "Sorry, the AI was unable to generate an answer."
            except Exception as e:
                answer = f"Error: {str(e)}"
            
            session["conversation"].append(f"Q: {question}")
            session["conversation"].append(f"A: {answer}")
            session.modified = True

    return render_template("index.html", answer=answer, error=error, conversation=session.get("conversation"))

@app.route("/reset")
def reset():
    session.pop("conversation", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
