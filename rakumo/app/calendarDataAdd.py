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
from .loginglibrary import init
from .checkList import doCheck
#from loginglibrary import init
#from checkList import doCheck
from apiclient.http import BatchHttpRequest
import random
import time
from apiclient.errors import HttpError
from google.oauth2 import service_account
import googleapiclient.discovery
from apiclient.http import BatchHttpRequest
import random
import ast
import shutil
import os.path

logging = init('calendarMain')
batchcount = 0
batch = None
okcnt = 0
ngcnt = 0
priEmail = ''
pricnt = 0
execMember = {}


"固定値の設定"
WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
USERCSV = WORKDIR + 'user.csv'
USEREXCSV = WORKDIR + 'userUnique.csv'
USERNOCSV = WORKDIR + 'userNotMigration.csv'
RESOURCE = WORKDIR + 'resource.csv'
HOLIDAY = WORKDIR + 'holiday.csv'
CALENDARCSV = WORKDIR + '180517_GroupSession_change.csv'
CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret.json'
SERVICE_ACCOUNT_FILE = '/var/www/html/mysite/rakumo/json/service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
TODAY = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
OUTPUTDIR = WORKDIR + 'result_'+TODAY
TEMPDIR = '/tmp/'+'result_'+TODAY
WORKLOG = OUTPUTDIR + '/calendarList_'+TODAY+'.csv'
WORKLOG2 = OUTPUTDIR +'/calendarResult_'+TODAY+'.txt'
DICTKEY = ['kind', 'etag', 'id', 'status', 'htmlLink', 'created', 'updated', 'summary', 'description', 'location', 'transparency', 'creator', 'organizer', 'start', 'end', 'recurrence', 'visibility', 'iCalUID', 'sequence', 'attendees', 'extendedProperties', 'reminders', 'overrides','guestsCanSeeOtherGuests','guestsCanInviteOthers','guestsCanModify']
EVENTKEY = ['SID','GRPID','SUMMARY','DESCRIPTION','BIKO','KIND','RESOURCE','DAILY','STARTDATE','STARTTIME','ENDDATE','ENDTIME','SEI','MEI','PRISEI','PRIMEI','KOJINFLG']
#HEADER = {'Content-Type': 'multipart/mixed; boundary=BOUNDARY'}
#os.mkdir(OUTPUTDIR)
#os.mkdir(TEMPDIR)
#writeObjt = codecs.open(WORKLOG2, 'w')
#csvf = codecs.open(WORKLOG, 'w')
#writeObj = csv.DictWriter(csvf, DICTKEY)  # キーの取得
#writeObj.writeheader()  # ヘッダー書き込
csvf = None
writeObj = None
resHourList = []

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
            logging.info('changeName!!:'+ret['name']+'→'+memberData['EXNAME'])
            ret['name'] = memberData['EXNAME']
        if ret['priName'] == memberData['NAME']:
            logging.info('changePriName!!:'+ret['priName']+'→'+memberData['EXNAME'])
            ret['priName'] = memberData['EXNAME']
    return ret

