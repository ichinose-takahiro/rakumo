from django.shortcuts import render

# Create your views here.
#from django.http import HttpResponse

#def index(request):
#    return HttpResponse("Hello, world. You're at the polls index.")

from django.http import HttpResponse
from django.template import loader

#from .models import Question

def index(request):
    #latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template('polls/index.html')
    context = {
        'latest_question_list': '',
    }
    return HttpResponse(template.render(context, request))
