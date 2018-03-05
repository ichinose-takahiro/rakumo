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
from rakumo.app.calendarAclList import Process as aclProcess
from rakumo.app.calendarAclAdd import Process as aclaProcess
from rakumo.app.calendarAclDelete import Process as acldProcess
from django import forms
from django.http import HttpResponse
from django.template import loader
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
from rakumo.app.loginglibrary import init,setId
import csv
# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
#logging = init('view1.py')
UPLOADE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/upload/'
DOWNLOAD_DIR = os.path.dirname(os.path.abspath(__file__)) + '/static/files/'
FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope=['https://www.googleapis.com/auth/plus.me','https://www.googleapis.com/auth/admin.directory.user'],
    redirect_uri='http://localhost:8000/oauth2callback')

@login_required
def index(request):
    logging = init('view1.py')
    # googleの設定でトップドメインが付与する必要があるが、サーバの都合上使わない・・。
    #storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
    #credential = storage.get()
    #if credential is None or credential.invalid == True:
    #  FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
    #                                                 request.user)
    #  authorize_url = FLOW.step1_get_authorize_url()
    #  return HttpResponseRedirect(authorize_url)
    #else:
    #  logging = None
    #  logging = setId(dict(credential.id_token)['sub'],str(vars(request.user)['_wrapped']),logging,'view1.py')
    #  logging.info(dict(credential.id_token)['sub'])
    #  http = httplib2.Http()
    #  http = credential.authorize(http)

    return render(request, 'rakumo/welcome.html', {
               'activitylist': '',
               })

@login_required
def auth_return(request):
  logging = init('view1.py')
  if not xsrfutil.validate_token(settings.SECRET_KEY, request.GET.get('state').encode('utf-8'),
                                 request.user):
    return  HttpResponseBadRequest()
  if request.GET.get('code') is None:
      return redirect('rakumo:form')
  credential = FLOW.step2_exchange(request.GET.get('code').encode('utf-8'))
 
  storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/rakumo/form")

@login_required
def form(request):
    logging = None
    storage = DjangoORMStorage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,request.user)
        authorize_url = FLOW.step1_get_authorize_url()
        return HttpResponseRedirect(authorize_url)

    logging = None
    userId = dict(credential.id_token)['sub']
    username = str(vars(request.user)['_wrapped'])
    logging = setId(userId,username,logging,'view1.py')
    logging.info('form_request')

    if request.method != 'POST':
        return render(request, 'rakumo/form.html')

    today = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")

    response = None
    rform = 'rakumo/form.html'
    postType = request.POST["postType"]

    print('process_start')
    if postType == 'group': # グループリストを取得
        logging.debug('postType group output start')
        logging = setId(userId,username,logging,'group')
        gProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groups.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupsList_" + today + ".csv"
        logging.debug('postType group output end')
    elif postType == 'groupmem': # グループ所属メンバーリストを取得
        logging.debug('postType groupmem output start')
        logging = setId(userId,username,logging,'groupmem')
        gmProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupMember.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleGroupMemberList_" + today + ".csv"
        logging.debug('postType groupmem output end')
    elif postType == 'resource': # 施設情報を取得
        logging.debug('postType resource output start')
        logging = setId(userId,username,logging,'resource')
        rProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'resource.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=googleResourceList_" + today + ".csv"
        logging.debug('postType resource output end')

    elif postType == 'user': # ユーザー情報を取得
        logging.debug('postType user output start')
        logging = setId(userId,username,logging,'user')
        uProcess()
        response = HttpResponse(open(DOWNLOAD_DIR + 'user.csv', 'rb').read(),
                            content_type="text/csv")
        response["Content-Disposition"] = "filename=googleUsersList_" + today + ".csv"
        logging.debug('postType user output end')

    elif postType == 'resourceUpdate': # 施設情報を更新
        try:
            logging.debug('postType resource update start')
            logging = setId(userId,username,logging,'resourceUpdate')
            path = upload(request)
            ruProcess(path)
            logging.debug('postType resource output end')
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
        except csv.Error as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': 'ファイルに問題があります。'})
    elif postType == 'groupmemAdd' or postType == 'groupmemDel': # グループ所属メンバーを追加、削除を行う
        try:
            path = upload(request)
            if postType == 'groupmemAdd':
                logging = setId(userId, username, logging, 'groupmemAdd')
                logging.info('postType groupmem add start')
                gmaProcess(path)
                logging.info('postType groupmem add end')
            else:
                logging = setId(userId, username, logging, 'groupmemDel')
                logging.info('postType groupmem del start')
                gmdProcess(path)
                logging.info('postType groupmem del end')
            response = redirect('rakumo:complete')
        except forms.ValidationError as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
        except csv.Error as e:
            logging.error(e.args[0])
            response = render(request, rform, {'error_message': 'ファイルに問題があります。'})
    elif postType == 'resourceTmp': # 施設情報の更新を行うテンプレートを取得
        response = HttpResponse(open(DOWNLOAD_DIR + 'resourceListTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=resourceListTmp.csv"
        logging.debug('postType resource output end')

    elif postType == 'groupmemTmp': # グループ所属メンバーの更新を行うテンプレートを取得
        logging.debug('postType resource output start')
        response = HttpResponse(open(DOWNLOAD_DIR + 'groupmenberInsertTmp.csv', 'rb').read(),
                                content_type="text/csv")
        response["Content-Disposition"] = "filename=groupmenberInsertTmp.csv"
        logging.debug('postType resource output end')
    elif postType == 'acl' or postType == 'aclAdd' or postType == 'aclDel': # カレンダーの権限を付与する
        try:
            logging = setId(userId,username,logging,'acl')
            path = upload(request)
            aclpath = ''
            if postType == 'acl':
                logging.debug('postType acllist start')
                aclProcess(path)
                aclpath = 'list_'
            elif postType == 'aclAdd':
                logging.debug('postType acladd start')
                aclaProcess(path)
                aclpath = 'add_'
            else:
                logging.debug('postType aclDel start')
                acldProcess(path)
                aclpath = 'del_'

            response = HttpResponse(open(DOWNLOAD_DIR + 'acl.csv', 'rb').read(),
                                    content_type="text/csv")
            response["Content-Disposition"] = "filename=googleAclList_" + aclpath + today + ".csv"
            logging.debug('postType acl output end')
        except forms.ValidationError as e:
            logging.error(e)
            response = render(request, rform, {'error_message': e.args[0]})
        except KeyError as e:
            logging.error(e)
            response =  render(request, rform, {'error_message': 'ファイルがアップロードされていないか、内容に問題があります。'})
        except csv.Error as e:
            logging.error(e)
            response = render(request, rform, {'error_message': 'ファイルに問題があります。'})

    return response

def complete(request):
    return render(request, 'rakumo/complete.html')

def upload(request):

    file = request.FILES['file']
    filename, ext = os.path.splitext(file.name)
    today = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
    path = os.path.join(UPLOADE_DIR, filename + '_' + today + ext)
    destination = open(path, 'wb')

    for chunk in file.chunks():
        destination.write(chunk)

    return path

@login_required
def readme(request):
    return request