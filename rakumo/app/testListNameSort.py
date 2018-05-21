# -*- coding: utf-8 -*-
# テスト用に、ユーザーネームを置き換える
from __future__ import print_function
from loginglibrary import init
import csv
import json
import sys
import pandas as pd

WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
#CALENDARCSV = WORKDIR + '180206_GroupSession_edit.csv'
#CALENDARCSV = WORKDIR + '180206_GroupSession_edit_change_20180312.csv'
#CALENDARCSV = WORKDIR + '180314_GroupSession_change.csv'
#CALENDARCSV = WORKDIR + '180314_GroupSession_change_wpd.csv'
CALENDARCSV = WORKDIR + 'GroupSession_20180512_10_sort.csv'
#CSVFILE = WORKDIR + '180206_GroupSession_edit_change_20180313_r.csv'
#CSVFILE = WORKDIR + '180314_GroupSession_change_r.csv'
#CSVFILE = WORKDIR + '180314_GroupSession_change_wpd_r.csv'
CSVFILE = WORKDIR + 'GroupSession_20180513_10_sort_prd.csv'
logging = init('testlist')

def getcalendarData():
    u""" getcalendarData カレンダーデータを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(CALENDARCSV)
    return calendarData

"CSVを読み込みJSON化する"
def csvToJson(csvData):
    jsonData = []
    with open(csvData, 'r',encoding='utf_8', errors='ignore', newline='') as f:
        for line in csv.DictReader(f):
            line_json = json.dumps(line, ensure_ascii=False)
            jsonData.append(line_json)
    return jsonData
def progress(p, l):
    sys.stdout.write("\r%d / 100" %(int(p * 100 / (l - 1))))
    sys.stdout.flush()
def Process():
    getProcess()

def getProcess():
    cnt = 0

    # カレンダーデータを取得
    #clList = getcalendarData()
    clList = pd.read_csv(CALENDARCSV, index_col='SCD_SID')
    logging.debug('------------start----------')
    # 列の設定
    dictkey=['SCD_SID','SCD_RSSID','SCE_SID','SCD_GRP_SID','SUMMARY','DESCRIPTION','BIKO','COLORID','RESOURCE','SCD_DAILY','STARTDATE','ENDDATE','SEI','MEI','PRISEI','PRIMEI','PUBLICFLG','EDITFLG','BYDAY_SU','BYDAY_MO','BYDAY_TU','BYDAY_WE','BYDAY_TH','BYDAY_FR','BYDAY_SA','SCE_DAY','SCE_WEEK','SCE_DAILY','SCE_MONTH_YEARLY','SCE_DAY_YEARLY']
    csvf = open(CSVFILE, 'w')
    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    #clList = sorted(clList, key=lambda x:(x[14], x[15], x[0], x[3], x[2]))
    #clList = sorted(clList, key=lambda x:(x[15]))
    clList = clList.sort_index()
    clList = clList.sort_values(['PRISEI', 'PRIMEI', 'SCD_GRP_SID', 'SCE_SID'])
    #clList = clList.values.tolist()
    #for clData in clList:
    #    logging.debug(clData)
        #clData = json.loads(clData,encoding='UTF-8')

    #    w.writerow(clData)
    #    cnt = cnt + 1
    #    progress(cnt-1, len(clList))
    #csvf.close()
    clList.to_csv(CSVFILE)
    #progress(cnt - 1, len(clList))
    logging.debug('-----------End---------------')

if __name__ == '__main__':
    Process()


