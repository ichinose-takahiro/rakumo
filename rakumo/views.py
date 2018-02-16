from django.shortcuts import render, redirect
import sys, os
import datetime
from pytz import timezone
from rakumo.app.calendarGroupsList import Process as gProcess
from rakumo.app.calendarUserList import Process as uProcess
from rakumo.app.calendarGroupsMemberList import Process as gmProcess
from rakumo.app.calendarResourceList import Process as rProcess
from rakumo.app.calendarResourceUpdate import Process as ruProcess
from rakumo.app.calendarGroupsMemberInsert import Process as gmaProcess
from rakumo.app.calendarGroupsMemberDelete import Process as gmdProcess
from django import forms
from django.http import HttpResponse
from django.template import loader
UPLOADE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/upload/'
DOWNLOAD_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/'

import logging
import httplib2

from googleapiclient.discovery import build
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from rakumo.models import CredentialsModel
from mysite import settings
from oauth2client.contrib import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from rakumo.app.loginglibrary import init
# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
logging = init('test')

FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope='https://www.googleapis.com/auth/plus.me',
    redirect_uri='http://localhost:8000/oauth2callback')


@login_required
def index(request):
  storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
  credential = storage.get()
  if credential is None or credential.invalid == True:
    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)
    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)
  else:
    http = httplib2.Http()
    http = credential.authorize(http)
    service = build("plus", "v1", http=http)
    activities = service.activities()
    activitylist = activities.list(collection='public',
                                   userId='me').execute()
    logging.info(activitylist)

    return render(request, 'rakumo/welcome.html', {
                'activitylist': activitylist,
                })


@login_required
def auth_return(request):
  logging.debug(vars(request))
  if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET.get('state').encode('utf-8'),
                                 request.user):
    return  HttpResponseBadRequest()
  credential = FLOW.step2_exchange(request.GET.get('code').encode('utf-8'))
  logging.debug(credential)
  logging.debug(CredentialsModel)
  storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
  logging.debug(storage)
  storage.put(credential)
  return HttpResponseRedirect("/rakumo/")

@login_required
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
        logging.debug('postType group output start')
        gProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groups.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupsList_" + today + ".csv"
        logging.debug('postType group output end')
    elif postType == 'groupmem':
        logging.debug('postType groupmem output start')
        gmProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupMember.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupMemberList_" + today + ".csv"
        logging.debug('postType groupmem output end')
    elif postType == 'resource':
        logging.debug('postType resource output start')
        rProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'resource.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleResourceList_" + today + ".csv"
        logging.debug('postType resource output end')

    elif postType == 'user':
        logging.debug('postType user output start')
        uProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'user.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleUsersList_" + today + ".csv"
        logging.debug('postType user output end')

    elif postType == 'resourceUpdate':
        t = loader.get_template('rakumo/form.html')
        try:
            logging.debug('postType resource update start')
            path = upload(request)
            ruProcess(path)
            logging.debug('postType resource output end')
            #response = render(request, rform, {'info_message': '処理完了しました。ご確認ください'})
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            response = render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
    elif postType == 'groupmemAdd':
        t = loader.get_template('rakumo/form.html')
        try:
            logging.debug('postType groupmem add start')
            path = upload(request)
            gmaProcess(path)
            logging.debug('postType groupmem add end')
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
        logging.debug('postType resource output end')

    elif postType == 'groupmemTmp':
        logging.debug('postType resource output start')
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupmenberInsertTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=groupmenberInsertTmp.csv"
        logging.debug('postType resource output end')
    elif postType == 'groupmemDel':
        t = loader.get_template('rakumo/form.html')
        try:
            logging.debug('postType groupmem update start')
            path = upload(request)
            gmdProcess(path)
            logging.debug('postType groupmem update end')
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
    logging.debug(path)
    destination = open(path, 'wb')

    for chunk in file.chunks():
        destination.write(chunk)

    #insert_data = FileNameModel(file_name = file.name)
    #insert_data.save()

    return path