@jit
def checkUseName(ret):
    u"""checkUseName 名前が特殊なユーザー名を変更する処理
    :param ret: 対象データ
    :return: チェック後データ
    """
    for memberData in getNotMigrationData():
        memberData = json.loads(memberData,encoding='UTF-8')
        #logging.debug(ret['name'])
        #logging.debug(memberData['NAME'])
        if ret['name'] == memberData['NAME'] or ret['priName'] == memberData['NAME']:
            ret['useFlg'] = False
            break

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
                #if memdata is None:
                ret['pri_email'] = memberData['primaryEmail']
                #else:
                #    ret['pri_email'] = memdata['pri_email']
                flg2 = True
            if flg1 == True and flg2 == True:
                ret['retFlg'] = True
                break

        if flg1 == False or flg2 == False:
            logging.debug('name:'+ret['name'])
            logging.debug('priName:'+ret['priName'])
            logging.debug('flg1:'+str(flg1))
            logging.debug('flg2:'+str(flg2))
            if flg1 == True:
                ret['pri_email'] = ret['email']
                ret['retFlg'] = True
                ret['priFlg'] = False
                logging.info('NotPriName name:'+ret['name']+' priName:'+ret['priName'])
            elif flg2 == True:
                ret['email'] = ret['pri_email']
                ret['retFlg'] = True
                ret['priFlg'] = True
                logging.info('NotName name:'+ret['name']+' priName:'+ret['priName'])
            else:
                logging.info('NotPriName,Name:'+ret['name']+' priName:'+ret['priName'])
                ret = None
    else:
        logging.info('NotUse!!name:'+ret['name']+' priName:'+ret['priName'])
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
    retList = []
    logging.debug(data['RESOURCE'].split(','))
    for rsData in data['RESOURCE'].split(','):
        for resourceData in getResource():
            resourceData = json.loads(resourceData,encoding='UTF-8')
            #resourceData = json.loads(resourceData,encoding='shift_jis')
            if resourceData['resourceName'] == rsData:
                retList.append(resourceData['resourceEmail'])
                break
    return retList
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
    calendarList = csvToJson(CALENDARCSV,'shift-jis')
    return calendarList

def csvToJson(csvData,encode = 'utf-8'):
    u""" csvToJson CSVを読み込みJSON化する
    CSVファイルを読み込みJSONデータにして返します
    :param csvData: CSVファイルのフルパス
    :return: JSONデータ
    """
    jsonData = []
    with open(csvData, 'r',encoding=encode, errors='ignore', newline='') as f:
        for line in csv.DictReader(f):
            line_json = json.dumps(line, ensure_ascii=False)
            jsonData.append(line_json)
    return jsonData

