### ユーザーのデータを取ってくるやつや
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import csv
import codecs

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'
CLIENT_SECRET_FILE = './json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
CSVFILE = '/var/www/html/mysite/rakumo/static/files/user.csv'
DICTKEY = ['primaryEmail', 'fullName']


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'admin-directory_v1-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def getUserData(service, dictkey, csvf, w, pagetoken):
    print('Getting the first 10 users in the domain')
    #results = service.users().list(customer='my_customer', maxResults=10,orderBy='email').execute()
    results = service.users().list(customer='my_customer', orderBy='email', pageToken=pagetoken).execute()
    users = results.get('users', [])

    if not users:
        print('No users in the domain.')

    else:
        print('get user.')
        if 'nextPageToken' in results:
            pagetoken = results['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for user in users:
            w.writerow({'primaryEmail':user['primaryEmail'],'fullName':user['name']['fullName']})

    return pagetoken

def Process():
    getProcess()

def getProcess():

    """Shows basic usage of the Google Admin SDK Directory API.
    Creates a Google Admin SDK API service object and outputs a list of first
    10 users in the domain.
    """
    # 認証
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('admin', 'directory_v1', http=http)

    # ファイル設定
    dictkey = DICTKEY
    csvf = codecs.open(CSVFILE, 'w')
    w = csv.DictWriter(csvf, dictkey)  # キーの取得
    w.writeheader()  # ヘッダー書き込み

    # 各行書き込み
    pagetoken = None
    cnt = 0
    # 限界2000件まで取ってくる
    while cnt < 20:
        print(service)
        pagetoken = getUserData(service, dictkey, csvf, w, pagetoken)
        if pagetoken is None:
            break
        cnt = cnt+1

        # results = service.users().list(customer='my_customer', orderBy='email', pageToken=pagetoken).execute()

    csvf.close()
    print('csv_writer_End')

#if __name__ == '__main__':
#    main()
