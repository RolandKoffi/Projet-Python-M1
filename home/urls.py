from unicodedata import name
from django.contrib import admin
from django.urls import path
from home import views
from authentification.views import login_view

urlpatterns = [
    
     path("", views.index, name="index"),
     path("camera", views.activer_camera, name="camera"),
     path("liste", views.liste_dormeurs, name="liste"),
     path("session", views.session, name="session")
]