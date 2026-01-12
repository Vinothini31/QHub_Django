from dotenv import load_dotenv
load_dotenv()

import os
import json
import traceback
import google.generativeai as genai

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 🔽 RAG imports
from documents.models import DocumentChatMapping
from documents import embeddings as doc_embeddings


@csrf_exempt
def gemini_chat(request):
    """
    Endpoint for Gemini AI chat with optional document-based RAG
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body or "{}")
        user_message = data.get("message", "").strip()
        chat_id = data.get("chat_id")

        # -------------------- VALIDATION --------------------
        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)
        if not chat_id:
            return JsonResponse({"error": "chat_id missing"}, status=400)

        # -------------------- GEMINI CONFIG --------------------
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return JsonResponse({"error": "Gemini API key missing"}, status=500)

        genai.configure(api_key=gemini_api_key)

        print("USER MESSAGE:", user_message)
        print("CHAT ID RECEIVED:", chat_id)

        # -------------------- RAG / DOCUMENT CONTEXT --------------------
        rag_context = ""
        try:
            mapping = (
                DocumentChatMapping.objects
                .filter(chat_id=chat_id)
                .select_related("document")
                .first()
            )

            if mapping and mapping.document:
                print("📄 USING DOCUMENT ID:", mapping.document.id)
                try:
                    results = doc_embeddings.query_document(
                        document_id=mapping.document.id,
                        query=user_message,
                        top_k=4
                    )
                    if results:
                        rag_context = "\n".join(
                            [f"- {r.get('text', '').strip()}" for r in results if r.get("text")]
                        )
                        print("📄 RAG CONTEXT FOUND")
                    else:
                        print("ℹ️ No RAG results found, fallback to normal AI chat")
                except Exception as e:
                    print("⚠️ RAG retrieval failed:", e)
                    print("ℹ️ Falling back to normal AI chat")

        except Exception as e:
            print("⚠️ Document mapping error:", e)
            rag_context = ""

        # -------------------- PROMPT BUILD --------------------
        if rag_context:
            final_prompt = f"""
You are a strict document-based assistant.

DOCUMENT CONTENT:
{rag_context}

USER QUESTION:
{user_message}

RULES:
- Answer ONLY using the document content above.
- Do NOT assume or guess.
- If the answer is NOT found, reply exactly:
"The information is not available in the document."
"""
            system_instruction = "You are a document-only assistant. Never answer outside the document content."
        else:
            final_prompt = user_message
            system_instruction = "You are a helpful, friendly AI assistant. Answer naturally and clearly."

        # -------------------- GEMINI CALL --------------------
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-lite",
                system_instruction=system_instruction
            )
            response = model.generate_content(final_prompt)
            reply_text = response.text.strip() if response.text else "The information is not available in the document."

        except Exception as e:
            print("❌ GEMINI ERROR:", str(e))
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

        print("AI REPLY:", reply_text)
        return JsonResponse({"reply": reply_text})

    except Exception as e:
        print("❌ SERVER ERROR:", str(e))
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
