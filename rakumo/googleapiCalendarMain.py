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
import codecs
import os
import argparse
from numba import jit
from pytz import timezone
from loginglibrary import init
from apiclient.http import BatchHttpRequest

logging = init('calendarMain')
batchcount = 0
batch = None

"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
USERCSV = WORKDIR + 'user.csv'
USEREXCSV = WORKDIR + 'userUnique.csv'
USERNOCSV = WORKDIR + 'userNotMigration.csv'
RESOURCE = WORKDIR + 'resource.csv'
HOLIDAY = WORKDIR + 'holiday.csv'
CALENDARCSV = WORKDIR + 'groupSessionData.csv'
CLIENT_SECRET_FILE = './json/client_secret.json'
SCOPES = 'https://www.googleapis.com/auth/calendar'
TODAY = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
WORKLOG = WORKDIR + 'calendarList_'+TODAY+'.csv'
DICTKEY = ['kind', 'etag', 'id', 'status', 'htmlLink', 'created', 'updated', 'summary', 'description', 'transparency',
           'creator', 'organizer', 'start', 'end', 'recurrence', 'visibility', 'iCalUID', 'sequence', 'attendees',
           'extendedProperties', 'reminders', 'overrides']
#HEADER = {'Content-Type': 'multipart/mixed; boundary=BOUNDARY'}
csvf = codecs.open(WORKLOG, 'w')
writeObj = csv.DictWriter(csvf, DICTKEY)  # キーの取得
writeObj.writeheader()  # ヘッダー書き込

STR_T = 'T'
GMT_OFF = '+09:00'  # ET/MST/GMT-4
GMT_PLACE = 'Asia/Tokyo'
STR_ONE = '1'
STR_ZERO = '0'
STR_MONE = '-1'
#色
SCCOLOR = {'BLUE':'1', #MTG
         'RED':'2',   #締切り・休み
         'GREEN':'3', #電話面談・来社面談
         'YELLOW':'4',    #外出
         'BLACK':'5', #備忘録・メモ
         'NAVY':'6',  #予備
         'RPURPLE':'7',   #研修
         'CYAN':'8',  #予備
         'GRAY':'9',  #予備
         'LBLUE':'10'}    #採用
SCEDIT = {'NONE':'0',
          'SELF':'1',
          'GROUP':'2'}

def getmemberData():
    u"""getmemberData メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    memberData = csvToJson(USERCSV)
    return memberData

def getExMemberData():
    u"""getmemberData 名称変更用メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    memberData = csvToJson(USEREXCSV)
    return memberData

def getNotMigrationData():
    u"""getmemberData 名称変更用メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    memberData = csvToJson(USERNOCSV)
    return memberData

@jit
def checkExName(ret):
    u"""checkExName 名前が特殊なユーザー名を変更する処理
    :param ret: 対象データ
    :return: チェック後データ
    """
    for memberData in getExMemberData():
        memberData = json.loads(memberData,encoding='UTF-8')
        if ret['name'] == memberData['NAME']:
            ret['name'] = memberData['EXNAME']

    return ret

@jit
def checkUseName(ret):
    u"""checkUseName 名前が特殊なユーザー名を変更する処理
    :param ret: 対象データ
    :return: チェック後データ
    """
    for memberData in getNotMigrationData():
        memberData = json.loads(memberData,encoding='UTF-8')
        if ret['name'] == memberData['NAME']:
            ret['useFlg'] = False

    return ret

@jit
def getMemberAddress(data):
    u"""getMemberAddress メンバーメールアドレス取得
    カレンダーデータからメンバーデータをチェックしてアドレスを抽出します
    :param data: カレンダーデータ
    :return: 参加者と登録者のメールアドレス
    """
    ret = {}
    flg1 = False
    flg2 = False
    membarName = data['SEI'] + data['MEI']
    priName = data['PRISEI']+data['PRIMEI']
    ret = {'name': membarName, 'priName': priName, 'retFlg': False, 'useFlg':True}
    ret = checkUseName(ret)
    if ret['useFlg'] == True:
        ret = checkExName(ret)
        for memberData in getmemberData():
            memberData = json.loads(memberData,encoding='UTF-8')
            if memberData['fullName'] == ret['name']:
                ret['email'] = memberData['primaryEmail']
                flg1 = True
            if memberData['fullName'] == ret['priName']:
                ret['pri_email'] = memberData['primaryEmail']
                flg2 = True
            if flg1 == True and flg2 == True:
                ret['retFlg'] = True
                break
    return ret
def getResource():
    u""" getResource 会議室データを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    resourceData = csvToJson(RESOURCE)
    return resourceData
