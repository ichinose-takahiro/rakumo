from django.shortcuts import render, redirect
#from django.template.context_processors import csrf
#from django.conf import settings
#from rakumo.models import FileNameModel
import sys, os
import datetime
#from django.template import Context, loader
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
    response = None
    rform = 'rakumo/form.html'
    postType = request.POST["postType"]
    try:
        path = upload(request)
    except KeyError as e:
        return render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
    request.FILES['file'] = None

    print('process_start')
    if postType == 'group':
        loging.debug('postType group output start')
        gProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groups.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupsList_" + today + ".csv"
        loging.debug('postType group output end')
    elif postType == 'groupmem':
        loging.debug('postType groupmem output start')
        gmProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupMember.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupMemberList_" + today + ".csv"
        loging.debug('postType groupmem output end')
    elif postType == 'resource':
        loging.debug('postType resource output start')
        rProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'resource.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleResourceList_" + today + ".csv"
        loging.debug('postType resource output end')

    elif postType == 'user':
        loging.debug('postType user output start')
        uProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'user.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleUsersList_" + today + ".csv"
        loging.debug('postType user output end')

    elif postType == 'resourceUpdate':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType resource update start')
            ruProcess(path)
            loging.debug('postType resource output end')
            #response = render(request, rform, {'info_message': '処理完了しました。ご確認ください'})
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            response = render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
    elif postType == 'groupmemAdd':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType groupmem add start')
            gmaProcess(path)
            loging.debug('postType groupmem add end')
            #response = render(request, rform, {'info_message': '処理完了しました。ご確認ください'})
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            response = render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
    elif postType == 'resourceTmp':
        response = HttpResponse(open(DOWNLOAD_DIR + 'resourceListTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=resourceListTmp.csv"
        loging.debug('postType resource output end')

    elif postType == 'groupmemTmp':
        loging.debug('postType resource output start')
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupmenberInsertTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=groupmenberInsertTmp.csv"
        loging.debug('postType resource output end')
    elif postType == 'groupmemDel':
        t = loader.get_template('rakumo/form.html')
        try:
            loging.debug('postType groupmem update start')
            gmdProcess(path)
            loging.debug('postType groupmem update end')
            #response = render(request, rform, {'info_message': '処理完了しました。ご確認ください'})
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            response =  render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})

    return response

    #insert_data = FileNameModel(file_name = file.name)
    #insert_data.save()

    #return redirect('rakumo:complete')
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
