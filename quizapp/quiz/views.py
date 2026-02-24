from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Avg
import json

from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer


# ---------- AUTH ----------

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'signup':
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            email      = request.POST.get('email', '').strip().lower()
            password1  = request.POST.get('password1', '')
            password2  = request.POST.get('password2', '')

            if not all([first_name, last_name, email, password1, password2]):
                messages.error(request, 'All fields are required.')
            elif password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif len(password1) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            elif User.objects.filter(username=email).exists():
                messages.error(request, 'An account with this email already exists.')
            else:
                user = User.objects.create_user(
                    username=email, email=email,
                    password=password1,
                    first_name=first_name, last_name=last_name
                )
                login(request, user)
                return redirect('dashboard')

        elif action == 'login':
            email    = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'auth.html')


def logout_view(request):
    logout(request)
    return redirect('auth')


@login_required
def profile_view(request):
    if request.method == 'POST':
        u = request.user
        u.first_name = request.POST.get('first_name', u.first_name).strip()
        u.last_name  = request.POST.get('last_name',  u.last_name).strip()
        u.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'profile.html')


# ---------- DASHBOARD ----------

@login_required
def dashboard(request):
    quizzes  = Quiz.objects.filter(creator=request.user)
    attempts = QuizAttempt.objects.filter(user=request.user, is_completed=True).select_related('quiz')[:5]
    avg = QuizAttempt.objects.filter(quiz__creator=request.user, is_completed=True).aggregate(a=Avg('percentage'))['a'] or 0
    return render(request, 'dashboard.html', {
        'quizzes': quizzes[:6],
        'recent_attempts': attempts,
        'total_quizzes': quizzes.count(),
        'published': quizzes.filter(is_published=True).count(),
        'total_attempts': QuizAttempt.objects.filter(quiz__creator=request.user).count(),
        'avg_score': round(avg, 1),
    })


# ---------- QUIZ CRUD ----------

