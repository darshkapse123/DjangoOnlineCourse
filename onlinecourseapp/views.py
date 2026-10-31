from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Course, Question, Choice, Enrollment, Submission


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    return render(
        request,
        'onlinecourseapp/course_details_bootstrap.html',
        {'course': course}
    )


def extract_answers(request):
    selected_ids = []

    for key in request.POST:
        if key.startswith('choice_'):
            selected_ids.append(int(request.POST[key]))

    return selected_ids


@login_required
def submit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method != 'POST':
        return redirect('course_details', course_id=course.id)

    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'mode': 'honor'}
    )

    submission = Submission.objects.create(
        enrollment=enrollment
    )

    selected_ids = extract_answers(request)

    selected_choices = Choice.objects.filter(
        id__in=selected_ids,
        question__course=course
    )

    submission.choices.set(selected_choices)

    return redirect(
        'show_exam_result',
        course_id=course.id,
        submission_id=submission.id
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, id=course_id)

    submission = get_object_or_404(
        Submission,
        id=submission_id,
        enrollment__user=request.user,
        enrollment__course=course
    )

    questions = Question.objects.filter(course=course)

    total_grade_points = sum(
        question.grade for question in questions
    )

    grade = 0
    choices = submission.choices.all()

    for question in questions:
        selected_ids = choices.filter(
            question=question
        ).values_list('id', flat=True)

        if question.is_get_score(selected_ids):
            grade += question.grade

    percentage_score = (
        round((grade / total_grade_points) * 100, 2)
        if total_grade_points else 0
    )

    context = {
        'course': course,
        'submission': submission,
        'grade': grade,
        'total_grade_points': total_grade_points,
        'percentage_score': percentage_score,
        'choices': choices,
    }

    return render(
        request,
        'onlinecourseapp/exam_result.html',
        context
    )