@jit
def getResourceAddress(data):
    u""" getResourceAddress 会議室メールアドレス取得
    カレンダーデータから会議室データをチェックしてアドレスを抽出します
    :param data: カレンダーデータ
    :return: 会議室データのメールアドレス
    """
    ret = None
    for resourceData in getResource():
        resourceData = json.loads(resourceData,encoding='UTF-8')
        if resourceData['generatedResourceName'].replace('[テスト中]','') == data['RESOURCE']:
            ret = resourceData['resourceEmail']
            break
    return ret
def getcalendarData():
    u""" getcalendarData カレンダーデータを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(CALENDARCSV)
    return calendarData
@jit
def getHolidayData(timedata):
    u""" getHolidayData 祝日データを取得
    CSVの祝日データからAPI実行用の文字列に変換して取得します。
    :param timedata: 時間
    :return: 文字列リスト
    """
    holidayData = csvToJson(HOLIDAY)
    retList = ''
    holidaylength = len(holidayData)
    cnt = 0
    for holiday in holidayData:
        holiday = json.loads(holiday)
        retList = retList + holiday['start'] + STR_T + timedata
        cnt = cnt + 1
        if cnt < holidaylength:
            retList = retList + ','
    return retList
def getGroupSessionList():
    u""" getGroupSessionList カレンダーデータを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarList = csvToJson(CALENDARCSV)
    return calendarList

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
def checkExData(clData):
    u""" checkExData 繰り返しデータの存在チェック
    カレンダーデータが繰り返し登録するデータかをチェックします。
    :param clData: カレンダーデータ
    :return: 繰り返し登録アリ True、繰り返し登録なし False
    """
    ret = False
    if clData['SCE_SID'] != STR_MONE:
        if clData['BYDAY_SU'] == STR_ONE or clData['BYDAY_MO'] == STR_ONE or \
            clData['BYDAY_TU'] == STR_ONE or \
            clData['BYDAY_WE'] == STR_ONE or \
            clData['BYDAY_TH'] == STR_ONE or \
            clData['BYDAY_FR'] == STR_ONE or \
            clData['BYDAY_SA'] == STR_ONE or \
            clData['SCE_DAY'] != STR_ZERO or \
            clData['SCE_WEEK'] != STR_ZERO or \
            clData['SCE_DAILY'] != STR_ZERO or \
            clData['SCE_MONTH_YEARLY'] != STR_ZERO or \
            clData['SCE_DAY_YEARLY'] != STR_ZERO:
            ret = True
    return ret
