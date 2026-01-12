from django.shortcuts import render
# Import your existing RAG function here
from .utils import answer_question  # adjust import if needed

def ask_question(request):
    return render(request, 'frontend/ask.html')


def show_result(request):
    if request.method == "POST":
        question = request.POST.get('question')

        # Call your existing RAG backend function
        answer = answer_question(question)  # <-- do not change this function

        return render(request, 'frontend/result.html', {
            'question': question,
            'answer': answer
        })
    else:
        return render(request, 'frontend/ask.html')
