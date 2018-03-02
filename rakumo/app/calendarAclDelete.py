# ユーザーのカレンダー権限データを取ってくる
import os
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from .loginglibrary import init
from .checkList import doCheck
import csv
import json
from apiclient.errors import HttpError

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret_calendar.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
CSVFILE = '/var/www/html/mysite/rakumo/static/files/acl.csv'

DICTKEY = ['calendarId', 'kind', 'etag', 'id', 'scope_type', 'scope_value','role', 'result']
EVENTKEY = {'calendarId', 'kind', 'etag', 'id', 'scope_type', 'scope_value','role'}

logging = init('acldel')

"会議室データを取得"
def getResource():
    resourceData = csvToJson(RESOURCE)
    return resourceData
"CSVを読み込みJSON化する"
def csvToJson(csvData):
    jsonData = []
    with open(csvData, 'r',encoding='utf-8', errors='ignore', newline='') as f:
        for line in csv.DictReader(f):
            line_json = json.dumps(line, ensure_ascii=False)
            jsonData.append(line_json)
    return jsonData

def getResourceData(service, w, calendarId, ruleId):

    try:
        service.acl().delete(calendarId=calendarId, ruleId=ruleId).execute()

        logging.info('acl delete ok ::calendarId:' + calendarId + ' ruleId:' + ruleId)
        # 各行書き込み
        w.writerow({'calendarId': calendarId,
                    'id': ruleId,
                    'result': 'OK'})
    except HttpError as error:
        logging.error(vars(error))
        errcontent = None
        if vars(error)['content'].decode('UTF-8') not in ['Not Found']:
            errcontent = json.loads(vars(error)['content'],encoding='UTF-8')['error']
        if errcontent != None and errcontent['errors'][0]['reason'] in ['cannotChangeOwnAcl']:
            w.writerow({'calendarId': calendarId,
                        'id': ruleId,
                       'result': 'NG:no access level'})
        else:
            w.writerow({'calendarId': '' if calendarId is None or len(calendarId) <= 0 else calendarId ,
                        'id': '' if ruleId is None or len(ruleId) <= 0 else ruleId,
                        'result': 'NG:else'})

def Process(name):
    global RESOURCE
    RESOURCE = name
    getProcess()

def getProcess():

    readList = getResource()
    doCheck(readList, EVENTKEY)
    logging.info('acl delete start')

    try:
        import argparse

        parser = argparse.ArgumentParser(parents=[tools.argparser])
        flags = parser.parse_args()
    except ImportError:
        flags = None

    # 認証情報を格納するディレクトリ「.credentials」の設定。ディレクトリが無い場合は作成
    credential_dir = os.path.join(os.path.expanduser('~'), '.test_credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    # 認証ファイルのパスを設定と読み込み
    credential_path = os.path.join(credential_dir, 'calendar_acl.json')
    store = Storage(credential_path)
    credentials = store.get()

    # 認証ファイルが無い場合は作成
    if not credentials or credentials.invalid:

        # 使用する機能の範囲を設定
        scopes = [
            SCOPES,
        ]

        # 認証キーの設定
        secret_dir = os.path.join(os.path.expanduser('~'), '.test_secrets')
        if not os.path.exists(secret_dir):
            os.makedirs(secret_dir)

        # 認証キーから認証処理を行うクラスのインスタンスを生成
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, scopes)

        # アプリケーションの名前
        flow.user_agent = APPLICATION_NAME

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Python 2.6　互換用処理
            credentials = tools.run(flow, store)
        logging.debug('証明書を保存しました： ' + credential_path)

    # 認証を行う
    http = credentials.authorize(httplib2.Http())
    app_admin_service = discovery.build('calendar', 'v3', http=http)

    csvf = open(CSVFILE, 'w')

    # 列の設定
    dictkey=DICTKEY

    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    logging.debug(readList)

    for readData in readList:
        readData = json.loads(readData, encoding='UTF-8')
        logging.debug(readData)

        # 各行書き込み
        getResourceData(app_admin_service, w, readData['calendarId'], readData['id'])

    csvf.close()

    logging.debug('acl delete End')

if __name__ == '__main__':
    Process('/var/www/html/mysite/rakumo/static/files/upload/acllist_20180228174057.csv')
