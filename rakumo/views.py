from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.conf import settings
from rakumo.models import FileNameModel
import sys, os
import datetime
from pytz import timezone
#sys.path.append('/var/www/html/mysite/rakumo/libs/')
#sys.path.append('/var/www/html/mysite/rakumo/')
from .calendarGroupsList import Process as gProcess
from .calendarUserList import Process as uProcess
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

    #file = request.FILES['file']
    today = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
    #path = os.path.join(UPLOADE_DIR, file.name + '_' + today)
    #destination = open(path, 'wb')

    #for chunk in file.chunks():
    #    destination.write(chunk)


    print('process_start')
    if request.POST["postType"] == 'groupmem':
        gProcess()
        response = HttpResponse(open('/var/www/html/mysite/rakumo/static/files/groups.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupsList" + today + ".csv"
    elif request.POST["postType"] == 'user':
        uProcess()
        response = HttpResponse(open('/var/www/html/mysite/rakumo/static/files/user.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleUsersList" + today + ".csv"

    return response
    #request = HttpResponse('/var/www/html/mysite/rakumo/static/files/groups.csv', content_type="text/csv")
    print('process_end')


    #insert_data = FileNameModel(file_name = file.name)
    #insert_data.save()

    #return redirect('rakumo:complete')
    #return HttpResponseRedirect('/complete/')
    #return HttpResponse(open('/var/www/html/mysite/rakumo/static/files/groups.csv','rb').read(), content_type="text/csv")
    #return render(request, 'rakumo/complete.html')

def complete(request):
    return render(request, 'rakumo/complete.html')
