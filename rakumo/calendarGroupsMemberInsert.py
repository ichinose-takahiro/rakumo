
u"""
グループに所属するメンバーを登録します。
"""
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from .checkList import doCheck
from oauth2client.file import Storage
import csv
import json
import urllib.parse
from .loginglibrary import init

logging = init('groupmemberInsert')

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/admin.directory.group'
CLIENT_SECRET_FILE = './json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
#WORKDIR = '/var/www/html/googleapi'
#GROUPLIST = WORKDIR + '/data/groupsMemberInsrtList_0117.csv'
RESOURCE = ''
EVENTKEY = {'groupKey','memberKey'}


def getGroups():
    u""" getResource 会議室データを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    resourceData = csvToJson(RESOURCE)
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
        print('Storing credentials to ' + credential_path)
    return credentials

def get_group_members(group, http):
    url = 'https://www.googleapis.com/admin/directory/v1/groups/{}/members'.format(group['groupKey'])
    payload = {'email':group['memberKey'],'role':'MEMBER'}
    return call_google_api("POST", url, payload, http)

def call_google_api(method, url,payload,http):
    content = {}
    try:
        (resp, content) = http.request(uri=url, method=method, body=json.dumps(payload),
                                       headers={'Content-type': 'application/json'})
    except Exception as e:
        print('Failed to post request to [{}] due to: {}').format(url, e)
    if resp['status'] == '200':
        print(payload['email']+':insert!')
    else:
        print(payload['email']+':NG!')

def insertData(service, http):

    groupList = getGroups()
    doCheck(groupList, EVENTKEY)

    for group in groupList:

        group = json.loads(group, encoding='UTF-8')
        tresult = get_group_members(group, http)
        print('insert!')

def Process(name):
    global RESOURCE
    RESOURCE = name
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

    insertData(service, http)
    print('csv_writer_End')

if __name__ == '__main__':
    Process()