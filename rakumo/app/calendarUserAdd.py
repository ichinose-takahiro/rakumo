### ユーザーのデータを取ってくるやつや
from __future__ import print_function
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import csv
import json

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/admin-directory_v1-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'
CLIENT_SECRET_FILE = '../json/client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'
WORKDIR = '/var/www/html/googleapi'
RESOURCE = WORKDIR + '/data/addUser.csv'

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

def getRequestBody(userList):
    BODY = {}
    BODY['password'] = userList['password']
    BODY['primaryEmail'] = userList['mailAddress']
    BODY['name'] = {'familyName':userList['sei'], 'givenName': userList['mei']}
    return BODY

def insertUserData(service):
    print('Getting the first 10 users in the domain')
    ## 作成するユーザー情報を取得
    userList = getResource()
    for upDataData in userList:
        userList = json.loads(upDataData,encoding='UTF-8')
        BODY = getRequestBody(userList)
        results = service.users().insert(body=BODY).execute()
        print(results['primaryEmail'] + ':add!')

def main():

    """Shows basic usage of the Google Admin SDK Directory API.
    Creates a Google Admin SDK API service object and outputs a list of first
    10 users in the domain.
    """
    # 認証
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('admin', 'directory_v1', http=http)

    insertUserData(service)

    print('userAdd_End')

if __name__ == '__main__':
    main()