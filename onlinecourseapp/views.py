
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Course, Question, Choice, Learner, Submission


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    return render(
        request,
        'onlinecourseapp/course_details_bootstrap.html',
        {'course': course}
    )


@login_required
def submit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method != 'POST':
        return redirect('course_details', course_id=course.id)

    learner, created = Learner.objects.get_or_create(
        user=request.user
    )

    questions = Question.objects.filter(course=course)

    score = 0
    total = 0
    exam_results = []

    for question in questions:
        total += question.grade

        selected_id = request.POST.get(
            f'question_{question.id}'
        )

        selected_choice = None

        if selected_id:
            selected_choice = Choice.objects.filter(
                id=selected_id,
                question=question
            ).first()

        if selected_choice:
            Submission.objects.create(
                learner=learner,
                question=question,
                choice=selected_choice
            )

        correct_choice = question.choices.filter(
            is_correct=True
        ).first()

        is_correct = (
            selected_choice is not None
            and selected_choice.is_correct
        )

        if is_correct:
            score += question.grade

        exam_results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': is_correct,
        })

    request.session['exam_result'] = {
        'course_name': course.name,
        'score': score,
        'total': total,
        'percentage': round(score / total * 100, 2) if total else 0,
        'results': [
            {
                'question': str(item['question']),
                'selected': str(item['selected_choice'])
                    if item['selected_choice'] else 'Not answered',
                'correct': str(item['correct_choice'])
                    if item['correct_choice'] else 'Not configured',
                'is_correct': item['is_correct'],
            }
            for item in exam_results
        ]
    }

    return redirect(
        'show_exam_result',
        course_id=course.id
    )


@login_required
def show_exam_result(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    result = request.session.get('exam_result')

    if not result:
        return redirect('course_details', course_id=course.id)

    return render(
        request,
        'onlinecourseapp/exam_result.html',
        {
            'course': course,
            'result': result,
        }
    )
