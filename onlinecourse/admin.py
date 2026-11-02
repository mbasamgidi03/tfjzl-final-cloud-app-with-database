<!DOCTYPE html>
<html lang="en">
<head>

     {% load static %}
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
<meta charset="UTF-8">
</head>
 
<body>
<!-- Navigation bar -->
<nav class="navbar navbar-light bg-light">
<div class="container-fluid">
<div class="navbar-header">
<a class="navbar-brand" href="{% url 'onlinecourse:index' %}">Home</a>
</div>
<ul class="nav navbar-nav navbar-right">

                {% if user.is_authenticated %}
<li>
<a class="btn btn-link" href="#">{{ user.first_name }}({{ user.username }})</a>
<a class="btn btn-link" href="{% url 'onlinecourse:logout' %}">Logout</a>
</li>

                {% else %}
<li>
<form class="form-inline" action="{% url 'onlinecourse:login' %}" method="post">

                        {% csrf_token %}
<div class="input-group">
<input type="text" class="form-control" placeholder="Username" name="username" >
<input type="password" class="form-control" placeholder="Username" name="psw" >
<button class="btn btn-primary" type="submit">Login</button>
<a class="btn btn-link" href="{% url 'onlinecourse:registration' %}">Sign Up</a>
</div>
</form>
</li>

                {% endif %}
</ul>
</div>
</nav>
 
    <!-- Page content -->
<div class="container-fluid">
<h2>{{ course.name }}</h2>
<div class="card-columns-vertical">

                {% for lesson in course.lesson_set.all %}
<div class="card mt-1">
<div class="card-header"><h5>Lesson {{lesson.order|add:1}}: {{lesson.title}}</h5></div>
<div class="card-body">{{lesson.content}}</div>
</div>

                {% endfor %}
</div>

            {% if user.is_authenticated %}
<br>
<button type="button" class="btn btn-primary btn-block" data-toggle="collapse" data-target="#exam">Start Exam</button>
<div id="exam" class="collapse">

                    {% url 'onlinecourse:submit' course.id as submit_url %}
<form id="questionform" action="{{ submit_url }}" method="POST">

                        {% csrf_token %}

                        {% for question in course.question_set.all %}
<div class="card mt-1">
<div class="card-header"><h5>{{ question.content }}</h5></div>
<div class="form-group">

                                    {% for choice in question.choice_set.all %}
<div class="form-check">
<label class="form-check-label">
<input type="checkbox" name="choice_{{ choice.id }}"

                                                       class="form-check-input" id="{{ choice.id }}"

                                                       value="{{ choice.id }}">{{ choice.content }}
</label>
</div>

                                    {% endfor %}
</div>
</div>

                        {% endfor %}

                        {% if submit_url %}
<input class="btn btn-success btn-block" type="submit" value="Submit">

                        {% else %}
<button class="btn btn-success btn-block" type="button" disabled>Submit</button>

                        {% endif %}
</form>
</div>

            {% endif %}
</div>
</body>
</html>
 
from django.http import HttpResponseRedirect

from .models import Choice, Course, Enrollment, Question, Submission

from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse

from django.views import generic

from django.views.decorators.http import require_POST

from django.contrib.auth import login, logout, authenticate

import logging

# Get an instance of a logger

logger = logging.getLogger(__name__)

# Create your views here.
 
 
def registration_request(request):

    context = {}

    if request.method == 'GET':

        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

    elif request.method == 'POST':

        # Check if user exists

        username = request.POST['username']

        password = request.POST['psw']

        first_name = request.POST['firstname']

        last_name = request.POST['lastname']

        user_exist = False

        try:

            User.objects.get(username=username)

            user_exist = True

        except:

            logger.error("New user")

        if not user_exist:

            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,

                                            password=password)

            login(request, user)

            return redirect("onlinecourse:index")

        else:

            context['message'] = "User already exists."

            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
 
 