def check_resourcecalendar(clData, resAddress, service):
    u""" 登録する設備がすでにカレンダーに登録済みかどうかを確認する
    """
    global resHourList

    calendarList = None
    logging.debug('check_resourcecalendar'+resAddress)
    start = clData['STARTDATE'].replace('/','-')+'T00:00:00Z'
    end = clData['ENDDATE'].replace('/','-')+'T23:59:59Z'
    chkCStart =  datetime.datetime.strptime(clData['STARTDATE']+ ' '+clData['STARTTIME']+':00', '%Y/%m/%d %H:%M:%S')
    chkCEnd =  datetime.datetime.strptime(clData['ENDDATE']+ ' '+clData['ENDTIME']+':00', '%Y/%m/%d %H:%M:%S')
    
    logging.debug('--csvdeplication--')
    logging.debug(resHourList)
    for rhData in resHourList:
        if rhData['resid'] == resAddress:
            rhchkStart = rhData['chkStart']
            rhchkEnd = rhData['chkEnd']
            logging.debug(rhchkStart)
            logging.debug(rhchkEnd)
            logging.debug(chkCStart)
            logging.debug(chkCEnd)            
            if (rhchkStart >= chkCStart and rhchkEnd <= chkCEnd) \
                or (rhchkStart <= chkCStart and rhchkEnd >= chkCStart) \
                or (rhchkStart <= chkCEnd and rhchkEnd >= chkCEnd) \
                or (rhchkStart <= chkCStart and rhchkEnd >= chkCEnd):
                logging.debug('csvFalse')
                resHourList = []
                return False
    logging.debug('---')

    try:
        calendar = service.events().list(calendarId=resAddress, timeMin=start, timeMax=end, timeZone="Asia/Tokyo", orderBy="startTime", singleEvents=True)
        calendarList = calendar.execute()
    except HttpError as error:
        calendarList = None
        raise error
    if not calendarList:
        logging.debug('No calendar in the domain.')
        return True
    else:
        #logging.debug(calendarList['items'])
        for calendardata in calendarList['items']:
            chkStart = datetime.datetime.strptime(calendardata['start']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00')
            chkEnd = datetime.datetime.strptime(calendardata['end']['dateTime'], '%Y-%m-%dT%H:%M:%S+09:00')
            logging.debug(chkStart)
            logging.debug(chkEnd)
            logging.debug(chkCStart)
            logging.debug(chkCEnd)
            if (chkStart >= chkCStart and chkEnd <= chkCEnd) \
                or (chkStart <= chkCStart and chkEnd >= chkCStart) \
                or (chkStart <= chkCEnd and chkEnd >= chkCEnd) \
                or (chkStart <= chkCStart and chkEnd >= chkCEnd):
                logging.debug('False')
                resHourList = []
                return False
            else:
                logging.debug('True')
    
    resHourList.append({'resid':resAddress, 'chkStart':chkCStart, 'chkEnd':chkCEnd})
    return True
@jit
def createEvent(clData, memData=None, service=None):
    u""" createEvent カレンダー入力データを作成
    カレンダーデータからGoogleAPIで実行するためのパラメータを設定する
    :param clData: カレンダーデータ
    :return: GoogleAPI実行イベントデータ
    """
    # 名前のチェック
    if memData is None:
        memData = getMemberAddress(clData)
    #if memData is None:
    #    return [], None
    # 会議室のチェック
    if clData['RESOURCE'] != 'null':
        resList = getResourceAddress(clData)
    else:
        resList = []
    for resData in resList:
        if check_resourcecalendar(clData, resData, service) == False:
            return [], None

    # タイトル設定
    EVENT = {'summary': clData['SUMMARY']}

    # 開始日を抽出
    eventStartDate = datetime.datetime.strptime(clData['STARTDATE'].replace('/','-')+' '+clData['STARTTIME']+':00', '%Y-%m-%d %H:%M:%S')
    eventStartDateD = str(eventStartDate)[0:10]
    eventStartDateT = str(eventStartDate)[11:19]

    # 終了日を抽出
    eventEndDate = datetime.datetime.strptime(clData['ENDDATE'].replace('/','-')+' '+clData['ENDTIME']+':00', '%Y-%m-%d %H:%M:%S')
    eventEndDateD = str(eventEndDate)[0:10]
    eventEndDateT = str(eventEndDate)[11:19]
    
    # 終日の場合は時間を設定しない
    if clData['DAILY'] == STR_ONE:
        # 開始日設定
        EVENT['start'] = {'date': eventStartDateD}
        # 終了日設定1日足す
        if eventStartDateD == eventEndDateD:
            eventEndDateD = str(eventEndDate + datetime.timedelta(days=1))[0:10]
        EVENT['end'] = {'date': eventEndDateD}
    else:
        # 開始日設定
        EVENT['start'] = {
            'dateTime': eventStartDateD + 'T' + eventStartDateT + GMT_OFF,
            'timeZone': GMT_PLACE
        }
        # 終了日設定
        EVENT['end'] = {
            'dateTime': eventEndDateD + 'T' + eventEndDateT + GMT_OFF,
            'timeZone': GMT_PLACE
        }

    # 詳細設定 詳細と備考をくっつける
    description = [clData['DESCRIPTION']]
    if len(clData['BIKO']) > 0:
        description.append('----------')
        description.append(clData['BIKO'])
    EVENT['description'] = '\n'.join(description)
    # 色設定　色の設定からどのミーティングかを割り出す
    if clData['KIND'] == '1':
        EVENT['extendedProperties'] = {'shared':{'eventType':'important'}}
    elif clData['KIND'] == '2':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'meeting'}}
    elif clData['KIND'] == '3':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'visitFrom'}}
    elif clData['KIND'] == '4':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'tellFrom'}}
    elif clData['KIND'] == '5':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'meetCustomer'}}
    elif clData['KIND'] == '6':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'tellPromise'}}
    elif clData['KIND'] == '7':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'out'}}
    elif clData['KIND'] == '8':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'bizTrip'}}
    elif clData['KIND'] == '9':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'deliveryDeadline'}}
    elif clData['KIND'] == '10':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'employ'}}
    elif clData['KIND'] == '11':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'employ2'}}
    elif clData['KIND'] == '12':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'training'}}
    elif clData['KIND'] == '13':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'rest'}}
    elif clData['KIND'] == '14':
        EVENT['extendedProperties'] = {'shared': {'eventType': 'temporary'}}
    else:
        EVENT['extendedProperties'] = {'shared': {'eventType': 'other'}}

    # 編集権限(仮)
        EVENT['guestsCanModify'] = True

    # 公開設定
    if clData['KOJINFLG'] == '1':
        EVENT['visibility'] = 'confidential'
        EVENT['transparency'] = 'transparent'
    else:
        EVENT['visibility'] = 'default'
        EVENT['transparency'] = 'opaque'
    # 参加者設定
    EVENT['attendees'] = [
    #    {'email': 'ichinose-takahiro@919.jp'},
    #    {'email': '919.jp_353739393539393532@resource.calendar.google.com'}
    ]
    if memData is not None:
        EVENT['attendees'].append({'email': memData['email'],'responseStatus':'accepted'})
    for resData in resList:
         logging.debug('resData:'+resData)
    #if resData is not None:
         EVENT['attendees'].append({'email': resData,'responseStatus':'accepted'}) # 会議室を追加

    return EVENT,memData['pri_email']

