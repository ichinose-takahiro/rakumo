# 施設データを取ってくるやつや
import os
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from .loginglibrary import init
import csv

SCOPES = 'https://www.googleapis.com/auth/admin.directory.resource.calendar'
CLIENT_SECRET_FILE = './json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
CSVFILE = '/var/www/html/mysite/rakumo/static/files/resource.csv'
DICTKEY = ['kind', 'etags', 'resourceId', 'resourceName', 'generatedResourceName',
             'resourceType', 'resourceDescription', 'resourceEmail', 'resourceCategory',
             'userVisibleDescription','capacity']

logging = init('resource')

def getResourceData(service, dictkey, csvf, w, pagetoken):
    logging.debug('Getting the first 10 users in the domain')
    #results = service.users().list(customer='my_customer', maxResults=10,orderBy='email').execute()
    #results = service.users().list(customer='my_customer', orderBy='email', pageToken=pagetoken).execute()


    resourcedatas = service.resources().calendars().list(customer='my_customer', pageToken=pagetoken).execute()

    if not resourcedatas:
        logging.debug('No resources in the domain.')

    else:
        logging.debug('get resource.')
        if 'nextPageToken' in resourcedatas:
            pagetoken = resourcedatas['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for target_dict in resourcedatas['items']:
            w.writerow(target_dict)

    return pagetoken

def Process():
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
            SCOPES,
        ]

        # 認証キーの設定
        secret_dir = os.path.join(os.path.expanduser('~'), '.test_secrets')
        if not os.path.exists(secret_dir):
            os.makedirs(secret_dir)

        # 認証キーから認証処理を行うクラスのインスタンスを生成
        # flow = client.flow_from_clientsecrets(
        #     os.path.join(secret_dir, 'client_secret_test.json'), scopes)

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
    app_admin_service = discovery.build('admin', 'directory_v1', http=http)

    csvf = open(CSVFILE, 'w')

    # 列の設定
    dictkey=DICTKEY

    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    # 各行書き込み
    pagetoken = None
    cnt = 0
    while cnt < 20:
        pagetoken = getResourceData(app_admin_service, dictkey, csvf, w, pagetoken)
        if pagetoken is None:
            break
        cnt = cnt+1
#    resourcedatas = app_admin_service.resources().calendars().list(customer='my_customer').execute()
    # print(resourcedatas)
    logging.debug('csv_writer_start')




    # 各行書き込み
    #for target_dict in resourcedatas['items']:
    #    w.writerow(target_dict)

        # print(target_dict['resourceName'])
        # print(target_dict['resourceEmail'])
        # print(target_dict)

    csvf.close()

    logging.debug('csv_writer_End')

#if __name__ == '__main__':
#    main()