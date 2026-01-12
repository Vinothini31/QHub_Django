import logging
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username", None)
        # Do not log password for security reasons
        logger.info(f"Login attempt for username: {username}")
        response = super().post(request, *args, **kwargs)
        if response.status_code == 401:
            logger.warning(f"Failed login for username: {username}")
            return Response({
                "detail": "Invalid username or password. Please check your credentials and try again.",
                "username": username,
                "error": "Authentication failed."
            }, status=status.HTTP_401_UNAUTHORIZED)
        logger.info(f"Successful login for username: {username}")
        return response
