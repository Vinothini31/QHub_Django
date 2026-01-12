from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    return f"documents/user_{instance.user.id}/{filename}"


class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=document_upload_path)
    title = models.CharField(max_length=255, blank=True)
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name


class DocumentChatMapping(models.Model):
    """Map a chat (from chat.Chat) to a Document so the chat can use doc context."""
    from django.conf import settings as _s
    chat_id = models.IntegerField()  # store chat id to avoid circular import
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="mappings")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.chat_id} -> Doc {self.document.id}"
