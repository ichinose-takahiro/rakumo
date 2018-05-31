from __future__ import print_function
import httplib2
import os
import datetime
import json
import csv
from pytz import timezone

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from loginglibrary import init
WORKDIR = '/var/www/html/mysite/rakumo/'
RESOURCE = WORKDIR + '/static/files/resource.csv'
logging = init('calendarCheck')

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.send'
]
#CLIENT_SECRET_FILE = '../json/client_secret.json'
CLIENT_SECRET_FILE = '/var/www/html/mysite/rakumo/json/client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'
DELETEDAY = 7

def getResource():
    u""" getResource 会議室データを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    resourceData = csvToJson(RESOURCE)
    return resourceData

def getResourceAddress():
    u""" getResourceAddress 会議室メールアドレス取得
    カレンダーデータから会議室データをチェックしてアドレスを抽出します
    :param data: カレンダーデータ
    :return: 会議室データのメールアドレス
    """
    ret = []
    for resourceData in getResource():
        resourceData = json.loads(resourceData,encoding='UTF-8')
        ret.append({'name':resourceData['generatedResourceName'], 'address':resourceData['resourceEmail']})

    return ret
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
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'googleapis.com-python-sheets-cal.json')

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

def getCalendarData(http):

    cal_service = discovery.build('calendar', 'v3', http=http)
    #now(timezone('UTC')
    #now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    now = (datetime.datetime.utcnow() + datetime.timedelta(days=90) + datetime.timedelta(hours=9)).isoformat() + 'Z'
    print(now)
    print('Getting the upcoming 10 events')
    returnEvents = []
    for resource in getResourceAddress():
        logging.debug(resource['name'])
        eventsResult = cal_service.events().list(
            calendarId=resource['address'], maxResults=250 , timeMin=now, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])
        #print(events)
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'summary' in event:
                returnEvents.append([resource['name'],start, event['summary']])
            else:
                returnEvents.append([resource['name'],start, 'なし'])
    #if not events:
    #    logging.debug('No upcoming events found.')

    return returnEvents

def deleteSheets(deleteSheetId,service,spreadsheetId):
    batch_delete_request_body = {
      "requests": [
        {
          "deleteSheet": {
            "sheetId": deleteSheetId
          }
        }
      ]
    }
    request_s = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId,
                                                   body=batch_delete_request_body)
    request_s.execute()
def createSheet(today, service, spreadsheetId):

    batch_update_request_body = {
      "requests": [
        {
          "addSheet": {
            "properties": {
              "title": today,
              "gridProperties": {
                "rowCount": 20,
                "columnCount": 12
              },
              "tabColor": {
                "red": 1.0,
                "green": 0.3,
                "blue": 0.4
              }
            }
          }
        }
      ]
    }
    request_s = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId,
                                                          body=batch_update_request_body)
    res = request_s.execute()
    logging.debug(res)

def updateSheets(http, events):
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1Rcb8RYkzXCgVcVRCQOfnhYNZeUDEhPz2dk55_8MX0Ag'
    #rangeName = 'sheet1'
    #result = service.spreadsheets().values().get(
    #    spreadsheetId=spreadsheetId, range=rangeName).execute()
    #values = result.get('values', [])

    #if not values:
    #    print('No data found.')
    #else:
    #    print('Name, Major:')
    #    for row in values:
    #        # Print columns A and E, which correspond to indices 0 and 4.
    #        print(row)

    # The ID of the spreadsheet to update.
    # spreadsheet_id = 'my-spreadsheet-id'  # TODO: Update placeholder value.

    #シートデータを取得
    request = service.spreadsheets().get(spreadsheetId=spreadsheetId)
    getData = request.execute()
    sheetsData = getData['sheets']

    today = datetime.date.today().strftime("%Y%m%d")
    todaydelta = (datetime.date.today() - datetime.timedelta(days=DELETEDAY)).strftime("%Y%m%d")
    logging.debug(today)
    logging.debug(todaydelta)
    # 一回取得した当日と過去7日以前のシートを削除
    for sheet in sheetsData:
        if int(todaydelta) >= int(sheet['properties']['title']) or int(today) == int(sheet['properties']['title']):
            logging.debug("%s %s",sheet['properties']['sheetId'],sheet['properties']['title'])
            deleteSheets(sheet['properties']['sheetId'], service, spreadsheetId)
            logging.debug('シート「' + sheet['properties']['title'] + '」を削除しました')

    #新たに当日のシートを作成
    createSheet(today, service, spreadsheetId)

    # 施設毎に追加する
    batch_update_values_request_body = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {
                "range": today + "!A1",
                "majorDimension": "ROWS",
                "values": events
            },
        ]
    }

    request = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId,
                                                          body=batch_update_values_request_body)
    return request.execute()

def sendMail(data):
    return None

def main():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())

    # カレンダーデータを取得
    events = getCalendarData(http)

    #print(events)
    #events = ''
    #スプレッドシートに追記
    response = updateSheets(http, events)

    # TODO: Change code below to process the `response` dict:
    print(response)

    # メール送信
    sendMail(response)


if __name__ == '__main__':
    main()
