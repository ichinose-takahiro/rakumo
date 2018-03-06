
u"""
グループのデータを作成
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
import json

logging = init('groupInsert')

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/admin.directory.group'
CLIENT_SECRET_FILE = '/var/www/html/googleapi/json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
WORKDIR = '/var/www/html/googleapi'
GROUPLIST = WORKDIR + '/data/groupsInsrtList_0116_2.csv'

def getGroups():
    u""" getResource 会議室データを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    resourceData = csvToJson(GROUPLIST)
    return resourceData
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

def insertData(service):

    insertList = getGroups()

    for insrtData in insertList:
        insrtData = json.loads(insrtData, encoding='UTF-8')

        EVENT = {"email": insrtData['email'],
                 "name": insrtData['name'],
                 "description": insrtData['description'],
                 "nonEditableAliases": insrtData['nonEditableAliases']}
        print(EVENT)
        resourcedatas = service.groups().insert(body=EVENT).execute()
        logging.debug(resourcedatas)
        logging.info(insrtData['email'] + ':insert!')

def main():

    """Shows basic usage of the Google Admin SDK Directory API.
    Creates a Google Admin SDK API service object and outputs a list of first
    10 users in the domain.
    """
    # 認証
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('admin', 'directory_v1', http=http)

    insertData(service)

if __name__ == '__main__':
    main()