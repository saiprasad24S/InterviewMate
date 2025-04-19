import json
import os
import hashlib
import subprocess
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import io
from pdfminer.high_level import extract_text
import google.generativeai as genai
import re
from dotenv import load_dotenv
import random

load_dotenv()
genai.configure(api_key=os.getenv('API_KEY'))
model = genai.GenerativeModel("gemini-1.5-flash")

USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
TESTS_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'tests.py')
process = None
clarification_count = 0
response_lengths = []

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return []
    with open(USER_DATA_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def index(request):
    return render(request, 'index.html')

def about_us(request):
    return render(request, 'about-us.html')

def resume(request):
    return render(request, "resume.html")

@csrf_exempt
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        users = load_users()
        for user in users:
            if user["email"] == email and user["password"] == hash_password(password):
                messages.success(request, "Login successful!")
                return redirect("resume")
        messages.error(request, "Invalid credentials!")
    return render(request, "login.html")

@csrf_exempt
def signup(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        users = load_users()
        if any(user["email"] == email for user in users):
            messages.error(request, "Email already exists!")
            return redirect("signup")
        users.append({"email": email, "password": hash_password(password)})
        save_users(users)
        messages.success(request, "Account created! Please log in.")
        return redirect("login")
    return render(request, "signup.html")

@csrf_exempt
def upload_resume(request):
    global process
    if request.method == 'POST':
        if 'resume' not in request.FILES:
            print("No file uploaded")
            return JsonResponse({"error": "No file uploaded"}, status=400)
        resume_file = request.FILES['resume']
        if not resume_file.name.endswith('.pdf'):
            print(f"Unsupported file type: {resume_file.name}")
            return JsonResponse({"error": "Unsupported file type. Please upload a PDF file."}, status=400)
        language = request.POST.get("language", "English").strip()
        try:
            print("Reading resume file")
            resume_data = resume_file.read()
            pdf_text = extract_text(io.BytesIO(resume_data))
            print("Extracted text:", pdf_text[:100])

            print("Extracting candidate name")
            name_prompt = f"Extract the candidate's full name from this resume text:\n\n{pdf_text}"
            response_name = model.generate_content(name_prompt)
            candidate_name = response_name.text.strip() if response_name.text else "Unknown Candidate"
            print("Candidate name:", candidate_name)

            print("Determining gender")
            gender_prompt = f"Based on this resume, determine if the candidate is male or female. Respond only with 'male' or 'female':\n\n{pdf_text}"
            response_gender = model.generate_content(gender_prompt)
            candidate_gender = response_gender.text.strip().lower() if response_gender.text else "male"
            print("Candidate gender:", candidate_gender)

            print("Generating questions in", language)
            questions_prompt = f"Generate interview questions based on this resume in {language} (use a formal interview style, addressing the candidate properly). Provide plain questions without numbers, bullets, asterisks, or any markers. Only return the questions:\n\n{pdf_text}"
            response_questions = model.generate_content(questions_prompt)
            lines = response_questions.text.splitlines()
            filtered_questions = [re.sub(r'^\s*[\d\.\)\-\*]*\s*', '', line).strip() for line in lines if line.strip()]
            if not filtered_questions:
                filtered_questions = [f"Default Question 1 in {language}"]
            print("Generated questions:", filtered_questions)

            if not process or process.poll() is not None:
                process = subprocess.Popen(['python', TESTS_SCRIPT_PATH])
                print(f"Started eye contact detection with PID: {process.pid}")

            print("Returning success response")
            return JsonResponse({
                "name": candidate_name,
                "gender": candidate_gender,
                "questions": filtered_questions,
                "language": language,
            }, status=200)
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)
    print("Invalid request method")
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def analyze_response(request):
    global clarification_count, response_lengths
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question")
            answer = data.get("answer")
            if not question or not answer:
                return JsonResponse({"error": "Missing question or answer"}, status=400)

            clarification_keywords = [
                "repeat", "again", "say that again", "can you say that again",
                "can you repeat", "sorry, what was the question", "i didn't understand"
            ]
            if any(keyword in answer.lower() for keyword in clarification_keywords):
                clarification_count += 1
                return JsonResponse({
                    "message": f"Sure! Here’s the question again:\n{question}",
                    "next_question": question,
                    "repeat": True
                }, status=200)

            response_lengths.append(len(answer.split()))

            feedback_prompt = f"""
            Evaluate the answer to the question '{question}' based on the following criteria:
            - Relevance: Does the answer directly address the question?
            - Clarity: Is the answer clear and easy to understand?
            - Structure: Is the answer well-organized with a logical flow?
            - Specificity: Does the answer provide specific details or examples?
            Provide a concise feedback paragraph (2-3 sentences) assessing these aspects.
            Answer: {answer}
            """
            response_feedback = model.generate_content(feedback_prompt)
            feedback_text = response_feedback.text.strip() if response_feedback.text else "No feedback available."

            return JsonResponse({
                "feedback": feedback_text,
                "next_question": "Proceeding to the next question.",
                "repeat": False
            }, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error analyzing response: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def stop_eye_tracking(request):
    global process, clarification_count, response_lengths
    if request.method == "POST":
        if process and process.poll() is not None:
            process.terminate()
            process.wait()
            print(f"Stopped eye contact detection with PID: {process.pid}")
            process = None
        
        # Read eye-tracking results for eye contact only
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        results_file = os.path.join(desktop_path, "eye_contact_results.txt")
        eye_contact_accuracy = 0
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    if "Accuracy" in line:
                        eye_contact_accuracy = float(line.split(":")[1].strip().replace("%", ""))
        except Exception as e:
            print(f"Error reading eye-tracking results: {str(e)}")

        # Generate random values for other attributes
        nervousness = random.randint(20, 80)
        confidence = random.randint(50, 90)
        fluency = random.randint(60, 95)
        intelligence = random.randint(55, 85)

        overall_score = (
            eye_contact_accuracy * 0.3 +
            nervousness * 0.2 +
            confidence * 0.2 +
            fluency * 0.15 +
            intelligence * 0.15
        )
        
        return JsonResponse({
            "message": "Eye tracking stopped",
            "overall_score": overall_score,
            "attributes": {
                "eye_contact": eye_contact_accuracy,
                "nervousness": nervousness,
                "confidence": confidence,
                "fluency": fluency,
                "intelligence": intelligence
            }
        }, status=200)
    return JsonResponse({"error": "Invalid request method"}, status=405)