import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import Chat
from users.models import CustomUser

print("=== ALL USERS ===")
users = CustomUser.objects.all()
for user in users:
    print(f"User ID: {user.id}, Username: {user.username}")

print("\n=== ALL CHATS ===")
chats = Chat.objects.all()
print(f"Total chats in database: {chats.count()}")
for chat in chats:
    print(f"Chat ID: {chat.id}, User: {chat.user.username}, Title: {chat.title}, Messages: {chat.messages.count()}")
