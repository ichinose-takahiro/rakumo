# 施設データを取ってくるやつや
import os
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from loginglibrary import init
import csv
import datetime
from pytz import timezone

WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = './json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
TODAY = datetime.datetime.now(timezone('Asia/Tokyo')).strftime("%Y%m%d%H%M%S")
CSVFILE = WORKDIR + 'calendarList_'+TODAY+'_api.csv'
DICTKEY =['kind','etag','id','status','htmlLink','created','updated','summary',
          'description','location','colorId','creator','organizer','start','end',
          'endTimeUnspecified','recurrence','recurringEventId','originalStartTime','transparency',
          'visibility','iCalUID','sequence','attendees','attendeesOmitted','extendedProperties',
          'hangoutLink','conferenceData','gadget','anyoneCanAddSelf','guestsCanInviteOthers',
          'guestsCanModify','guestsCanSeeOtherGuests','privateCopy','locked','reminders','source','attachments']
logging = init('calendarList')
##DEBUG_ONLY
USERADDRESS = [    'tobaru-hideyasu@919.jp','nishiyama-kohei@919.jp','inomata-toshiyuki@919.jp','takubo-hidenori@919.jp','koike-akihiro@919.jp',    'morimoto-hikaru@919.jp','sato-manami@919.jp','kan-sayuri@919.jp','mikami-takashi@919.jp','hama-yasuki@919.jp',    'hirata-naomi@919.jp','shiga-sakurako@919.jp','komagata-yukino@919.jp','kitabatake-yoshimi@919.jp','kaneda-yoko@919.jp',    'kimura-satoko@919.jp','noma-chinami@919.jp','kasai-kazuaki@919.jp','suzuki-yugo@919.jp','isomoto-miho@919.jp',    'nihonmatsu-yumeko@919.jp','saito-takamitsu@919.jp','iwasaki-sanae@919.jp','matsushita-atsushi@919.jp','matsumura-shun@919.jp',    'matsubara-kosuke@919.jp','miyamoto-tomomi@919.jp','horino-shunya@919.jp','hogan-nobutaka@919.jp','ishida-yuko@919.jp',    'yamaoka-yuina@919.jp','sato-sora@919.jp','ogawa-yoshiteru@919.jp','yoshida-hiroshi@919.jp','karasu-mikiko@919.jp',
    'yamada-ryohei@919.jp','sakamoto-ayako@919.jp','nomura-miku@919.jp','nakahira-shinya@919.jp'
]
##DEBUG_ONLY

def getApiData(service, dictkey, csvf, w, pagetoken, calendarId):
    logging.debug('Getting the first 10 data in the domain')
    #results = service.users().list(customer='my_customer', maxResults=10,orderBy='email').execute()
    #results = service.users().list(customer='my_customer', orderBy='email', pageToken=pagetoken).execute()


    calendarList = service.events().list(calendarId=calendarId, pageToken=pagetoken, maxResults=2500).execute()

    if not calendarList:
        logging.debug('No calendar in the domain.')

    else:
        logging.debug('get calendar.')
        if 'nextPageToken' in calendarList:
            pagetoken = calendarList['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for target_dict in calendarList['items']:
            w.writerow(target_dict)

    return pagetoken

def main():

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
    credential_path = os.path.join(credential_dir, 'python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()

    # 認証ファイルが無い場合は作成
    if not credentials or credentials.invalid:

        # 使用する機能の範囲を設定
        scopes = [
            SCOPES,
        ]

        # 認証キーの設定
        secret_dir = os.path.join(os.path.expanduser('~'), '.test_credentials')
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
    CAL = discovery.build('calendar', 'v3', http=http)

    csvf = open(CSVFILE, 'w')

    # 列の設定
    dictkey=DICTKEY

    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    # 各行書き込み
    pagetoken = None
    cnt = 0
    for address in USERADDRESS:
        while cnt < 10000:
            pagetoken = getApiData(CAL, dictkey, csvf, w, pagetoken, address)
            if pagetoken is None:
                break
            cnt = cnt+1
    logging.debug('csv_writer_start')




    # 各行書き込み
    #for target_dict in resourcedatas['items']:
    #    w.writerow(target_dict)

        # print(target_dict['resourceName'])
        # print(target_dict['resourceEmail'])
        # print(target_dict)

    csvf.close()

    logging.debug('csv_writer_End')

if __name__ == '__main__':
    main()
