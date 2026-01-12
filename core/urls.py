from django.urls import path
from . import views

urlpatterns = [
    path('', views.ask_question, name='ask'),      # Ask page
    path('result/', views.show_result, name='result'),  # Result page
]
