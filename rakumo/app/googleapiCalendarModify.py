# -*- coding: utf-8 -*-

u""" カレンダーのデータを追加するやつや
 google calendar apiの利用についてhttps://developers.google.com/google-apps/calendar/v3/reference/events/insert?hl=ja
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.file import Storage
import csv
import json
import sys
import datetime
import ast
import os
from loginglibrary import init
from apiclient.http import BatchHttpRequest
from numba import jit
import argparse
import random
import time
from apiclient.errors import HttpError

logging = init('calendar')
batchcount = 0
batch = None
priEmail = ''

"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
#CALENDARCSV = WORKDIR + 'calendarList.csv'
DELETESTRING = 'https://www.google.com/calendar/event?eid='
CLIENT_SECRET_FILE = './json/client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
okcnt = 0
ngcnt = 0

CALENDARCSVS = [
#'calendarList_20180513092400_api.csv'
#'deletedata_20180513_prd.csv'
#'testmodify.csv'
'calendarList_20180513095252_2.csv'
]
@jit
def getCalendarData(calendacsv):
    u"""getmemberData メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(calendacsv)
    logging.debug(len(calendarData))
    eventidList = []
    cnnt = 0
    for data in calendarData:
        cnnt = cnnt + 1
        logging.debug('get:'+ str(cnnt))
        data = json.loads(data, encoding='UTF-8')
        if data['status'] != 'cancelled':
            organizer = ast.literal_eval(data['organizer'])
            if 'email' in organizer:
                if {'id':data['id'],'organizer':organizer['email']} not in eventidList:
                    eventidList.append({'id':data['id'],'organizer':organizer['email']})
            #if data['attendees'] != '':
            #    attendees = ast.literal_eval(data['attendees'])
            #    for attendee in attendees:
            #        if attendee['responseStatus'] == 'accepted' and organizer['email'] != attendee['email']:
            #            eventidList.append({'id':data['id'],'organizer':attendee['email']})


    return eventidList

def csvToJson(csvData):
    u""" csvToJson CSVを読み込みJSON化する
    CSVファイルを読み込みJSONデータにして返します
    :param csvData: CSVファイルのフルパス
    :return: JSONデータ
    """
    jsonData = []
    with open(csvData, 'r',encoding='utf-8', errors='ignore', newline='') as f:
        for line in csv.DictReader(f):
            line_json = json.dumps(line, ensure_ascii=False)
            jsonData.append(line_json)
    return jsonData

@jit
def progress(p, l):
    if l > 1:
        sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    else:
        sys.stdout.write("\r%d / 100" %(int(p * 100 / (1))))
    sys.stdout.flush()

def bachExecute(EVENT, service,calendarId, http, lastFlg = None):
    global batchcount
    global batch
    global okcnt
    global ngcnt
#    okcnt = 0
#    ngcnt = 0
    rtnFlg = False
    
    #modevent = {}
    #modevent['guestsCanModify'] = True
   
    if batch is None:
        batch = service.new_batch_http_request(callback=delete_calendar)
    logging.debug('-----batchpara-------')
    if batchcount < 50 and lastFlg != 'change':
        logging.debug(EVENT['id'])
        modevent = service.events().get(calendarId=calendarId,eventId=EVENT['id']).execute()
        modevent['guestsCanModify'] = True
        batch.add(service.events().update(calendarId=calendarId,eventId=EVENT['id'], body=modevent))
        #batch.add(service.events().update(calendarId,EVENT['id'], modevent))
        batchcount = batchcount + 1
        logging.debug(str(batchcount))

    if batchcount >= 50 or lastFlg == True or lastFlg == 'change':
        logging.debug('batchexecute-------before---------------------')

        for n in range(0, 10):  # 指数バックオフ(遅延処理対応)

            try:
                batch.execute(http=http)
                rtnFlg = True
                break
            except HttpError as error:
                errcontent = json.loads(vars(error)['content'],encoding='UTF-8')['error']
                if errcontent['errors'][0]['reason'] in ['userRateLimitExceeded', 'quotaExceeded', 'internalServerError', 'backendError']:
                    logging.debug('exponential backoff:' + str(n+1) + '回目:' + errcontent['errors'][0]['reason'])
                    time.sleep((2 ** n) + random.random())
                else:
                    logging.debug('else error')
                    raise error

        if rtnFlg != True:
            raise Exception("There has been an error, the request never succeeded.")

        batch = service.new_batch_http_request(callback=delete_calendar)
        logging.debug('batchexecute-------after---------------------')
        batchcount = 0


    return okcnt, ngcnt

