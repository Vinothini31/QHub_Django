# Register CustomUser model for admin panel
from django.contrib import admin
from .models import CustomUser

admin.site.register(CustomUser)
