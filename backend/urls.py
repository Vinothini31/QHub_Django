from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Simple API check (used only for /api/)
def home(request):
    return JsonResponse({"message": "API is running!"})

urlpatterns = [

    # ================= FRONTEND =================
    # This will load your HTML page
    path("", include("frontend.urls")),

    # ================= ADMIN ====================
    path("admin/", admin.site.urls),

    # ================= API ROOT =================
    # Optional API check
    path("api/", home),

    # ================= AUTH =====================
    path("api/users/", include("users.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ================= CORE / CHAT / DOCS =======
    path("api/", include("core.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/documents/", include("documents.urls")),
]
