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

DICTKEY = ['calendarId', 'kind', 'etag', 'id', 'scope_type', 'scope_value','role']
EVENTKEY = {'calendarId'}

logging = init('acl')

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

def getResourceData(service, w, calendarId, pagetoken, http):
    logging.info('Getting the first 10 acls in the domain')
    
    try:
        resourcedatas = service.acl().list(calendarId=calendarId, pageToken=pagetoken).execute()

        logging.info(resourcedatas)
        if not resourcedatas:
            logging.info('No acl in the domain.')

        else:
            logging.info('get acl list.')
            if 'nextPageToken' in resourcedatas:
                pagetoken = resourcedatas['nextPageToken']
            else:
                pagetoken = None

            # 各行書き込み
            for data in resourcedatas['items']:
                w.writerow({'calendarId': calendarId,
                            'kind': data['kind'],
                            'etag': data['etag'],
                            'id': data['id'],
                            'scope_type': data['scope']['type'],
                            'scope_value': data['scope']['value'],
                            'role': data['role']})
    except HttpError as error:
        logging.error(vars(error))
        errcontent = json.loads(vars(error)['content'],encoding='UTF-8')['error']
        if errcontent['errors'][0]['reason'] in ['notFound']:
            w.writerow({'calendarId': calendarId,
                        'kind': 'notFound',
                        'etag': '',
                        'id': '',
                        'scope_type': '',
                        'scope_value': '',
                        'role': ''})

    return pagetoken

def Process(name):
    global RESOURCE
    RESOURCE = name
    getProcess()

def getProcess():

    readList = getResource()
    doCheck(readList, EVENTKEY)
    logging.info('acl list start')

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
        pagetoken = None
        cnt = 0
        while cnt < 20:
            pagetoken = getResourceData(app_admin_service, w, readData['calendarId'], pagetoken, http)
            if pagetoken is None:
                break
            cnt = cnt+1

    csvf.close()

    logging.info('acl list End')

if __name__ == '__main__':
    Process('/var/www/html/mysite/rakumo/static/files/upload/acllist_20180228174057.csv')
