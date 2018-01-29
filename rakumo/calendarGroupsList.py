
u"""
グループのデータを取ってくるやつや
"""
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from .loginglibrary import init
import csv
import codecs


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

logging = init()

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/admin.directory.group'
CLIENT_SECRET_FILE = './json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
CSVFILE = '/var/www/html/mysite/rakumo/static/files/groups.csv'
DICTKEY = ['kind','id','etag','email','name','directMembersCount','description','adminCreated','nonEditableAliases','aliases']

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials_groups')
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
        logging.debug('Storing credentials to ' + credential_path)
    return credentials

def getUserData(service, w, pagetoken):
    logging.debug('Getting the first 10 Group in the domain')
    #results = service.users().list(customer='my_customer', maxResults=10,orderBy='email').execute()
    results = service.groups().list(customer='my_customer', pageToken=pagetoken).execute()
    groups = results.get('groups', [])

    if not groups:
        logging.debug('No users in the domain.')

    else:
        logging.debug('get group.')
        if 'nextPageToken' in results:
            pagetoken = results['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for group in groups:
            if group['name'] == '東京紹介部':
                logging.debug(group)
            w.writerow(group)

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
        pagetoken = getUserData(service, w, pagetoken)
        if pagetoken is None:
            break
        cnt = cnt+1

    csvf.close()
    logging.debug('csv_writer_End')
#
#if __name__ == '__main__':
#    main()
