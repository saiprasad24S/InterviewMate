from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import io
from pdfminer.high_level import extract_text
import google.generativeai as genai
import re

# Configure Generative AI
genai.configure(api_key="AIzaSyBZB86QbtDRpB3hkBkQcjsvpHJdMv03Viw")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

def index(request):
    return render(request, 'index.html')

def about_us(request):
    return render(request, 'about-us.html')

@csrf_exempt
def upload_resume(request):
    if request.method == 'POST':
        if 'resume' not in request.FILES:
            return JsonResponse({"error": "No file part"}, status=400)

        resume_file = request.FILES['resume']
        if not resume_file.name:
            return JsonResponse({"error": "No selected file"}, status=400)

        try:
            resume_data = resume_file.read()
            print(f"Read {len(resume_data)} bytes from the file")

            # Check if the uploaded file is a PDF
            if resume_file.name.endswith('.pdf'):
                pdf_text = extract_text(io.BytesIO(resume_data))
                print(f"Extracted text: {pdf_text[:100]}...")
            else:
                return JsonResponse({"error": "Unsupported file type"}, status=400)

            # Generate prompt for AI to extract the name
            name_extraction_prompt = f"Extract the candidate's full name from the following text:\n\n{pdf_text}"
            response_name = model.generate_content(name_extraction_prompt)
            candidate_name = response_name.text.strip() if response_name.text else "Candidate Name"

            if candidate_name == "Candidate Name":
                return JsonResponse({"error": "Unable to extract candidate name from the provided resume"}, status=400)

            # Generate personalized interview questions based on extracted resume content
            questions_prompt = f"Based on the following resume, generate interview questions (like real interview format, first Hello Mr/Ms Candidate name and so on...) with candidate name that probe the candidate’s skills, experiences, and technical knowledge (only generate questions no other comments, should not mention like question 1, question 2.):\n\n{pdf_text}"
            response_questions = model.generate_content(questions_prompt)

            # Split the response into lines and filter out unwanted prefixes
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
                "questions": filtered_questions,
            }, status=200)

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)







































# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import io
# from pdfminer.high_level import extract_text
# import google.generativeai as genai
# import re  # Optional, in case manual regex extraction is required

# # Configure Generative AI
# genai.configure(api_key="AIzaSyBZB86QbtDRpB3hkBkQcjsvpHJdMv03Viw")  # Replace with your actual API key
# model = genai.GenerativeModel("gemini-1.5-flash")

# def index(request):
#     return render(request, 'index.html')

# def about_us(request):
#     return render(request, 'about-us.html')

# @csrf_exempt
# def upload_resume(request):
#     if request.method == 'POST':
#         if 'resume' not in request.FILES:
#             return JsonResponse({"error": "No file part"}, status=400)

#         resume_file = request.FILES['resume']
#         if not resume_file.name:
#             return JsonResponse({"error": "No selected file"}, status=400)

#         try:
#             resume_data = resume_file.read()
#             print(f"Read {len(resume_data)} bytes from the file")

#             # Check if the uploaded file is a PDF
#             if resume_file.name.endswith('.pdf'):
#                 pdf_text = extract_text(io.BytesIO(resume_data))
#                 print(f"Extracted text: {pdf_text[:100]}...")  # Display the first 100 characters
#             else:
#                 return JsonResponse({"error": "Unsupported file type"}, status=400)

#             # Generate prompt for AI to extract the name
#             name_extraction_prompt = f"Extract the candidate's full name from the following text:\n\n{pdf_text}"
#             response_name = model.generate_content(name_extraction_prompt)
#             candidate_name = response_name.text.strip() if response_name.text else "Candidate Name"

#             if candidate_name == "Candidate Name":
#                 return JsonResponse({"error": "Unable to extract candidate name from the provided resume"}, status=400)

#             # Generate personalized interview questions based on extracted resume content
#             questions_prompt = f"Based on the following resume, generate interview questions (like real interview format, first Hello Mr/Ms Candidate name and so on...) with candidate name that probe the candidate’s skills, experiences, and technical knowledge (only generate questions no other comments, should not mention like question 1, question 2.):\n\n{pdf_text}"
#             response_questions = model.generate_content(questions_prompt)

#             # Split the response into lines and filter out unwanted prefixes
#             lines = response_questions.text.splitlines()
#             filtered_questions = [
#                 re.sub(r'^\s*[\d\.\)\-]*\s*', '', line)  # Remove numbering, bullets, and extra spaces
#                 for line in lines
#                 if line.strip()  # Skip empty lines
#             ]

#             if not filtered_questions:
#                 filtered_questions = ["Default Question 1"]

#             return JsonResponse({
#                 "name": candidate_name,
#                 "questions": filtered_questions,
#             }, status=200)

#         except Exception as e:
#             print(f"Error during processing: {str(e)}")
#             return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)

#     return JsonResponse({"error": "Invalid request method"}, status=405)
