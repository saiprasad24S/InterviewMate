from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('about-us/', views.about_us, name='about_us'),
]