def login_request(request):

    context = {}

    if request.method == "POST":

        username = request.POST['username']

        password = request.POST['psw']

        user = authenticate(username=username, password=password)

        if user is not None:

            login(request, user)

            return redirect('onlinecourse:index')

        else:

            context['message'] = "Invalid username or password."

            return render(request, 'onlinecourse/user_login_bootstrap.html', context)

    else:

        return render(request, 'onlinecourse/user_login_bootstrap.html', context)
 
 
def logout_request(request):

    logout(request)

    return redirect('onlinecourse:index')
 
 
def check_if_enrolled(user, course):

    is_enrolled = False

    if user.id is not None:

        # Check if user enrolled

        num_results = Enrollment.objects.filter(user=user, course=course).count()

        if num_results > 0:

            is_enrolled = True

    return is_enrolled
 
 
# CourseListView

class CourseListView(generic.ListView):

    template_name = 'onlinecourse/course_list_bootstrap.html'

    context_object_name = 'course_list'
 
    def get_queryset(self):

        user = self.request.user

        courses = Course.objects.order_by('-total_enrollment')[:10]

        for course in courses:

            if user.is_authenticated:

                course.is_enrolled = check_if_enrolled(user, course)

        return courses
 
 
class CourseDetailView(generic.DetailView):

    model = Course

    template_name = 'onlinecourse/course_detail_bootstrap.html'
 
 
def enroll(request, course_id):

    course = get_object_or_404(Course, pk=course_id)

    user = request.user
 
    is_enrolled = check_if_enrolled(user, course)

    if not is_enrolled and user.is_authenticated:

        # Create an enrollment

        Enrollment.objects.create(user=user, course=course, mode='honor')

        course.total_enrollment += 1

        course.save()
 
    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))
 
 
def extract_answers(request):

    submitted_answers = []

    for key in request.POST:

        if key.startswith('choice_'):

            for value in request.POST.getlist(key):

                try:

                    submitted_answers.append(int(value))

                except (TypeError, ValueError):

                    continue

    return submitted_answers
 
 
def submit(request, course_id):

    if not request.user.is_authenticated:

        return redirect('onlinecourse:login')
 
    course = get_object_or_404(Course, pk=course_id)

    enrollment = get_object_or_404(

        Enrollment,

        user=request.user,

        course=course,

    )

    submission = Submission.objects.create(enrollment=enrollment)

    choices = Choice.objects.filter(

        id__in=extract_answers(request),

        question__course=course,

    )

    submission.choices.set(choices)
 
    return HttpResponseRedirect(reverse(

        'onlinecourse:exam_result',

        args=(course.id, submission.id),

    ))
 
 
def show_exam_result(request, course_id, submission_id):

    if not request.user.is_authenticated:

        return redirect('onlinecourse:login')
 
    course = get_object_or_404(Course, pk=course_id)

    submission = get_object_or_404(

        Submission,

        pk=submission_id,

        enrollment__course=course,

        enrollment__user=request.user,

    )

    choices = list(submission.choices.select_related('question'))

    questions = list(course.question_set.prefetch_related('choice_set'))

    total_score = 0

    question_results = []
 
    for question in questions:

        correct_choices = [

            choice for choice in question.choice_set.all()

            if choice.is_correct

        ]

        selected_choices = [

            choice for choice in choices

            if choice.question_id == question.id

        ]

        is_correct = bool(correct_choices) and set(correct_choices) == set(selected_choices)

        earned_grade = question.grade if is_correct else 0

        total_score += earned_grade

        question_results.append({

            'question': question,

            'selected_choices': selected_choices,

            'correct_choices': correct_choices,

            'is_correct': is_correct,

            'earned_grade': earned_grade,

        })
 
    context = {

        'course': course,

        'grade': total_score,

        'total_possible': sum(question.grade for question in questions),

        'choices': choices,

        'question_results': question_results,

    }

    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
 
