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
#CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret.json'
CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret_calendar.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
CSVFILE = '/var/www/html/mysite/rakumo/static/files/acl.csv'

DICTKEY = ['calendarId', 'kind', 'etag', 'id', 'scope_type', 'scope_value','role', 'result']
EVENTKEY = {'calendarId', 'kind', 'etag', 'id', 'scope_type', 'scope_value','role'}

logging = init('aclAdd')

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

def getResourceData(service, w, calendarId, EVENT):
    logging.info('Getting the first 10 acls in the domain')
    
    try:
        response = service.acl().insert(calendarId=calendarId,sendNotifications=False,body=EVENT).execute()

        logging.info(response)
        if not response:
            logging.info('No acl in the domain.')

        else:
            logging.info('get resource.')

            # 各行書き込み
            w.writerow({'calendarId': calendarId,
                        'scope_type': response['scope']['type'],
                        'scope_value': response['scope']['value'],
                        'role': response['role'],
                        'result': 'OK'})
    except HttpError as error:
        logging.error(vars(error))
        errcontent = None
        if vars(error)['content'].decode('UTF-8') not in ['Not Found']:
            errcontent = json.loads(vars(error)['content'],encoding='UTF-8')['error']
        if errcontent != None and errcontent['errors'][0]['reason'] in ['cannotChangeOwnAcl']:
            w.writerow({'calendarId': calendarId,
                        'scope_type': EVENT['scope']['type'],
                        'scope_value': EVENT['scope']['value'],
                        'role': EVENT['role'],
                        'result': 'NG:no access level'})
        else:
            w.writerow({'calendarId': calendarId,
                        'scope_type': EVENT['scope']['type'],
                        'scope_value': EVENT['scope']['value'],
                        'role': EVENT['role'],
                        'result': 'NG:else'})

def Process(name):
    global RESOURCE
    RESOURCE = name
    getProcess()

def getProcess():

    readList = getResource()
    doCheck(readList, EVENTKEY)
    logging.info('acl Add start')

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

    for readData in readList:
        readData = json.loads(readData, encoding='UTF-8')
        logging.debug(readData)

        event = {
            'role': readData['role'],
            'scope': {
                'type': readData['scope_type'],
                'value': readData['scope_value']
            }
        }
        # 各行書き込み
        getResourceData(app_admin_service, w, readData['calendarId'], event)

    csvf.close()

    logging.info('acl Add End')

if __name__ == '__main__':
    Process('/var/www/html/mysite/rakumo/static/files/upload/acllist_20180228174057.csv')
