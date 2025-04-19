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
@csrf_exempt
def analyze_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question")
            answer = data.get("answer")
            feedback_prompt = f"""
            Evaluate the answer to the question '{question}'.
            Provide:
            1. A concise feedback (one sentence) on clarity, completeness, and professionalism."""
            response_feedback = model.generate_content(feedback_prompt)
            feedback_text = response_feedback.text.strip() 
            lines = feedback_text.split('\n')
            feedback = lines[0] if lines else "No feedback available."
            improvement = lines[1] if len(lines) > 1 else "You can tell it like this: Please provide a more detailed and structured response."
            return JsonResponse({
                "feedback": feedback,
                "improvement": improvement,
                "next_question": "Proceeding to the next question.",
                "repeat": False
            }, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Error analyzing response: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)