import os
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework.decorators import api_view, permission_classes

from .models import Document, DocumentChatMapping
from .serializers import DocumentSerializer

from chat.models import Chat
from . import embeddings as doc_embeddings

# -------------------------
# TEXT EXTRACTION IMPORTS
# -------------------------
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import docx
except Exception:
    docx = None


# -------------------------
# FIXED TEXT EXTRACTION
# -------------------------
def extract_text_from_file(fpath):
    """
    Extract text from PDF, DOCX, or TXT files.
    SAFE: only fixes PDF extraction
    """
    ext = os.path.splitext(fpath)[1].lower()
    text = ""

    try:
        # PDF
        if ext == ".pdf" and pdfplumber:
            with pdfplumber.open(fpath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        # DOCX
        elif ext == ".docx" and docx:
            doc = docx.Document(fpath)
            for para in doc.paragraphs:
                text += para.text + "\n"

        # TXT / fallback
        else:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()

    except Exception as e:
        print("Error extracting text:", e)

    return text


# -------------------------
# UPLOAD DOCUMENT
# -------------------------
class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        if file_obj.size > 100 * 1024 * 1024:
            return Response({"detail": "File too large (max 100 MB)"}, status=status.HTTP_400_BAD_REQUEST)

        filename = file_obj.name
        allowed = [".pdf", ".txt", ".docx"]
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed:
            return Response({"detail": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file
        save_path = default_storage.save(
            f"documents/user_{request.user.id}/{filename}", file_obj
        )
        full_path = os.path.join(settings.MEDIA_ROOT, save_path)

        # Extract text
        extracted = extract_text_from_file(full_path)

        doc = Document.objects.create(
            user=request.user,
            file=save_path,
            title=filename,
            extracted_text=extracted
        )

        # Create chat
        chat = Chat.objects.create(user=request.user, title=filename)

        # Map chat ↔ document
        DocumentChatMapping.objects.create(chat_id=chat.id, document=doc)

        # Generate embeddings (SAFE CALL)
        # Generate embeddings
        try:
            doc_embeddings.upsert_document_embeddings(doc)
        except Exception as e:
            print("Embedding upsert failed:", e)
            import traceback
            traceback.print_exc()

        serializer = DocumentSerializer(doc, context={"request": request})
        return Response(
            {"document": serializer.data, "chat_id": chat.id},
            status=status.HTTP_201_CREATED
        )


# -------------------------
# LIST DOCUMENTS
# -------------------------
class ListDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        docs = Document.objects.filter(user=request.user).order_by("-uploaded_at")
        data = []

        for d in docs:
            mapping = DocumentChatMapping.objects.filter(document=d).first()
            data.append({
                "id": d.id,
                "title": d.title,
                "file": d.file.url if d.file else None,
                "uploaded_at": d.uploaded_at,
                "linked_chat_id": mapping.chat_id if mapping else None,
            })

        return Response(data)


# -------------------------
# DELETE DOCUMENT
# -------------------------
class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        DocumentChatMapping.objects.filter(document=doc).delete()

        try:
            doc.file.delete(save=False)
        except Exception:
            pass

        # Remove Chroma collection (SAFE)
        try:
            import chromadb
            client = chromadb.PersistentClient(
                path=os.path.join(settings.BASE_DIR, "chroma_db")
            )
            client.delete_collection(name=f"document_{doc.id}")
        except Exception as e:
            print("Chroma delete failed:", e)

        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# -------------------------
# TEST QUERY API
# -------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_document_query(request):
    document_id = request.data.get("document_id")
    question = request.data.get("question")

    if not document_id or not question:
        return Response(
            {"error": "document_id and question required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    results = doc_embeddings.query_document(
        document_id=int(document_id),
        query=question,
        top_k=5
    )

    return Response({
        "document_id": document_id,
        "question": question,
        "matches": results
    })
