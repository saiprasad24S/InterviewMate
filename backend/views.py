import json
import os
import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import io
from pdfminer.high_level import extract_text
import google.generativeai as genai
import re

# Configure Generative AI
genai.configure(api_key="AIzaSyBZB86QbtDRpB3hkBkQcjsvpHJdMv03Viw")
model = genai.GenerativeModel("gemini-1.5-flash")

# Path to JSON file for storing user data
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# Load users from JSON
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return []
    with open(USER_DATA_FILE, 'r') as file:
        return json.load(file)

# Save users to JSON
def save_users(users):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)

# Hash password
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
    if request.method == 'POST':
        if 'resume' not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        resume_file = request.FILES['resume']
        if not resume_file.name.endswith('.pdf'):
            return JsonResponse({"error": "Unsupported file type. Please upload a PDF file."}, status=400)

        try:
            resume_data = resume_file.read()
            pdf_text = extract_text(io.BytesIO(resume_data))

            # Extract candidate's name
            name_prompt = f"Extract the candidate's full name from this resume text:\n\n{pdf_text}"
            response_name = model.generate_content(name_prompt)
            candidate_name = response_name.text.strip() if response_name.text else "Candidate Name"

            if candidate_name == "Candidate Name":
                return JsonResponse({"error": "Unable to extract candidate name"}, status=400)

            # Detect candidate's gender
            gender_prompt = f"Based on this resume, determine if the candidate is male or female. Respond only with 'male' or 'female':\n\n{pdf_text}"
            response_gender = model.generate_content(gender_prompt)
            candidate_gender = response_gender.text.strip().lower() if response_gender.text else "male"

            # Generate interview questions
            questions_prompt = f"Generate interview questions based on this resume (use a formal interview style, addressing the candidate properly). Only return questions:\n\n{pdf_text}"
            response_questions = model.generate_content(questions_prompt)

            lines = response_questions.text.splitlines()
            filtered_questions = [
                re.sub(r'^\s*[\d\.\)\-]*\s*', '', line)
                for line in lines
                if line.strip()
            ]

            if not filtered_questions:
                filtered_questions = ["Default Question 1"]

            return JsonResponse({
                "name": candidate_name,
                "gender": candidate_gender,  
                "questions": filtered_questions,
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def analyze_response(request):
    """
    Analyze the candidate's spoken response and provide interactive feedback.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question")
            answer = data.get("answer")

            if not question or not answer:
                return JsonResponse({"error": "Missing question or answer"}, status=400)

            # Check if the candidate is asking for a repeat
            clarification_keywords = [
                "repeat", "again", "say that again", "can you say that again",
                "can you repeat", "sorry, what was the question", "i didn't understand"
            ]
            if any(keyword in answer.lower() for keyword in clarification_keywords):
                return JsonResponse({
                    "message": f"Sure! Here’s the question again:\n{question}",
                    "next_question": question,
                    "repeat": True
                }, status=200)

            # Generate feedback for the response
            feedback_prompt = f"""
            Evaluate the following answer to the question '{question}'. 
            1. Provide constructive feedback on clarity, completeness, and professionalism.
            2. If the response is unclear or incomplete, suggest a follow-up question.
            3. If the response is good, acknowledge and move to the next question.
            Answer: {answer}
            """
            response_feedback = model.generate_content(feedback_prompt)

            feedback_text = response_feedback.text.strip() if response_feedback.text else "No feedback available."

            # Extract a follow-up question if needed
            followup_match = re.search(r'Follow-up question:\s*(.*)', feedback_text, re.IGNORECASE)
            followup_question = followup_match.group(1) if followup_match else None

            return JsonResponse({
                "message": feedback_text,
                "next_question": followup_question if followup_question else "Proceeding to the next question.",
                "repeat": False
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"Error analyzing response: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)










































# import json
# import os
# import hashlib
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import io
# from pdfminer.high_level import extract_text
# import google.generativeai as genai
# import re

# # Configure Generative AI
# genai.configure(api_key="AIzaSyBZB86QbtDRpB3hkBkQcjsvpHJdMv03Viw")
# model = genai.GenerativeModel("gemini-1.5-flash")

# # Path to JSON file for storing user data
# USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# # Load users from JSON
# def load_users():
#     if not os.path.exists(USER_DATA_FILE):
#         return []
#     with open(USER_DATA_FILE, 'r') as file:
#         return json.load(file)

# # Save users to JSON
# def save_users(users):
#     with open(USER_DATA_FILE, 'w') as file:
#         json.dump(users, file, indent=4)

# # Hash password
# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def index(request):
#     return render(request, 'index.html')

# def about_us(request):
#     return render(request, 'about-us.html')

# def resume(request):
#     return render(request, "resume.html")

# @csrf_exempt
# def login(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         users = load_users()
#         for user in users:
#             if user["email"] == email and user["password"] == hash_password(password):
#                 messages.success(request, "Login successful!")
#                 return redirect("resume")

#         messages.error(request, "Invalid credentials!")
    
#     return render(request, "login.html")

# @csrf_exempt
# def signup(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         users = load_users()
#         if any(user["email"] == email for user in users):
#             messages.error(request, "Email already exists!")
#             return redirect("signup")

#         users.append({"email": email, "password": hash_password(password)})
#         save_users(users)
#         messages.success(request, "Account created! Please log in.")
#         return redirect("login")

#     return render(request, "signup.html")

# @csrf_exempt
# def upload_resume(request):
#     if request.method == 'POST':
#         print("Files received:", request.FILES)
#         if 'resume' not in request.FILES:
#             return JsonResponse({"error": "No file part"}, status=400)

#         resume_file = request.FILES['resume']
#         print("Resume file:", resume_file)
#         if not resume_file.name:
#             return JsonResponse({"error": "No selected file"}, status=400)

#         try:
#             resume_data = resume_file.read()
#             print(f"Read {len(resume_data)} bytes from the file")

#             if resume_file.name.endswith('.pdf'):
#                 pdf_text = extract_text(io.BytesIO(resume_data))
#                 print(f"Extracted text: {pdf_text[:100]}...")
#             else:
#                 return JsonResponse({"error": "Unsupported file type. Please upload a PDF file."}, status=400)

#             # Extract candidate's name
#             name_extraction_prompt = f"Extract the candidate's full name from the following text:\n\n{pdf_text}"
#             response_name = model.generate_content(name_extraction_prompt)
#             candidate_name = response_name.text.strip() if response_name.text else "Candidate Name"

#             if candidate_name == "Candidate Name":
#                 return JsonResponse({"error": "Unable to extract candidate name from the provided resume"}, status=400)

#             # Detect candidate's gender
#             gender_detection_prompt = f"Based on the following resume text, determine if the candidate is male or female. Respond only with 'male' or 'female':\n\n{pdf_text}"
#             response_gender = model.generate_content(gender_detection_prompt)
#             candidate_gender = response_gender.text.strip().lower() if response_gender.text else "male"  # Default to male if detection fails

#             # Generate interview questions
#             questions_prompt = f"Based on the following resume, generate interview questions (like real interview format, first Hello Mr/Ms Candidate name and so on...) with candidate name that probe the candidate’s skills, experiences, and technical knowledge (only generate questions no other comments, should not mention like question 1, question 2.):\n\n{pdf_text}"
#             response_questions = model.generate_content(questions_prompt)

#             lines = response_questions.text.splitlines()
#             filtered_questions = [
#                 re.sub(r'^\s*[\d\.\)\-]*\s*', '', line)
#                 for line in lines
#                 if line.strip()
#             ]

#             if not filtered_questions:
#                 filtered_questions = ["Default Question 1"]

#             return JsonResponse({
#                 "name": candidate_name,
#                 "gender": candidate_gender,  
#                 "questions": filtered_questions,
#             }, status=200)

#         except Exception as e:
#             print(f"Error during processing: {str(e)}")
#             return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

#     return JsonResponse({"error": "Invalid request method"}, status=405)