@login_required
def create_quiz(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Title is required.')
            return render(request, 'create_quiz.html')

        try:
            mins = int(request.POST.get('timer_minutes') or 0)
        except ValueError:
            mins = 0

        quiz = Quiz.objects.create(
            title=title,
            description=request.POST.get('description', '').strip(),
            creator=request.user,
            timer_minutes=max(0, mins),
            passcode=request.POST.get('passcode', '').strip(),
            is_published='is_published' in request.POST,
        )
        return redirect('add_questions', quiz_id=quiz.id)

    return render(request, 'create_quiz.html')


@login_required
def add_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        action = data.get('action')

        if action == 'add_question':
            text        = data.get('text', '').strip()
            marks       = int(data.get('marks') or 1)
            choices_raw = data.get('choices', [])

            if not text:
                return JsonResponse({'error': 'Question text is required.'}, status=400)

            filled = [c for c in choices_raw if str(c.get('text', '')).strip()]
            if len(filled) < 2:
                return JsonResponse({'error': 'Add at least 2 choices.'}, status=400)
            if not any(c.get('is_correct') for c in filled):
                return JsonResponse({'error': 'Mark at least one correct answer.'}, status=400)

            q = Question.objects.create(
                quiz=quiz,
                text=text,
                order=quiz.questions.count() + 1,
                marks=marks
            )
            for c in filled:
                Choice.objects.create(
                    question=q,
                    text=str(c['text']).strip(),
                    is_correct=bool(c.get('is_correct', False))
                )
            return JsonResponse({'success': True, 'question_id': q.id, 'count': quiz.questions.count()})

        if action == 'delete_question':
            qid = data.get('question_id')
            Question.objects.filter(id=qid, quiz=quiz).delete()
            for i, q in enumerate(quiz.questions.all(), 1):
                q.order = i; q.save()
            return JsonResponse({'success': True})

        return JsonResponse({'error': 'Unknown action'}, status=400)

    questions = quiz.questions.prefetch_related('choices').all()
    return render(request, 'add_questions.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_list(request):
    return render(request, 'quiz_list.html', {
        'quizzes': Quiz.objects.filter(creator=request.user)
    })


@login_required
def quiz_detail(request, quiz_id):
    quiz      = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    questions = quiz.questions.prefetch_related('choices').all()
    attempts  = quiz.attempts.filter(is_completed=True).select_related('user')
    return render(request, 'quiz_detail.html', {
        'quiz': quiz, 'questions': questions, 'attempts': attempts
    })


@login_required
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    if request.method == 'POST':
        quiz.title       = request.POST.get('title', quiz.title).strip()
        quiz.description = request.POST.get('description', '').strip()
        quiz.passcode    = request.POST.get('passcode', '').strip()
        quiz.is_published = 'is_published' in request.POST
        try:
            quiz.timer_minutes = max(0, int(request.POST.get('timer_minutes') or 0))
        except ValueError:
            pass
        quiz.save()
        messages.success(request, 'Quiz updated.')
        return redirect('quiz_detail', quiz_id=quiz.id)
    return render(request, 'edit_quiz.html', {'quiz': quiz})


@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted.')
    return redirect('quiz_list')


@login_required
def toggle_publish(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    quiz.is_published = not quiz.is_published
    quiz.save()
    messages.success(request, 'Quiz ' + ('published.' if quiz.is_published else 'unpublished.'))
    return redirect('quiz_detail', quiz_id=quiz.id)


# ---------- TAKE QUIZ ----------

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

    if quiz.passcode:
        sk = f'pc_{quiz_id}'
        if not request.session.get(sk):
            if request.method == 'POST' and request.POST.get('passcode_submit'):
                if request.POST.get('passcode', '') == quiz.passcode:
                    request.session[sk] = True
                else:
                    messages.error(request, 'Wrong passcode.')
                    return render(request, 'passcode.html', {'quiz': quiz})
            else:
                return render(request, 'passcode.html', {'quiz': quiz})

    questions = quiz.questions.prefetch_related('choices').all()
    if not questions.exists():
        messages.error(request, 'This quiz has no questions.')
        return redirect('dashboard')

    attempt = QuizAttempt.objects.create(
        quiz=quiz, user=request.user,
        total_marks=sum(q.marks for q in questions)
    )
    return render(request, 'take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'attempt': attempt,
        'timer_seconds': quiz.timer_minutes * 60,
    })


@login_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('dashboard')
    quiz    = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(QuizAttempt, id=request.POST.get('attempt_id'),
                                user=request.user, is_completed=False)
    score = 0
    for q in quiz.questions.prefetch_related('choices').all():
        cid = request.POST.get(f'q_{q.id}')
        if cid:
            try:
                choice = Choice.objects.get(id=cid, question=q)
                ok = choice.is_correct
                if ok: score += q.marks
                AttemptAnswer.objects.create(attempt=attempt, question=q,
                                             selected_choice=choice, is_correct=ok)
            except Choice.DoesNotExist:
                AttemptAnswer.objects.create(attempt=attempt, question=q, is_correct=False)
        else:
            AttemptAnswer.objects.create(attempt=attempt, question=q, is_correct=False)

    attempt.score = score
    attempt.percentage = (score / attempt.total_marks * 100) if attempt.total_marks else 0
    attempt.is_completed = True
    attempt.completed_at = timezone.now()
    attempt.time_taken_seconds = int(request.POST.get('time_taken', 0) or 0)
    attempt.save()
    return redirect('quiz_results', attempt_id=attempt.id)


@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.select_related('question', 'selected_choice') \
                             .prefetch_related('question__choices').all()
    return render(request, 'results.html', {'attempt': attempt, 'answers': answers})


@login_required
def join_quiz(request):
    if request.method == 'POST':
        qid = request.POST.get('quiz_id', '').strip()
        try:
            quiz = Quiz.objects.get(id=int(qid), is_published=True)
            return redirect('take_quiz', quiz_id=quiz.id)
        except (Quiz.DoesNotExist, ValueError):
            messages.error(request, 'Quiz not found.')
    return render(request, 'join_quiz.html')
