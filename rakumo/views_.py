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
from rakumo.app.calendarGroupsList import Process as gProcess
from rakumo.app.calendarUserList import Process as uProcess
from rakumo.app.calendarGroupsMemberList import Process as gmProcess
from rakumo.app.calendarResourceList import Process as rProcess
from rakumo.app.calendarResourceUpdate import Process as ruProcess
from rakumo.app.calendarGroupsMemberInsert import Process as gmaProcess
from rakumo.app.calendarGroupsMemberDelete import Process as gmdProcess
from rakumo.app.loginglibrary import init
from django import forms
UPLOADE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/upload/'
DOWNLOAD_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/'

#from apiclient.discovery import build
#from httplib2 import Http
#from oauth2client import file, client, tools
#from oauth2client.file import Storage
#import argparse
#import os

#SCOPES = 'https://www.googleapis.com/auth/plus.me'
#CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret.json'
#APPLICATION_NAME = 'Directory API Python Quickstart'

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

#    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    #except ImportError:
    #    flags = None
#    home_dir = os.path.expanduser('~')
#    credential_dir = os.path.join(home_dir, '.credentials')
#    if not os.path.exists(credential_dir):
#        os.makedirs(credential_dir)
#    credential_path = os.path.join(credential_dir,
#                                   'python-quickstart.json')
#    store = Storage(credential_path)
#    creds = store.get()
#    if not creds or creds.invalid:
#        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
#        creds = tools.run_flow(flow, store, flags) \
#              if flags else tools.run(flow, store)
#    service = build('plus', 'v2', http=creds.authorize(Http()))
#    activities = service.activities()
#    activitylist = activities.list(collection='public',
#                                   userId='me').execute()
    
#    logging.info(activitylist)

#    # return render(request, 'plus/welcome.html', {
#    #             'activitylist': activitylist,
#    #             })
#    template = loader.get_template('rakumo/form.html')
#    context = {
#      'activitylist': activitylist,
#    }
 #   return HttpResponse(template.render(context, request))



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
            path = upload(request)
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
            path = upload(request)
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
            path = upload(request)
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
