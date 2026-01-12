from django.shortcuts import render

def login_page(request):
    return render(request, "frontend/login.html")

def signup_page(request):
    return render(request, "frontend/signup.html")

def chat_page(request):
    return render(request, "frontend/chat.html")
