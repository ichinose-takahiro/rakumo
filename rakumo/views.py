from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.conf import settings
from rakumo.models import FileNameModel
import sys, os
import datetime
from django.template import Context, loader
from pytz import timezone
#sys.path.append('/var/www/html/mysite/rakumo/libs/')
#sys.path.append('/var/www/html/mysite/rakumo/')
from .calendarGroupsList import Process as gProcess
from .calendarUserList import Process as uProcess
from .calendarGroupsMemberList import Process as gmProcess
from .calendarResourceList import Process as rProcess
from .calendarResourceUpdate import Process as ruProcess
from .calendarGroupsMemberInsert import Process as gmaProcess
from .calendarGroupsMemberDelete import Process as gmdProcess
from .loginglibrary import init
from django import forms
UPLOADE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/upload/'
DOWNLOAD_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/'

# Create your views here.
#from django.http import HttpResponse

#def index(request):
#    return HttpResponse("Hello, world. You're at the polls index.")

from django.http import HttpResponse
from django.template import loader

#from .models import Question
loging = init()

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
    if request.POST["postType"] == 'group':
        loging.debug('postType group output start')
        gProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groups.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupsList_" + today + ".csv"
        loging.debug('postType group output end')
    elif request.POST["postType"] == 'groupmem':
        loging.debug('postType groupmem output start')
        gmProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupMember.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupMemberList_" + today + ".csv"
        loging.debug('postType groupmem output end')
    elif request.POST["postType"] == 'resource':
        loging.debug('postType resource output start')
        rProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'resource.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleResourceList_" + today + ".csv"
        loging.debug('postType resource output end')

    elif request.POST["postType"] == 'user':
        loging.debug('postType user output start')
        uProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'user.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleUsersList_" + today + ".csv"
        loging.debug('postType user output end')

    elif request.POST["postType"] == 'resourceUpdate':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType resource update start')
            path = upload(request)
            ruProcess(path)
            loging.debug('postType resource output end')
            c = {'info_message': '処理完了しました。ご確認ください',}
        except forms.ValidationError as e:
            c = {'error_message': e.args[0],}
        except KeyError as e:
            c = {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。',}
        response = HttpResponse(t.render(c, request))
    elif request.POST["postType"] == 'groupmemAdd':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType groupmem add start')
            path = upload(request)
            gmaProcess(path)
            loging.debug('postType groupmem add end')
            c = {'info_message': '処理完了しました。ご確認ください',}
        except forms.ValidationError as e:
            c = {'error_message': e.args[0],}
        except KeyError as e:
            c = {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。',}

        response = HttpResponse(t.render(c, request))
    elif request.POST["postType"] == 'resourceTmp':
        response = HttpResponse(open(DOWNLOAD_DIR + 'resourceListTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=resourceListTmp.csv"
        loging.debug('postType resource output end')

    elif request.POST["postType"] == 'groupmemTmp':
        loging.debug('postType resource output start')
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupmenberInsertTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=groupmenberInsertTmp.csv"
        loging.debug('postType resource output end')
    elif request.POST["postType"] == 'groupmemDel':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType groupmem update start')
            path = upload(request)
            gmdProcess(path)
            loging.debug('postType groupmem update end')
            c = {'info_message': '処理完了しました。ご確認ください',}
        except forms.ValidationError as e:
             c = {'error_message': e.args[0],}
        except KeyError as e:
            c = {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。',}
        response = HttpResponse(t.render(c, request))

    return response
    #request = HttpResponse('/var/www/html/mysite/rakumo/static/files/groups.csv', content_type="text/csv")


    #insert_data = FileNameModel(file_name = file.name)
    #insert_data.save()

    #return redirect('rakumo:complete')
    #return HttpResponseRedirect('/complete/')
    #return HttpResponse(open('/var/www/html/mysite/rakumo/static/files/groups.csv','rb').read(), content_type="text/csv")
    #return render(request, 'rakumo/complete.html')

def complete(request):
    return render(request, 'rakumo/complete.html')

def upload(request):

    file = request.FILES['file']
    filename, ext = os.path.splitext(file.name)
    today = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
    path = os.path.join(UPLOADE_DIR, filename + '_' + today + ext)
    loging.debug(path)
    destination = open(path, 'wb')

    for chunk in file.chunks():
        destination.write(chunk)

    #insert_data = FileNameModel(file_name = file.name)
    #insert_data.save()

    return path