@jit
def setExWeekly(clData):
    u""" setExWeekly 週ごとの設定を取得する
    カレンダーデータから、googleAPIに実行できる繰り返しデータを取得します。
    :param clData: カレンダーデータ
    :return: APIパラメータ(byDay)
    """
    byday = 'BYDAY='
    bydayFlg = False
    if clData['BYDAY_SU'] == STR_ONE:
        byday = byday + getWeeklyByDay(clData) + 'SU'
        bydayFlg = True
    if clData['BYDAY_MO'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'MO'
        bydayFlg = True
    if clData['BYDAY_TU'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'TU'
        bydayFlg = True
    if clData['BYDAY_WE'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'WE'
        bydayFlg = True
    if clData['BYDAY_TH'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'TH'
        bydayFlg = True
    if clData['BYDAY_FR'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'FR'
        bydayFlg = True
    if clData['BYDAY_SA'] == STR_ONE:
        if bydayFlg == True: byday = byday + ','
        byday = byday + getWeeklyByDay(clData) + 'SA'
    return byday
@jit
def getWeeklyByDay(clData):
    u""" getWeeklyByDay 何週目の繰り返しかの値取得する処理
    毎月登録時の何週目に連続登録するかを設定します
    :param clData: カレンダーデータ
    :return: APIパラメータ 繰り返さない場合は空文字
    """
    str = ''
    if clData['SCE_WEEK'] != STR_ZERO:
        str = clData['SCE_WEEK']
    return str
def progress(p, l):
    sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    sys.stdout.flush()
@jit
def createEvent(clData):
    u""" createEvent カレンダー入力データを作成
    カレンダーデータからGoogleAPIで実行するためのパラメータを設定する
    :param clData: カレンダーデータ
    :return: GoogleAPI実行イベントデータ
    """
    # 名前のチェック
    memData = getMemberAddress(clData)
    # 会議室のチェック
    if clData['RESOURCE'] != 'null':
        resData = getResourceAddress(clData)
    else:
        resData = None
    # タイトル設定
    EVENT = {'summary': clData['SUMMARY']}
    eventStartDate = (clData['STARTDATE'][0:10]).replace('/','-')
    eventEndDate = (clData['ENDDATE'][0:10]).replace('/','-')
    # 終日の場合は時間を設定しない
    if clData['SCD_DAILY'] == STR_ONE:
        # 開始日設定
        EVENT['start'] = {'date': eventStartDate}
        # 終了日設定1日足す
        #eventEndDate = clData['ENDDATE'][0:10]
        if clData['STARTDATE'][0:10] == eventEndDate:
            #eventEndDate = eventEndDate.replace('/', '-')
            eventEndDate = str(datetime.datetime.strptime(eventEndDate,"%Y-%m-%d") + datetime.timedelta(days=1))[0:10]
        EVENT['end'] = {'date': eventEndDate}
    else:
        # 開始日設定
        EVENT['start'] = {
            # 'dateTime': '2014-05-26T13:00:00%s' % GMT_OFF,
            #'dateTime': clData['STARTDATE'][0:10] + 'T' + clData['STARTDATE'][11:19] + GMT_OFF,
            'dateTime': eventStartDate + 'T' + clData['STARTDATE'][11:19] + GMT_OFF,
            'timeZone': GMT_PLACE
        }
        # 終了日設定
        EVENT['end'] = {
            # 'dateTime': '2014-05-26T14:00:00%s' % GMT_OFF,
            'dateTime': eventEndDate + 'T' + clData['ENDDATE'][11:19] + GMT_OFF,
            'timeZone': GMT_PLACE
        }
    # 詳細設定 詳細と備考をくっつける
    description = [clData['DESCRIPTION']]
    if len(clData['BIKO']) > 0:
        description.append('----------')
        description.append(clData['BIKO'])
    EVENT['description'] = '\n'.join(description)
    # 色設定　色の設定からどのミーティングかを割り出す
    #EVENT['colorId'] = clData['COLORID']
    if clData['COLORID'] == SCCOLOR['RED']:
        EVENT['extendedProperties'] = {'shared':{'eventType':'important'}}
    elif clData['COLORID'] == SCCOLOR['YELLOW']:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'out'}}
    elif clData['COLORID'] == SCCOLOR['GREEN']:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'visitFrom'}}
    elif clData['COLORID'] == SCCOLOR['BLUE']:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'meeting'}}
    elif clData['COLORID'] == SCCOLOR['RPURPLE']:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'training'}}
    elif clData['COLORID'] == SCCOLOR['LBLUE']:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'employ'}}
    else:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'other'}}

    # 編集権限(仮)
    #if clData['EDITID'] == SCEDIT['GROUP']:
    #    EVENT['guestsCanModify'] = 'TRUE'

    # 公開設定
    if clData['PUBLICFLG'] == '1':
        EVENT['visibility'] = 'confidential'
        EVENT['transparency'] = 'opaque'
    elif clData['PUBLICFLG'] == '2':
        EVENT['visibility'] = 'default'
        EVENT['transparency'] = 'opaque'
    elif clData['PUBLICFLG'] == '3':
        EVENT['visibility'] = 'private'
        EVENT['transparency'] = 'opaque'
    else:
        EVENT['visibility'] = 'default'
        EVENT['transparency'] = 'transparent'
    # 参加者設定
    EVENT['attendees'] = [
    #    {'email': 'ichinose-takahiro@919.jp'},
    #    {'email': '919.jp_353739393539393532@resource.calendar.google.com'}
    ]
    if memData != {}:
        EVENT['attendees'].append({'email': memData['email'],'responseStatus':'accepted'})
    if resData is not None:
        EVENT['attendees'].append({'email': memData['pri_email'],'responseStatus':'accepted'}) # 会議室の重複予約対応
        memData['pre_email'] = resData
        # EVENT['attendees'].append({'email': resData,'responseStatus':'accepted'}) # 会議室を追加

    # 繰り返し設定。RRULE設定についてはRFC-5545を参考とする
    # https://tools.ietf.org/html/rfc5545
    startDate = clData['STARTDATE'][0:10].replace('/','')
    endDate = clData['ENDDATE'][0:10].replace('/','')
    #EVENT['enddate'] = ''
    startTime = clData['STARTDATE'][11:19].replace(':','')
    EVENT['recurrence'] = [ ]
    ## 繰り返しデータのチェック
    if checkExData(clData) == True:
        EVENT['recurrence'].append("EXDATE;TZID=%s:" % GMT_PLACE +getHolidayData(startTime))
        EVENT['recurrence'].append("RDATE;TZID=%s:" % GMT_PLACE + startDate + 'T' + startTime)
        EVENT['recurrence'].append("RRULE:")
        #毎日
        if clData['SCE_DAILY'] == STR_ONE and clData['BYDAY_SU'] == STR_ZERO and clData['BYDAY_MO'] == STR_ZERO \
            and clData['BYDAY_TU'] == STR_ZERO and clData['BYDAY_WE'] == STR_ZERO and clData['BYDAY_TH'] == STR_ZERO \
            and clData['BYDAY_FR'] == STR_ZERO and clData['BYDAY_SA'] == STR_ZERO and clData['SCE_MONTH_YEARLY'] == STR_ZERO \
            and clData['SCE_DAY_YEARLY'] == STR_ZERO and clData['SCE_DAY'] == STR_ZERO :
            #EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=DAYLY;INTERVAL=1'
            EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=DAILY;INTERVAL=1;UNTIL='+ endDate
        ##毎週
        if clData['SCE_WEEK'] == STR_ZERO \
        and (clData['BYDAY_SU'] != STR_ZERO or clData['BYDAY_MO'] != STR_ZERO or clData['BYDAY_TU'] != STR_ZERO \
        or clData['BYDAY_WE'] != STR_ZERO or clData['BYDAY_TH'] != STR_ZERO or clData['BYDAY_FR'] != STR_ZERO \
        or clData['BYDAY_SA'] != STR_ZERO):
            byday = setExWeekly(clData)

            #EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=WEEKLY;' + byday + ';INTERVAL=1'
            EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=WEEKLY;' + byday + ';INTERVAL=1;UNTIL=' + endDate
        ##毎月
        if clData['SCE_DAY'] != STR_ZERO \
        or clData['SCE_WEEK'] != STR_ZERO \
        and (clData['BYDAY_SU'] != STR_ZERO or clData['BYDAY_MO'] != STR_ZERO or clData['BYDAY_TU'] != STR_ZERO \
        or clData['BYDAY_WE'] != STR_ZERO or clData['BYDAY_TH'] != STR_ZERO or clData['BYDAY_FR'] != STR_ZERO \
        or clData['BYDAY_SA'] != STR_ZERO):
            if clData['SCE_WEEK'] != STR_ZERO:
                byday = setExWeekly(clData)
                #EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=MONTH;' + byday + ';INTERVAL=1'
                EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=MONTHLY;' + byday + ';INTERVAL=1;UNTIL=' + endDate
            else:
                #EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=MONTH;BYMONTHDAY=' + clData['SCE_DAY'] + ';INTERVAL=1'
                EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=MONTHLY;BYMONTHDAY=' + (clData['SCE_DAY'] if clData['SCE_DAY'] != '99' else '-1') + ';INTERVAL=1;UNTIL=' + endDate
        ##毎年
        if clData['SCE_MONTH_YEARLY'] != STR_ZERO and clData['SCE_DAY_YEARLY'] != STR_ZERO:
            #EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=YEALY;BYMONTH=' + clData['SCE_MONTH_YEARLY'] + ';BYMONTHDAY=' + clData['SCE_DAY'] + ';INTERVAL=1'
            EVENT['recurrence'][2] = EVENT['recurrence'][2] + 'FREQ=YEARLY;BYMONTH=' + clData['SCE_MONTH_YEARLY'] + ';BYMONTHDAY=' + (clData['SCE_DAY_YEARLY'] if clData['SCE_DAY_YEARLY'] != '99' else '-1') + ';INTERVAL=1;UNTIL=' + endDate
    return EVENT

