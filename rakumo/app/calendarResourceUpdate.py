# 施設データを取ってくるやつや
import os
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from .checkList import doCheck
from .loginglibrary import init
import csv
import json

logging = init('resourceUpdate')

WORKDIR = '/var/www/html/googleapi'
#RESOURCE = WORKDIR + '/data/updateResource_1221.csv'
RESOURCE = ''
EVENTKEY = {'resourceId','resourceName','generatedResourceName','resourceType'}

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

def getResourceData(service):
    upDateList = getResource()
    doCheck(upDateList, EVENTKEY)

    for upDataData in upDateList:
        upDataData = json.loads(upDataData,encoding='UTF-8')
        EVENT = {"resourceId":upDataData['resourceId'],
                 "resourceName":upDataData['resourceName'],
                 "generatedResourceName": upDataData['generatedResourceName'],
                 "resourceType":upDataData['resourceType']}
#        EVENT['resourceId'] = upDataData['resourceId']
#        EVENT['resourceName'] = upDataData['resourceName']
#        EVENT['generatedResourceName'] = upDataData['generatedResourceName']
        resourcedatas = service.resources().calendars().update(customer='my_customer', calendarResourceId='appsadmin@919.jp', body=EVENT).execute()
        logging.info(resourcedatas)
        logging.info(upDataData['resourceId'] + ':update!')

def Process(name):
    global RESOURCE
    RESOURCE = name
    getProcess()

def getProcess():

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
    credential_path = os.path.join(credential_dir, 'admin-directory_v1_test.json')
    store = Storage(credential_path)
    credentials = store.get()

    # 認証ファイルが無い場合は作成
    if not credentials or credentials.invalid:

        # 使用する機能の範囲を設定
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.resource.calendar',
        ]

        # 認証キーの設定
        secret_dir = os.path.join(os.path.expanduser('~'), '.test_secrets')
        if not os.path.exists(secret_dir):
            os.makedirs(secret_dir)

        # 認証キーから認証処理を行うクラスのインスタンスを生成
        # flow = client.flow_from_clientsecrets(
        #     os.path.join(secret_dir, 'client_secret_test.json'), scopes)

        flow = client.flow_from_clientsecrets( '../json/client_secret.json', scopes)

        # アプリケーションの名前
        flow.user_agent = 'User register Test Tool'

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Python 2.6　互換用処理
            credentials = tools.run(flow, store)
        logging.info('証明書を保存しました： ' + credential_path)

    # 認証を行う
    http = credentials.authorize(httplib2.Http())
    app_admin_service = discovery.build('admin', 'directory_v1', http=http)

    getResourceData(app_admin_service)

if __name__ == '__main__':
    Process()
