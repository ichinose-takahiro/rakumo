# -*- coding: utf-8 -*-

u""" カレンダーのデータを追加するやつや
 google calendar apiの利用についてhttps://developers.google.com/google-apps/calendar/v3/reference/events/insert?hl=ja
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import csv
import json
import sys
import datetime
import ast

"固定値の設定"
WORKDIR = '/var/www/html/googleapi'
CALENDARCSV = WORKDIR + '/data/calendarList_0.csv'
DELETESTRING = 'https://www.google.com/calendar/event?eid='

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

def progress(p, l):
    sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    sys.stdout.flush()

def createEvent(clData):
    u""" createEvent カレンダー入力データを作成
    カレンダーデータからGoogleAPIで実行するためのパラメータを設定する
    :param clData: カレンダーデータ
    :return: GoogleAPI実行イベントデータ
    """
def printLog(ref):
    u""" printLog
    作成ログを保存する
    :param ref:
    :return:
    """
    print(ref)

def main():
    u""" main メイン処理
    メインで実行する処理
    :return: なし
    """
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('../json/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store, flags) \
              if flags else tools.run(flow, store)
    CAL = build('calendar', 'v3', http=creds.authorize(Http()))

    for event in getCalendarData():
        try:
            print(event)
            ref = CAL.events().delete(calendarId=event['organizer'], eventId=event['id']).execute()
            print(ref)
        except Exception as e:
            print(format(e))

if __name__ == '__main__':

    main()