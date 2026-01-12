from django.urls import path
from django.contrib.auth import views as auth_views   # ✅ ADD THIS LINE
from .views import login_page, signup_page, chat_page

urlpatterns = [
    path("", login_page, name="login"),
    path("signup/", signup_page, name="signup"),
    path("chat/", chat_page, name="chat"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
