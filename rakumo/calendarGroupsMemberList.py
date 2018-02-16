
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
from .loginglibrary import init as loginit
import csv
import codecs
import httplib2
import json

loging = loginit('groupmem')
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
CSVFILE = '/var/www/html/mysite/rakumo/static/files/groupMember.csv'
DICTKEY = ['groupId','groupEmail','groupName','groupMemberCnt', 'memberId','memberEmail','memberRole','memberType','memberStatus']


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
        loging.debug('Storing credentials to ' + credential_path)
    return credentials

def get_group_members(group, http):
    url = 'https://www.googleapis.com/admin/directory/v1/groups/{}/members'.format(group['email'])
    return call_google_api("GET", url, http)

def add_group_member(group, http, payload=False):
    url = 'https://www.googleapis.com/admin/directory/v1/groups/{}/members'.format(group)
    return call_google_api("POST", url, payload, http)

def call_google_api(method, url,http ,payload=False):
 content = {}
 try:
     if payload:
        (resp, content) = http.request(uri=url, method=method, body=urlencode(payload))
     else:
        (resp, content) = http.request(uri=url, method=method)
 except Exception as e:
     loging.debug('Failed to post request to [{}] due to: {}').format(url, e)
 return json.loads(content)


def getUserData(service, w, pagetoken, http):
    results = service.groups().list(customer='my_customer', pageToken=pagetoken).execute()
    loging.info(results)
    groups = results.get('groups', [])
    loging.debug(results)
    if not groups:
        loging.info('No users in the domain.')

    else:
        if 'nextPageToken' in results:
            pagetoken = results['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for group in groups:
            tresult = get_group_members(group, http)

            if 'members' in tresult.keys():
                members = tresult['members']
                loging.debug('------------')
                for member in members:
                    loging.debug(group['name'])
                    loging.debug(member)
                    rowMember = {
                        'groupId': group['id'],
                        'groupEmail': group['email'],
                        'groupName': group['name'],
                        'groupMemberCnt':group['directMembersCount'],
                        'memberId':member['id'],
                        'memberEmail': member['email'] if 'email' in member.keys() else '',
                        'memberRole': member['role'],
                        'memberType': member['type'],
                        'memberStatus': member['status'],
                    }
                    w.writerow(rowMember)
            else:
                loging.debug(group['name'])
                loging.debug(member)
                rowMember = {
                    'groupId': group['id'],
                    'groupEmail': group['email'],
                    'groupName': group['name'],
                    'groupMemberCnt': group['directMembersCount'],
                    'memberId': '',
                    'memberEmail': '',
                    'memberRole': '',
                    'memberType': '',
                    'memberStatus': '',
                }
                w.writerow(rowMember)

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
        pagetoken = getUserData(service, w, pagetoken, http)
        if pagetoken is None:
            break
        cnt = cnt+1

    csvf.close()
    loging.debug('csv_writer_End')

if __name__ == '__main__':
    getProcess()
