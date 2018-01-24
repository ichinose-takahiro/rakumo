from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.conf import settings
from rakumo.models import FileNameModel
import sys, os
UPLOADE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/'

# Create your views here.
#from django.http import HttpResponse

#def index(request):
#    return HttpResponse("Hello, world. You're at the polls index.")

from django.http import HttpResponse
from django.template import loader

#from .models import Question

def index(request):
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template('rakumo/index.html')
    context = {
        'latest_question_list': '',
    }
    return HttpResponse(template.render(context, request))

def group(request):
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template('rakumo/group.html')
    context = {
        'latest_question_list': '',
    }
    return HttpResponse(template.render(context, request))


def form(request):
    if request.method != 'POST':
        return render(request, 'rakumo/form.html')

    file = request.FILES['file']
    path = os.path.join(UPLOADE_DIR, file.name)
    destination = open(path, 'wb')

    for chunk in file.chunks():
        destination.write(chunk)

    insert_data = FileNameModel(file_name = file.name)
    insert_data.save()

    return redirect('rakumo:complete')

def complete(request):
    return render(request, 'rakumo/complete.html')
