
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
import csv
import codecs
import httplib2
import json

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
    print('Failed to post request to [{}] due to: {}').format(url, e)
 return json.loads(content)


def getUserData(service, w, pagetoken, http):
    print('Getting the first 10 users in the domain')
    #results = service.users().list(customer='my_customer', maxResults=10,orderBy='email').execute()
    results = service.groups().list(customer='my_customer', pageToken=pagetoken).execute()
    groups = results.get('groups', [])
    print(results)
    if not groups:
        print('No users in the domain.')

    else:
        print('get user.')
        if 'nextPageToken' in results:
            pagetoken = results['nextPageToken']
        else:
            pagetoken = None

        # 各行書き込み
        for group in groups:
            tresult = get_group_members(group, http)

            if 'members' in tresult.keys():
                members = tresult['members']
                print('------------')
                for member in members:
                    print(group['name'])
                    print(member)
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

def main():

    """Shows basic usage of the Google Admin SDK Directory API.
    Creates a Google Admin SDK API service object and outputs a list of first
    10 users in the domain.
    """
    # 認証
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('admin', 'directory_v1', http=http)

    # ファイル設定
    dictkey = ['groupId','groupEmail','groupName','groupMemberCnt', 'memberId','memberEmail','memberRole','memberType','memberStatus']
    csvf = codecs.open('/var/www/html/googleapi/data/groupsMember_0117.csv', 'w')
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
    print('csv_writer_End')

if __name__ == '__main__':
    main()