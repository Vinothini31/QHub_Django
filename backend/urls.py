from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from users.custom_token_view import CustomTokenObtainPairView


def api_health(request):
    return JsonResponse({"message": "API is running!"})


urlpatterns = [

    # ================= FRONTEND =================
    path("", include("frontend.urls")),

    # ================= ADMIN ====================
    path("admin/", admin.site.urls),

    # ================= API HEALTH =================
    path("api/health/", api_health),

    # ================= USERS / AUTH =================
    path("api/", include("users.urls")),   # 🔥 THIS ENABLES /api/register/
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ================= OTHER APPS =================
    path("api/core/", include("core.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/documents/", include("documents.urls")),
]
