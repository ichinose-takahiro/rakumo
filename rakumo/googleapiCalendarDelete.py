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

"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
#CALENDARCSV = WORKDIR + 'calendarList.csv'
DELETESTRING = 'https://www.google.com/calendar/event?eid='
CLIENT_SECRET_FILE = './json/client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
okcnt = 0
ngcnt = 0

CALENDARCSVS = [
#'calendarList_20180131164834.csv',
#'calendarList_20180131165134.csv',
#'calendarList_20180131175136.csv', #end
#'calendarList_20180131185652.csv', #end
#'calendarList_20180131190202.csv', #end
#'calendarList_20180201133539.csv', #end
#'calendarList_20180201140123.csv', #end
#'calendarList_20180201141441.csv', #end
#'calendarList_20180201150804.csv', #end
#'calendarList_20180201151342.csv', #end
#'calendarList_20180201154603.csv', #end
#'calendarList_20180201154707.csv', #end
#'calendarList_20180201154848.csv', #end
#'calendarList_20180201155158.csv', #end
#'calendarList_20180201160906.csv', #end
#'calendarList_20180201161130.csv', #end
#'calendarList_20180201162219.csv', #end
#'calendarList_20180201163435.csv', #end
#'calendarList_20180201163914.csv', #end
#'calendarList_20180201164337.csv', #end
#'calendarList_20180201164440.csv', #end
#'calendarList_20180201164815.csv', #end
#'calendarList_20180201165311.csv', #end
#'calendarList_20180201170346.csv', #end
#'calendarList_20180201170551.csv', #end
#'calendarList_20180201171225.csv', #end
#'calendarList_20180201171315.csv', #end
#'calendarList_20180201171616.csv', #end
#'calendarList_20180201172137.csv', #end
#'calendarList_20180201172644.csv', #end
#'calendarList_20180202110319.csv', #end
#'calendarList_20180202112739.csv', #end
'calendarList_20180202113228.csv',
'calendarList_20180202115103.csv',
'calendarList_20180202120343.csv',
'calendarList_20180202130013.csv',
]
@jit
def getCalendarData(calendacsv):
    u"""getmemberData メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(calendacsv)
    eventidList = []
    for data in calendarData:
        data = json.loads(data, encoding='UTF-8')

        eventidList.append({'id':data['id'],'organizer':ast.literal_eval(data['organizer'])['email']})
 #       eventidList.append({'id':data['id'],'organizer':data['organizer']})

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
    sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    sys.stdout.flush()

def bachExecute(EVENT, service, http, lastFlg = None):
    global batchcount
    global batch
    global okcnt
    global ngcnt
#    okcnt = 0
#    ngcnt = 0
    rtnFlg = False

    if batch is None:
        batch = service.new_batch_http_request(callback=delete_calendar)
    logging.debug('-----batchpara-------')
    logging.debug(EVENT)
    if batchcount < 100:
        batch.add(service.events().delete(calendarId=EVENT['organizer'], eventId=EVENT['id']))
        batchcount = batchcount + 1
        logging.debug(str(batchcount))

    if batchcount >= 100 or lastFlg == True:
        logging.debug('batchexecute-------before---------------------')

        for n in range(0, 5):  # 指数バックオフ(遅延処理対応)

            try:
                batch.execute(http=http)
                rtnFlg = True
                break
            except HttpError as error:
                if error.resp.reason in ['userRateLimitExceeded', 'quotaExceeded', 'internalServerError', 'backendError']:
                    logging.debug('exponential backoff')
                    time.sleep((2 ** n) + random.random())
                else:
                    logging.debug('else error')
                    raise Exception(error)

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
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        #writeObj.writerow(response)
        okcnt = okcnt + 1
        pass
    else:
        exc_content = json.loads(vars(exception)['content'],encoding='UTF-8')['error']
        if str(exc_content['code']) == '410' and exc_content['errors'][0]['reason'] == 'deleted':
            logging.debug('callback----OK-------')
            logging.debug('request_id:'+str(request_id) + ' reason:deleted' )
            ngcnt = ngcnt + 1
            pass            
        else:
            logging.debug('callback----NG-------')
            logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
            logging.debug('exception:')
            logging.debug(vars(exception))
            # Do something with the response
            raise(HttpError(exc_content['code'], reason=exc_content['errors'][0]['reason']))
    return response

def progress(p, l):
    sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    sys.stdout.flush()

def init():
    global okcnt
    global ngcnt
    okcnt = 0
    ngcnt = 0
@jit
def main():
    u""" main メイン処理
    メインで実行する処理
    :return: なし
    """
    #try:
    #import argparse
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
            logging.debug('LINECNT:'+ str(cnt))
            #try:
                #ref = CAL.events().delete(calendarId=event['organizer'], eventId=event['id']).execute()
            if(cnt < len(clList) - 1):
                _okcnt, _ngcnt = bachExecute(event, CAL, creds.authorize(Http()))
            else:
                _okcnt, _ngcnt = bachExecute(event, CAL, creds.authorize(Http()),True)
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