def bachExecute(EVENT, service, calendarId, http, _okcnt, _ngcnt, lastFlg = None):
    global batchcount
    global batch
    global okcnt
    global ngcnt
    global priEmail
    global resHourList

    okcnt = _okcnt
    ngcnt = _ngcnt
    rtnFlg = False

    if batch is None:
        batch = service.new_batch_http_request(callback=insert_calendar)
    logging.debug('-----batchpara-------')
    logging.debug(calendarId)
    #if batchcount < 50 and lastFlg != 'change':
    if batchcount < 50 and EVENT != []:
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
                logging.debug(batch)
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

        batch = service.new_batch_http_request(callback=insert_calendar)
        logging.debug('batchexecute-------after---------------------')
        batchcount = 0
    if rtnFlg == True:
        resHourList = []

    return okcnt, ngcnt

def insert_calendar(request_id, response, exception):
    global writeObj
    global okcnt
    global ngcnt
    global execMember
    if exception is None:
        logging.debug('callback----OK-------')
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        writeObj.writerow(response)
        okcnt = okcnt + 1
        #organizer = ast.literal_eval(response['organizer'])
        organizer = response['organizer']
        if organizer['email'] in execMember:
            execMember[organizer['email']]['cnt'] = execMember[organizer['email']]['cnt'] + 1
        else:
            execMember[organizer['email']] = {'cnt': 1}
        pass
    else:
        logging.debug('callback----except start----')
        logging.debug('request_id:'+str(request_id) + ' response:' + str(response) )
        logging.debug(json.loads(vars(exception)['content'], encoding='UTF-8')['error'])

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

        logging.debug('callback----except end----')
    return response

def init():
    global okcnt
    global ngcnt
    okcnt = 0
    ngcnt = 0

#@jit
def Process(name):
    global CALENDARCSV
    #global writeObjt

    CALENDARCSV = name
    #try:
    getProcess()
    #except HttpError as error:
    #    writeObjt.write('予期しないエラー\n')
    #    writeObjt.write(error)
    #writeObjt.close()    
    return TEMPDIR

def checkMissGrpList(missGrpList, clData):
    for mgd in missGrpList:
        if mgd['GRPID'] == clData['GRPID']:
            return False
    return True

