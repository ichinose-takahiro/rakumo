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

logging = init('calendar')
batchcount = 0
batch = None

"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
CALENDARCSV = WORKDIR + 'calendarList.csv'
DELETESTRING = 'https://www.google.com/calendar/event?eid='
CLIENT_SECRET_FILE = './json/client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'

@jit
def getCalendarData():
    u"""getmemberData メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(CALENDARCSV)
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

@jit
def bachExecute(EVENT, service, http, lastFlg = None):
    global batchcount
    global batch
    if batch is None:
        batch = service.new_batch_http_request(callback=delete_calendar)
    logging.debug('-----batchpara-------')
    #logging.debug(vars(batch))
    logging.debug(EVENT)
    if batchcount < 100:
        batch.add(ref = service.events().delete(calendarId=EVENT['organizer'], eventId=EVENT['id']))
        batchcount = batchcount + 1
        logging.debug(str(batchcount))

    if batchcount >= 100 or lastFlg == True:
        logging.debug('batchexecute-------before---------------------')
        batch.execute(http=http)
        batch = service.new_batch_http_request(callback=delete_calendar)
        logging.debug('batchexecute-------after---------------------')
        batchcount = 0

@jit
def delete_calendar(request_id, response, exception):
    global writeObj
    if exception is None:
        logging.debug('callback----OK-------')
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        writeObj.writerow(response)
        pass
    else:
        logging.debug('callback----NG-------')
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        logging.debug('exception:')
        logging.debug(vars(exception))
        # Do something with the response
        #logging.debug('exception:' + exception)
        raise(Exception(exception))
    return response

@jit
def main():
    u""" main メイン処理
    メインで実行する処理
    :return: なし
    """
    #try:
    import argparse
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

    logging.debug('------calendarDataDelete start------')
    for event in getCalendarData():
        #try:
            #ref = CAL.events().delete(calendarId=event['organizer'], eventId=event['id']).execute()
        bachExecute(event, CAL, creds.authorize(Http()))

        #except Exception as e:
        #    logging.debug(format(e))

    logging.debug('------calendarDataDelete end------')

if __name__ == '__main__':

    main()