def bachExecute(EVENT, service, calendarId, http, lastFlg = None):
    global batchcount
    global batch
    if batch is None:
        batch = service.new_batch_http_request(callback=insert_calendar)
    logging.debug('-----batchpara-------')
    #logging.debug(vars(batch))
    logging.debug(EVENT)
    if batchcount < 50:
        batch.add(service.events().insert(calendarId=calendarId, conferenceDataVersion=1, sendNotifications=False,body=EVENT))
        batchcount = batchcount + 1
        logging.debug(str(batchcount))

    if batchcount >= 50 or lastFlg == True:
        logging.debug('batchexecute-------before---------------------')
        batch.execute(http=http)
        batch = service.new_batch_http_request(callback=insert_calendar)
        logging.debug('batchexecute-------after---------------------')
        batchcount = 0

def insert_calendar(request_id, response, exception):
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
def delHolidayData(exdate, rdate):
    exdatestr = exdate.replace('EXDATE;TZID=%s:' % GMT_PLACE, "")
    exdateList = exdatestr.split(',')
    rdatestr = rdate.replace('RDATE;TZID=%s:' % GMT_PLACE, "")
    rdateList = rdatestr.split(',')
    for date in rdateList:
        if date in exdateList:
            exdate = exdate.replace(',' + date, '')

    return exdate

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

    #csvf = codecs.open(WORKLOG, 'w')
    #w = csv.DictWriter(csvf, DICTKEY)  # キーの取得
    #w.writeheader()  # ヘッダー書き込み

    # カレンダーデータを取得
    clList= getGroupSessionList()
    EVENT = []
    eid = ''
    gid = ''
    sid = ''
    cnt = 0
    noUseCnt = 0
    noMigCnt = 0
    memData = None
    recr_cnt = 0
    #global batch
    #batch = CAL.new_batch_http_request(callback=insert_calendar)
    #try:
    for clData in clList:
        clData = json.loads(clData,encoding='UTF-8')
        memData = getMemberAddress(clData)
        if memData['retFlg'] == True and memData['useFlg'] == True:
            # 同じグループのデータを取得してまとめて登録する
            if EVENT != [] :
                if gid == clData['SCD_GRP_SID'] and clData['SCD_GRP_SID'] != '-1':
                    if {'email': memData['email'],'responseStatus':'accepted'} not in EVENT['attendees']:
                        EVENT['attendees'].append({'email': memData['email']})
                    # resourceDataのチェックと挿入
                    resAddress = getResourceAddress(clData)
                    if {'email': resAddress,'responseStatus':'accepted'} not in EVENT['attendees'] and resAddress is not None:
                        EVENT['attendees'].append({'email': resAddress})
                    cnt = cnt + 1
                    continue
                #elif clData['SCE_SID'] != STR_MONE and eid == clData['SCE_SID']
                elif checkExData(clData) == True and clData['SCE_SID'] != STR_MONE and eid == clData['SCE_SID'] and recr_cnt <= 30:
                    EVENT['recurrence'][1] = EVENT['recurrence'][1] + ',' + clData['STARTDATE'][0:10].replace('/','') + 'T' + clData['STARTDATE'][11:19].replace(':','')
                    #enddate = clData['ENDDATE'][0:10].replace('-','')
                    #if int(EVENT['enddate']) < int(enddate):
                    #    EVENT['enddate'] = enddate
                    cnt = cnt + 1
                    recr_cnt = recr_cnt + 1
                    continue
                else:
                    #if 'enddate' in EVENT and len(EVENT['enddate']) > 0:
                    #    EVENT['recurrence'][2] = EVENT['recurrence'][2] + ';UNTIL = ' + EVENT['enddate']
                    #繰り返しデータより追加するデータから削除対象のデータを取り除く
                    EVENT['recurrence'][0] = delHolidayData(EVENT['recurrence'][0], EVENT['recurrence'][1])
                    logging.debug(EVENT)
                    #メールアドレスがないやつがあるので、取得せなならん
                    #ref = CAL.events().insert(calendarId=memData['pri_email'], conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
                    #ref = CAL.events().insert(calendarId='appsadmin@919.jp', conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
                    bachExecute(EVENT, CAL, memData['pri_email'], creds.authorize(Http()))
                    recr_cnt = 0
                    logging.debug('------------------------------')
                    #logging.debug()
                    #w.writerow(ref)
                    EVENT = createEvent(clData)
            else:
                #初回データの取得
                EVENT = createEvent(clData)

        else:
            # 移行対象ではないユーザ
            if memData['useFlg'] == False:
                logging.debug('NoUseUser!!=lineNO:'+ str(cnt) +' SCD_SID[' + sid + '] SCE_SID[' + eid + '] SCD_GRP_SID[' + gid + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                noUseCnt = noUseCnt + 1
            # 移行できなかったユーザー
            elif memData['retFlg'] == False:
                logging.debug('DoNotMigrationData!!=lineNO:'+ str(cnt) +' SCD_SID[' + sid + '] SCE_SID[' + eid + '] SCD_GRP_SID[' + gid + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                noMigCnt = noMigCnt + 1
            else:
                logging.warn('ERRORMEMDATA=' + memData)
                logging.warn('ERRORCALDATA=' + clData)
                raise(ValueError("memDataerror!"))
        gid = clData['SCD_GRP_SID']
        eid = clData['SCE_SID']
        sid = clData['SCD_SID']
        cnt = cnt + 1
        progress(cnt-1, len(clList))
    #if 'enddate' in EVENT and len(EVENT['enddate']) > 0:
    #    EVENT['recurrence'][2] = EVENT['recurrence'][2] + ';UNTIL=' + EVENT['enddate']
    # 最後の一つは必ず実行する
    logging.debug('------------end----------------')
    if memData is not None:
        bachExecute(EVENT, CAL, memData['pri_email'], creds.authorize(Http()), True)
    #ref = CAL.events().insert(calendarId=memData['pri_email'], conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
    #ref = CAL.events().insert(calendarId='ichinose-takahiro@919.jp', conferenceDataVersion=1, sendNotifications=False, body=EVENT).execute()
    #logging.debug(ref)
    #writeObj.writerow(ref)
    progress(cnt-1, len(clList))
    #except ValueError as e:
    #    logging.debug('Exception=lineNO:'+ str(cnt) +' SCD_SID[' + str(sid) + '] SCE_SID[' + str(eid) + '] SCD_GRP_SID[' + str(gid) + ']:' + 'ERROR:',e.args)
    #    logging.debug('ERROR END')

    logging.debug('calendarMigration END count:'+str(cnt))
    logging.debug('noUseCnt:' + str(noUseCnt))
    logging.debug('noMigCnt:' + str(noMigCnt))

if __name__ == '__main__':

    main()
