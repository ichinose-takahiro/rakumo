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
#CALENDARCSV = WORKDIR + '180416_GroupSession_change_ssp_2.csv'
#CALENDARCSV = WORKDIR + '180426_GroupSession_change_ssp_3.csv'
#CALENDARCSV = WORKDIR + '180512_GroupSession_change.csv'
CALENDARCSV = WORKDIR + 'GroupSession_20180512.csv'
#CALENDARCSV = WORKDIR + 'GroupSession_20180413.csv'
#CSVFILE = WORKDIR + '180206_GroupSession_edit_change_20180313_r.csv'
#CSVFILE = WORKDIR + '180314_GroupSession_change_r.csv'
#CSVFILE = WORKDIR + '180314_GroupSession_change_wpd_r.csv'
#CSVFILE = WORKDIR + '180426_GroupSession_change_ssp_3_sort.csv'
#CSVFILE = WORKDIR + '180512_GroupSession_change_sort.csv'
CSVFILE = WORKDIR + 'GroupSession_20180512_10_sort.csv'
#CSVFILE = WORKDIR + 'GroupSession_20180413_sort.csv'
logging = init('testlist')

STR_ONE = '1'
STR_ZERO = '0'
STR_MONE = '-1'

def checkExData(clData):
    u""" checkExData 繰り返しデータの存在チェック
    カレンダーデータが繰り返し登録するデータかをチェックします。
    :param clData: カレンダーデータ
    :return: 繰り返し登録アリ True、繰り返し登録なし False
    """
    ret = False
    if clData['SCE_SID'] != STR_MONE:
        if clData['BYDAY_SU'] == STR_ONE or clData['BYDAY_MO'] == STR_ONE or \
            clData['BYDAY_TU'] == STR_ONE or \
            clData['BYDAY_WE'] == STR_ONE or \
            clData['BYDAY_TH'] == STR_ONE or \
            clData['BYDAY_FR'] == STR_ONE or \
            clData['BYDAY_SA'] == STR_ONE or \
            clData['SCE_DAY'] != STR_ZERO or \
            clData['SCE_WEEK'] != STR_ZERO or \
            clData['SCE_DAILY'] != STR_ZERO or \
            clData['SCE_MONTH_YEARLY'] != STR_ZERO or \
            clData['SCE_DAY_YEARLY'] != STR_ZERO:
            ret = True
    return ret

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

    priOrgnizerFlg = False
    kurikaesiList = []
    eid = ''
    gid = ''
    sid = ''
    cnt = 0
    priSei = None
    priMei = None
    #clList = sorted(clList, key=lambda x:(x[14], x[15], x[0], x[3], x[2]))
    #clList = sorted(clList, key=lambda x:(x[15]))
    clList = clList.sort_index()
    clList = clList.sort_values(['PRISEI', 'PRIMEI', 'SCD_GRP_SID', 'SCE_SID'])
    #clList = clList.values.tolist()
    clList.to_csv(CSVFILE)
    clList = csvToJson(CSVFILE)

    for clData in clList:
        logging.debug(clData)
        clData = json.loads(clData,encoding='UTF-8')

        if (gid == clData['SCD_GRP_SID'] and clData['SCD_GRP_SID'] != '-1') or (checkExData(clData) == True and clData['SCE_SID'] != '-1' and eid == clData['SCE_SID']):
            
            # 管理者が参加者になっていない場合は、rakumoの管理者からも外す(登録してしまうため)
            if (clData['PRISEI']+clData['PRIMEI']) != (clData['SEI']+clData['MEI']):
                priSei = clData['SEI']
                priMei = clData['MEI']
            else:
                priOrgnizerFlg = True

            #gid = clData['SCD_GRP_SID']
            #eid = clData['SCE_SID']
            #sid = clData['SCD_SID']
            kurikaesiList.append(clData)
            #cnt = cnt + 1
            #progress(cnt-1, len(clList))
            #continue
        else:
            
            # 管理者が参加者になっていない場合は、rakumoの管理者からも外す(登録してしまうため)                    
            if kurikaesiList != []:
               for kurikaesiRow in kurikaesiList:
                   if priOrgnizerFlg == False:
                       logging.debug('---------------------------------')
                       logging.debug('PRISEI:'+priSei+' PRIMEI:'+priMei)
                       kurikaesiRow['PRISEI'] = priSei
                       kurikaesiRow['PRIMEI'] = priMei
                       logging.debug(kurikaesiRow)
                       logging.debug('---------------------------------')
                   w.writerow(kurikaesiRow)
                   cnt = cnt + 1
                   progress(cnt-1, len(clList))
               priSei = None
               priMei = None
               priOrgnizerFlg = False
               kurikaesiList = []

            # 管理者が参加者になっていない場合は、rakumoの管理者からも外す(登録してしまうため)
            if (clData['PRISEI']+clData['PRIMEI']) != (clData['SEI']+clData['MEI']):
               priSei = clData['SEI']
               priMei = clData['MEI']
            else:
               priOrgnizerFlg = True
            kurikaesiList.append(clData)

        gid = clData['SCD_GRP_SID']
        eid = clData['SCE_SID']
        sid = clData['SCD_SID']

    #最後の分
    if kurikaesiList != []:
       for kurikaesiRow in kurikaesiList:
           if priOrgnizerFlg == False:
               logging.debug('---------------------------------')
               logging.debug('PRISEI:'+priSei+' PRIMEI:'+priMei)
               kurikaesiRow['PRISEI'] = priSei
               kurikaesiRow['PRIMEI'] = priMei
               logging.debug(kurikaesiRow)
               logging.debug('---------------------------------')
           w.writerow(kurikaesiRow)
           cnt = cnt + 1
           progress(cnt-1, len(clList))

    csvf.close()
    #clList.to_csv(CSVFILE)
    #progress(cnt - 1, len(clList))
    logging.debug('-----------End---------------')

if __name__ == '__main__':
    Process()