def getProcess():
    u""" main メイン処理
    メインで実行する処理
    :return: なし
    """
    global priEmail
    global execMember
    #global writeObjt
    global csvf
    global writeObj
    global batch
    global TODAY
    global WORKLOG
    global WORKLOG2
    global OUTPUTDIR

    TODAY = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
    OUTPUTDIR = WORKDIR + 'result_'+TODAY
    WORKLOG = OUTPUTDIR + '/calendarList_'+TODAY+'.csv'
    WORKLOG2 = OUTPUTDIR +'/calendarResult_'+TODAY+'.txt'

    if os.path.exists(OUTPUTDIR) == False:
        os.mkdir(OUTPUTDIR)
    writeObjt = codecs.open(WORKLOG2, 'w')
    csvf = codecs.open(WORKLOG, 'w')
    writeObj = csv.DictWriter(csvf, DICTKEY)  # キーの取得
    writeObj.writeheader()  # ヘッダー書き込

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
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

    # カレンダーデータを取得
    clList= getGroupSessionList()
    doCheck(clList, EVENTKEY)
    EVENT = []
    gid = ''
    cnt = 0
    noUseCnt = 0
    noMigCnt = 0
    memData = None
    recr_cnt = 0
    init()
    _okcnt = 0
    _ngcnt = 0
    batch = None
    missGrpList = []

    for clData in clList:
        logging.info('csvRowCount:'+str(cnt))
        #clData = json.loads(clData,encoding='UTF-8')
        clData = json.loads(clData,encoding='SHIFT-JIS')
        # すでに施設予約の入っているカレンダーのあるグループは追加対象にいれない。
        if checkMissGrpList(missGrpList, clData) == False:
            cnt = cnt + 1
            continue
        memData = getMemberAddress(clData, memData)
        #logging.debug(memData)
        if memData is not None and memData['retFlg'] == True and memData['useFlg'] == True:
            # 同じグループのデータを取得してまとめて登録する
            if EVENT != [] :
                if gid == clData['GRPID'] and clData['GRPID'] != '-1' and memData['priFlg'] == True:
                    if {'email': memData['email'], 'responseStatus': 'accepted'} not in EVENT['attendees']:
                        EVENT['attendees'].append({'email': memData['email'],'responseStatus':'accepted'})
                    # resourceDataのチェックと挿入
                    #resAddress = getResourceAddress(clData)
                    resAddressList = getResourceAddress(clData)
                    for resAddress in resAddressList:
                        logging.debug(resAddress)
                        if check_resourcecalendar(clData, resAddress, CAL) == False:
                            logging.debug('false1')
                            missGrpList.append({'SID':clData['SID'], 'GRPID':clData['GRPID']})
                            _ngcnt = _ngcnt + 1
                            EVENT = []
                            break
                        if {'email': resAddress,'responseStatus':'accepted'} not in EVENT['attendees'] and resAddress is not None:
                            EVENT['attendees'].append({'email': resAddress, 'responseStatus': 'accepted'})
                    #elif resAddress is not None:
                    #    memData['pri_email'] = resAddress
                    cnt = cnt + 1
                    gid = clData['GRPID']
                    continue
                else:
                    logging.debug(EVENT)

                    if priEmail != memData['pri_email']:
                        logging.debug('---change---')
                        logging.debug(priEmail)
                        logging.debug(memData['pri_email'])
                        _okcnt, _ngcnt = bachExecute(EVENT, CAL, priEmail, creds.authorize(Http()), _okcnt, _ngcnt, 'change')
                        priEmail = memData['pri_email']
                    else:
                        logging.debug('---execute---')
                        _okcnt, _ngcnt = bachExecute(EVENT, CAL, priEmail, creds.authorize(Http()), _okcnt, _ngcnt)
                    recr_cnt = 0
                    logging.debug('------------------------------')
                    EVENT, memData['pri_email'] = createEvent(clData, memData, CAL)
                    # 設備で重複スケジュールの場合は飛ばす
                    if EVENT == [] and memData['pri_email'] == None:
                        logging.debug('false2')
                        cnt = cnt + 1
                        _ngcnt = _ngcnt + 1
                        logging.debug(_ngcnt)
                        missGrpList.append({'SID':clData['SID'], 'GRPID':clData['GRPID']})
                        continue
            else:
                #初回データの取得
                recr_cnt = 0
                logging.debug('---start----')
                EVENT, memData['pri_email'] = createEvent(clData, memData, CAL)
                # 設備で重複スケジュールの場合は飛ばす
                if EVENT == [] and memData['pri_email'] == None:
                    logging.debug('false3')
                    cnt = cnt + 1
                    _ngcnt = _ngcnt + 1
                    logging.debug(_ngcnt)
                    missGrpList.append({'SID':clData['SID'], 'GRPID':clData['GRPID']})
                    continue
                priEmail = memData['pri_email']
        else:
            if memData is not None:
                # 移行対象ではないユーザ
                if memData['useFlg'] == False:
                    logging.warn('NoUseUser!!=lineNO:'+ str(cnt) +'] GRPID[' + clData['GRPID'] + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                    noUseCnt = noUseCnt + 1
                # 移行できなかったユーザー
                elif memData['retFlg'] == False:
                    logging.warn('DoNotMigrationData!!=lineNO:'+ str(cnt) +'] GRPID[' + clData['GRPID'] + '] NAME:' + memData['name'] + ' PRINAME:' + memData['priName'])
                    noMigCnt = noMigCnt + 1
                else:
                    logging.warn('ERRORMEMDATA=' + memData)
                    logging.warn('ERRORCALDATA=' + clData)
                    raise(ValueError("memDataerror!"))
            else:
                logging.warn(
                    'NoUser!!=lineNO:' + str(cnt) + '] GRPID[' + clData['GRPID'] + ']')
        gid = clData['GRPID']
        cnt = cnt + 1
    # 最後の一つは必ず実行する
    logging.debug('------------end----------------')
    logging.debug(EVENT)
    if memData is not None:
        _okcnt, _ngcnt = bachExecute(EVENT, CAL, memData['pri_email'], creds.authorize(Http()), _okcnt, _ngcnt, True)
    writeObjt.write('CSVFILE:' + WORKLOG + '\n')
    writeObjt.write('calendarMigration END count:'+str(cnt) + '\n')
    writeObjt.write('noUseCnt:' + str(noUseCnt) + '\n')
    writeObjt.write('noMigCnt:' + str(noMigCnt) + '\n')
    writeObjt.write('OK CNT:' + str(_okcnt) + '\n')
    writeObjt.write('NG CNT:' + str(_ngcnt) + '\n')
    writeObjt.write('---exec member count----' + '\n')
    logging.info('CSVFILE:' + WORKLOG)
    logging.info('calendarMigration END count:'+str(cnt))
    logging.info('noUseCnt:' + str(noUseCnt))
    logging.info('noMigCnt:' + str(noMigCnt))
    logging.info('OK CNT:' + str(_okcnt))
    logging.info('NG CNT:' + str(_ngcnt))
    logging.info('---exec member count----')
    for key, value in execMember.items():
        writeObjt.write(key+':'+str(value)+'\n')
        #writeObjt.writelines('\n')
        logging.info(key+':'+str(value))
    writeObjt.write('---setsubi Duplication list----' + '\n')
    logging.info('---setsubi Duplication list----')
    for missdata in missGrpList:
        writeObjt.write('SID:' + str(missdata['SID'])+', GRPID:'+ str(missdata['GRPID'])+'\n')
        logging.debug('SID:' + str(missdata['SID'])+', GRPID:'+ str(missdata['GRPID']))

    #writeObjt.close()
    shutil.make_archive(TEMPDIR, 'zip', root_dir=OUTPUTDIR)
    writeObjt.close()
    #return writeObjt

if __name__ == '__main__':

    Process('/var/www/html/mysite/rakumo/static/files/upload/import_test_2_20180613145307_.csv')
