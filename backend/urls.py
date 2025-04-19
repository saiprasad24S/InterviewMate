from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('analyze-response/', views.analyze_response, name='analyze_response'),
    path('about-us/', views.about_us, name='about_us'),
    path('login/', views.login, name='login'),
    path("resume/", views.resume, name="resume"),
    path('stop-eye-tracking/', views.stop_eye_tracking, name='stop_eye_tracking'),  # Ensure this is included
]