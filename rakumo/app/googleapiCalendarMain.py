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
import random
import time
from apiclient.errors import HttpError
from google.oauth2 import service_account
import googleapiclient.discovery
from apiclient.http import BatchHttpRequest
import random

logging = init('calendarMain')
batchcount = 0
batch = None
okcnt = 0
ngcnt = 0
priEmail = ''
pricnt = 0

"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
USERCSV = WORKDIR + 'user.csv'
USEREXCSV = WORKDIR + 'userUnique.csv'
USERNOCSV = WORKDIR + 'userNotMigration.csv'
RESOURCE = WORKDIR + 'resource_test_20180206.csv'
HOLIDAY = WORKDIR + 'holiday.csv'
#CALENDARCSV = WORKDIR + '180206_GroupSession_edit.csv'
#CALENDARCSV = WORKDIR + '180308_GroupSession_test.csv'
CALENDARCSV = WORKDIR + '180206_GroupSession_edit_change_20180312.csv'
CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret.json'
SERVICE_ACCOUNT_FILE = '/var/www/html/mysite/rakumo/json/service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
TODAY = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
WORKLOG = WORKDIR + 'calendarList_'+TODAY+'.csv'
DICTKEY = ['kind', 'etag', 'id', 'status', 'htmlLink', 'created', 'updated', 'summary', 'description', 'location', 'transparency',
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

##DEBUG_ONLY
USERADDRESS = [
    'tobaru-hideyasu@919.jp','nishiyama-kohei@919.jp','inomata-toshiyuki@919.jp','takubo-hidenori@919.jp','koike-akihiro@919.jp',
    'morimoto-hikaru@919.jp','sato-manami@919.jp','kan-sayuri@919.jp','mikami-takashi@919.jp','hama-yasuki@919.jp',
    'hirata-naomi@919.jp','shiga-sakurako@919.jp','komagata-yukino@919.jp','kitabatake-yoshimi@919.jp','kaneda-yoko@919.jp',
    'kimura-satoko@919.jp','noma-chinami@919.jp','kasai-kazuaki@919.jp','suzuki-yugo@919.jp','isomoto-miho@919.jp',
    'nihonmatsu-yumeko@919.jp','saito-takamitsu@919.jp','iwasaki-sanae@919.jp','matsushita-atsushi@919.jp','matsumura-shun@919.jp',
    'matsubara-kosuke@919.jp','miyamoto-tomomi@919.jp','horino-shunya@919.jp','hogan-nobutaka@919.jp','ishida-yuko@919.jp',
    'yamaoka-yuina@919.jp','sato-sora@919.jp','ogawa-yoshiteru@919.jp','yoshida-hiroshi@919.jp','karasu-mikiko@919.jp',
    'yamada-ryohei@919.jp','sakamoto-ayako@919.jp','nomura-miku@919.jp','nakahira-shinya@919.jp'
]
##DEBUG_ONLY

def selectEmail():
    global priEmail
    global pricnt

    priEmail = USERADDRESS[pricnt]
    pricnt = pricnt + 1
    if pricnt == len(USERADDRESS):
        pricnt = 0

    return priEmail

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
def getMemberAddress(data, memdata = None):
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
    ret = {'name': membarName, 'priName': priName, 'retFlg': False, 'useFlg':True, 'priFlg':True}
    ret = checkUseName(ret)
    if ret['useFlg'] == True:
        ret = checkExName(ret)
        for memberData in getmemberData():
            memberData = json.loads(memberData,encoding='UTF-8')
            if memberData['fullName'] == ret['name']:
                ret['email'] = memberData['primaryEmail']
                flg1 = True
            if memberData['fullName'] == ret['priName']:
                if memdata is None:
                    ret['pri_email'] = memberData['primaryEmail']
                else:
                    ret['pri_email'] = memdata['pri_email']
                flg2 = True
            if flg1 == True and flg2 == True:
                ret['retFlg'] = True
                break
    if flg1 == False or flg2 == False:
        logging.debug('flg1:'+str(flg1))
        logging.debug('flg2:'+str(flg2))
        if flg1 == True:
            ret['pri_email'] = ret['email']
            ret['retFlg'] = True
            ret['priFlg'] = False
        else:
            ret = None
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
        if resourceData['generatedResourceName'] == '[テスト中]'+data['RESOURCE']:
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
    if memData is None:
        return [], None
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
    #if clData['EDITFLG'] == SCEDIT['GROUP']:
    #    EVENT['guestsCanModify'] = True

    # 公開設定
    if clData['PUBLICFLG'] == '1':
        EVENT['visibility'] = 'confidential'
        EVENT['transparency'] = 'transparent'
    elif clData['PUBLICFLG'] == '2':
        EVENT['visibility'] = 'default'
        EVENT['transparency'] = 'opaque'
    elif clData['PUBLICFLG'] == '3':
        EVENT['visibility'] = 'private'
        EVENT['transparency'] = 'transparent'
    else:
        EVENT['visibility'] = 'default'
        EVENT['transparency'] = 'opaque'
    # 参加者設定
    EVENT['attendees'] = [
    #    {'email': 'ichinose-takahiro@919.jp'},
    #    {'email': '919.jp_353739393539393532@resource.calendar.google.com'}
    ]
    if memData != {}:
        EVENT['attendees'].append({'email': memData['email'],'responseStatus':'accepted'})
    if resData is not None:
    #    EVENT['attendees'].append({'email': memData['pri_email'],'responseStatus':'accepted'}) # 会議室の重複予約対応
    #    memData['pri_email'] = resData
         EVENT['attendees'].append({'email': resData,'responseStatus':'accepted'}) # 会議室を追加

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
    return EVENT,memData['pri_email']

def bachExecute(EVENT, service, calendarId, http, lastFlg = None):
    global batchcount
    global batch
    global okcnt
    global ngcnt
    global priEmail
    rtnFlg = False

    if batch is None:
        batch = service.new_batch_http_request(callback=insert_calendar)
    logging.debug('-----batchpara-------')
    #logging.debug(vars(batch))
    logging.debug(priEmail)
    logging.debug(calendarId)
    #logging.debug(EVENT)
    if batchcount < 50 and lastFlg != 'change':
        batch.add(service.events().insert(calendarId=calendarId, conferenceDataVersion=1, sendNotifications=False,body=EVENT))
        batchcount = batchcount + 1
        logging.debug(str(batchcount))

    if batchcount >= 50 or lastFlg == True or lastFlg == 'change':
        logging.debug('batchexecute-------before---------------------')

        for n in range(0, 20):  # 指数バックオフ(遅延処理対応)

            try:
#SERVICEACCOUNT
#                batch.execute()
#SERVICEACCOUNT
                batch.execute(http=http)
                #selectEmail()
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

        batch = service.new_batch_http_request(callback=insert_calendar)
        logging.debug('batchexecute-------after---------------------')
        batchcount = 0

    return okcnt, ngcnt

def insert_calendar(request_id, response, exception):
    global writeObj
    global okcnt
    global ngcnt
    if exception is None:
        logging.debug('callback----OK-------')
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        writeObj.writerow(response)
        okcnt = okcnt + 1
        pass
    else:
        exc_content = json.loads(vars(exception)['content'], encoding='UTF-8')['error']
        if str(exc_content['code']) == '410' and exc_content['errors'][0]['reason'] == 'deleted':
            logging.debug('callback----OK-------')
            logging.debug('request_id:' + str(request_id) + ' reason:deleted')
            ngcnt = ngcnt + 1
            pass
        else:
            logging.debug('callback----NG-------')
            logging.debug('request_id:' + str(request_id) + ' exception:' + str(vars(exception)['content']))
            # Do something with the response
            raise exception
    return response


@jit
def delHolidayData(exdate, rdate):
    exdatestr = exdate.replace('EXDATE;TZID=%s:' % GMT_PLACE, "")
    exdateList = exdatestr.split(',')
    rdatestr = rdate.replace('RDATE;TZID=%s:' % GMT_PLACE, "")
    rdateList = rdatestr.split(',')
    rtnExdateList = []
    for date in exdateList:
        if date not in rdateList:
            rtnExdateList.append(date)
    retunExdate = 'EXDATE;TZID=%s:' % GMT_PLACE + ','.join(rtnExdateList)
    return retunExdate

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
    global priEmail
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
#SERVICEACCOUNT
#    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#    CAL = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
#SERVICEACCOUNT
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
    init()
    cnt = 0
    _okcnt = 0
    _ngcnt = 0    #global batch
    #batch = CAL.new_batch_http_request(callback=insert_calendar)
    #try:
    #priEmail = selectEmail()
    #for clData in sorted(clList, key=lambda x:(x[15]+x[16],x[3],x[4],x[1])):
    for clData in clList:
        clData = json.loads(clData,encoding='UTF-8')
        memData = getMemberAddress(clData, memData)
        if memData is not None and memData['retFlg'] == True and memData['useFlg'] == True:
            # 同じグループのデータを取得してまとめて登録する
            if EVENT != [] :
                if gid == clData['SCD_GRP_SID'] and clData['SCD_GRP_SID'] != '-1' and memData['priFlg'] == True:
                    if {'email': memData['email'],'responseStatus':'accepted'} not in EVENT['attendees']:
                        EVENT['attendees'].append({'email': memData['email']})
                    # resourceDataのチェックと挿入
                    resAddress = getResourceAddress(clData)
                    if {'email': resAddress,'responseStatus':'accepted'} not in EVENT['attendees'] and resAddress is not None:
                        EVENT['attendees'].append({'email': resAddress,'responseStatus':'accepted'})
                    #elif resAddress is not None:
                    #    memData['pri_email'] = resAddress
                    cnt = cnt + 1
                    continue
                #elif clData['SCE_SID'] != STR_MONE and eid == clData['SCE_SID']
                elif checkExData(clData) == True and clData['SCE_SID'] != STR_MONE and eid == clData['SCE_SID'] and recr_cnt <= 30 and memData['priFlg'] == True:
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
                    if 'recurrence' in EVENT.keys() and EVENT['recurrence'] != [ ]:
                        EVENT['recurrence'][0] = delHolidayData(EVENT['recurrence'][0], EVENT['recurrence'][1])
                    logging.debug(EVENT)
                    logging.debug(memData['pri_email'])
                    logging.debug(priEmail)
                    #メールアドレスがないやつがあるので、取得せなならん
                    #ref = CAL.events().insert(calendarId=memData['pri_email'], conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
                    #ref = CAL.events().insert(calendarId='appsadmin@919.jp', conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
#SERVICEACCOUNT
#                    _okcnt, _ngcnt = bachExecute(EVENT, CAL, memData['pri_email'], credentials)
#SERVICEACCOUNT
                    # 入れ替えのタイミングなので、先に実行してから次にいく。
                    if priEmail == '':
                        priEmail = memData['pri_email']
                    if priEmail != memData['pri_email']:
                        _okcnt, _ngcnt = bachExecute(EVENT, CAL, priEmail, creds.authorize(Http()), 'change')
                        priEmail = memData['pri_email']

                    #_okcnt, _ngcnt = bachExecute(EVENT, CAL, priEmail, creds.authorize(Http()))
                    _okcnt, _ngcnt = bachExecute(EVENT, CAL, memData['pri_email'], creds.authorize(Http()))
                    recr_cnt = 0
                    logging.debug('------------------------------')
                    #logging.debug()
                    #w.writerow(ref)
                    EVENT, memData['pri_email'] = createEvent(clData)
            else:
                #初回データの取得
                recr_cnt = 0
                EVENT, memData['pri_email'] = createEvent(clData)
        else:
            if memData is not None:
                # 移行対象ではないユーザ
                if memData['useFlg'] == False:
                    logging.warn('NoUseUser!!=lineNO:'+ str(cnt) +' SCD_SID[' + clData['SCD_SID'] + '] SCE_SID[' + clData['SCE_SID'] + '] SCD_GRP_SID[' + clData['SCD_GRP_SID'] + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                    noUseCnt = noUseCnt + 1
                # 移行できなかったユーザー
                elif memData['retFlg'] == False:
                    logging.warn('DoNotMigrationData!!=lineNO:'+ str(cnt) +' SCD_SID[' + clData['SCD_SID'] + '] SCE_SID[' + clData['SCE_SID'] + '] SCD_GRP_SID[' + clData['SCD_GRP_SID'] + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                    noMigCnt = noMigCnt + 1
                else:
                    logging.warn('ERRORMEMDATA=' + memData)
                    logging.warn('ERRORCALDATA=' + clData)
                    raise(ValueError("memDataerror!"))
            else:
                logging.warn(
                    'NoUser!!=lineNO:' + str(cnt) + ' SCD_SID[' + clData['SCD_SID'] + '] SCE_SID[' + clData[
                        'SCE_SID'] + '] SCD_GRP_SID[' + clData['SCD_GRP_SID'] + ']')
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
        # 最後の一つ前と最後のメンバーが違う場合は先に実行する。
        if priEmail != memData['pri_email']:
            _okcnt, _ngcnt = bachExecute(EVENT, CAL, priEmail, creds.authorize(Http()), 'change')
        _okcnt, _ngcnt = bachExecute(EVENT, CAL, memData['pri_email'], creds.authorize(Http()), True)
    #ref = CAL.events().insert(calendarId=memData['pri_email'], conferenceDataVersion=1,sendNotifications=False, body=EVENT).execute()
    #ref = CAL.events().insert(calendarId='ichinose-takahiro@919.jp', conferenceDataVersion=1, sendNotifications=False, body=EVENT).execute()
    #logging.debug(ref)
    #writeObj.writerow(ref)
    progress(cnt-1, len(clList))
    #except ValueError as e:
    #    logging.debug('Exception=lineNO:'+ str(cnt) +' SCD_SID[' + str(sid) + '] SCE_SID[' + str(eid) + '] SCD_GRP_SID[' + str(gid) + ']:' + 'ERROR:',e.args)
    #    logging.debug('ERROR END')
    logging.debug('CSVFILE:' + WORKLOG)
    logging.debug('calendarMigration END count:'+str(cnt))
    logging.debug('noUseCnt:' + str(noUseCnt))
    logging.debug('noMigCnt:' + str(noMigCnt))
    logging.debug('OK CNT:' + str(_okcnt))
    logging.debug('NG CNT:' + str(_ngcnt))

if __name__ == '__main__':

    main()