def delete_calendar(request_id, response, exception):
    global writeObj
    global okcnt
    global ngcnt
    if exception is None:
        logging.debug('callback----OK-------')
        logging.debug('request_id:'+str(request_id) )
        okcnt = okcnt + 1
        pass
    else:
        exc_content = json.loads(vars(exception)['content'],encoding='UTF-8')['error']
        if str(exc_content['code']) == '410':
            logging.debug('callback----OK-------')
            logging.debug('request_id:'+str(request_id) + ' reason:changed' )
            ngcnt = ngcnt + 1
            pass
        elif str(exc_content['code']) == '404' and exc_content['errors'][0]['reason'] == 'notFound':
            logging.debug(exc_content['errors'][0])
            logging.debug('callback----OK-------')
            logging.debug('request_id:'+str(request_id) + ' reason:NOTFOUND' )
            ngcnt = ngcnt + 1
            pass            
        else:
            logging.debug('callback----NG-------')
            logging.debug('request_id:'+str(request_id) + ' exception:' + str(vars(exception)['content']) )
            
            # Do something with the response
            raise exception
    return response

def init():
    global okcnt
    global ngcnt
    okcnt = 0
    ngcnt = 0
#@jit
def main():
    u""" main メイン処理
    メインで実行する処理
    :return: なし
    """
    #try:
    #import argparse
    global priEmail
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    #except ImportError:
    #    flags = None
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'python-quickstart.json')
    store = Storage(credential_path)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        creds = tools.run_flow(flow, store, flags) \
              if flags else tools.run(flow, store)
    CAL = build('calendar', 'v3', http=creds.authorize(Http()))
    progressList = []
    for calendarcsv in CALENDARCSVS:
        init()
        cnt = 0
        _okcnt = 0
        _ngcnt = 0
        logging.debug(WORKDIR + calendarcsv)
        clList= getCalendarData(WORKDIR + calendarcsv)
        logging.debug('------calendarDataDelete start------')
        for event in clList:
            #event = json.loads(event,encoding='UTF-8')
            logging.debug('LINECNT:'+ str(cnt+1))
            #try:
                #ref = CAL.events().delete(calendarId=event['organizer'], eventId=event['id']).execute()
            if priEmail == '':
                priEmail = event['organizer']
            if priEmail != event['organizer']:
                _okcnt, _ngcnt = bachExecute(event, CAL, priEmail, creds.authorize(Http()), 'change')
                priEmail = event['organizer']

            if(cnt < len(clList) - 1):
                _okcnt, _ngcnt = bachExecute(event, CAL,event['organizer'], creds.authorize(Http()))
            else:
                _okcnt, _ngcnt = bachExecute(event, CAL,event['organizer'], creds.authorize(Http()),True)
            #except Exception as e:
            #    logging.debug(format(e))

            cnt = cnt + 1
            progress(cnt-1, len(clList))

        progress(cnt-1, len(clList))
        logging.debug('------calendarDataDelete end------')
        logging.debug('CSVFILE:' + WORKDIR + calendarcsv)
        logging.debug('OK CNT:'+str(_okcnt))
        logging.debug('NG CNT:'+str(_ngcnt))

        progressList.append('CSVFILE:' + calendarcsv + ' OKCNT:'+str(_okcnt) + ' NGCNT:'+str(_ngcnt) )

    logging.debug('------FINISH calendarDataDelete------')
    for pdata in progressList:
        logging.debug(pdata)


if __name__ == '__main__':

    main()
