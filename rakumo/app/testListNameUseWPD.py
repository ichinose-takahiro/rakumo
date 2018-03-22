# -*- coding: utf-8 -*-
# テスト用に、ユーザーネームを置き換える
from __future__ import print_function
from loginglibrary import init
import csv
import json

WORKDIR = '/var/www/html/mysite/rakumo/static/files/'
#CALENDARCSV = WORKDIR + '180206_GroupSession_edit.csv'
#CALENDARCSV = WORKDIR + '180206_GroupSession.csv'
CALENDARCSV = WORKDIR + '180314_GroupSession.csv'
CSVFILE = WORKDIR + '180314_GroupSession_change_wpd.csv'
USERCSV = WORKDIR + 'user.csv'
USEREXCSV = WORKDIR + 'userUnique.csv'
pricnt = 0
memcnt = 0

USERADDRESS = [
    'tobaru-hideyasu@919.jp','nishiyama-kohei@919.jp','inomata-toshiyuki@919.jp','takubo-hidenori@919.jp','koike-akihiro@919.jp',
    'morimoto-hikaru@919.jp','sato-manami@919.jp','kan-sayuri@919.jp','mikami-takashi@919.jp','hama-yasuki@919.jp',
    'hirata-naomi@919.jp','shiga-sakurako@919.jp','komagata-yukino@919.jp','kitabatake-yoshimi@919.jp','kaneda-yoko@919.jp',
    'kimura-satoko@919.jp','noma-chinami@919.jp','kasai-kazuaki@919.jp','suzuki-yugo@919.jp','isomoto-miho@919.jp',
    'nihonmatsu-yumeko@919.jp','saito-takamitsu@919.jp','iwasaki-sanae@919.jp','matsushita-atsushi@919.jp','matsumura-shun@919.jp',
    'matsubara-kosuke@919.jp','miyamoto-tomomi@919.jp','horino-shunya@919.jp','hogan-nobutaka@919.jp','ishida-yuko@919.jp',
    'yamaoka-yuina@919.jp','sato-sora@919.jp','ogawa-yoshiteru@919.jp','yoshida-hiroshi@919.jp','karasu-mikiko@919.jp',
    'yamada-ryohei@919.jp','sakamoto-ayako@919.jp','nomura-miku@919.jp','nakahira-shinya@919.jp'
]

logging = init('testlist')

def selectEmail(cnt):
    global priEmail

    priEmail = USERADDRESS[cnt]
    cnt = cnt + 1
    if cnt == len(USERADDRESS):
        cnt = 0

    return priEmail, cnt
def getcalendarData():
    u""" getcalendarData カレンダーデータを取得
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    calendarData = csvToJson(CALENDARCSV)
    return calendarData
def getmemberData():
    u"""getmemberData メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    memberData = csvToJson(USERCSV)
    return memberData
def getExMemberData():
    u"""getmemberData 名称変更用メンバーデータを取得する処理
    CSVからJSONデータを取得します。
    :return: JSONデータ
    """
    memberData = csvToJson(USEREXCSV)
    return memberData

"CSVを読み込みJSON化する"
def csvToJson(csvData):
    jsonData = []
    with open(csvData, 'r',encoding='utf-8', errors='ignore', newline='') as f:
        for line in csv.DictReader(f):
            line_json = json.dumps(line, ensure_ascii=False)
            jsonData.append(line_json)
    return jsonData
def checkExName(ret):
    u"""checkExName 名前が特殊なユーザー名を変更する処理
    :param ret: 対象データ
    :return: チェック後データ
    """
    for memberData in getExMemberData():
        memberData = json.loads(memberData,encoding='UTF-8')
        if ret['name'] == memberData['NAME']:
            ret['name'] = memberData['EXNAME']
        if ret['priName'] == memberData['NAME']:
            ret['priName'] = memberData['EXNAME']
    return ret
def changeSeiMei(email):
    sei = None
    mei = None

    #memberList = getmemberData()
    for member in getmemberData():
        member = json.loads(member,encoding='UTF-8')
        if email == member['primaryEmail']:
            sei = member['sei']
            mei = member['mei']
            break

    return sei, mei

def getMemberAddress(data, memdata = None):
    u"""getMemberAddress メンバーメールアドレス取得
    カレンダーデータからメンバーデータをチェックしてアドレスを抽出します
    :param data: カレンダーデータ
    :return: 参加者と登録者のメールアドレス
    """
    ret = {}
    flg1 = False
    flg2 = False
    logging.debug(data)
    memberName = data['SEI'] + data['MEI']
    priName = data['PRISEI']+data['PRIMEI']
    ret = {'name': memberName, 'priName': priName, 'retFlg': False}
    logging.debug(ret)
    ret = checkExName(ret)
    logging.debug(ret)
    for memberData in getmemberData():
        memberData = json.loads(memberData,encoding='UTF-8')
        if memberData['fullName'] == ret['name']:
            ret['email'] = memberData['primaryEmail']
            flg1 = True
        if memberData['fullName'] == ret['priName']:
            ret['pri_email'] = memberData['primaryEmail']
            flg2 = True
        if flg1 == True and flg2 == True:
            break
    if flg1 == False or flg2 == False:
        ret = None
        #logging.debug('flg1:'+str(flg1))
        #logging.debug('flg2:'+str(flg2))
        #if flg1 == True:
        #   ret['pri_email'] = ret['email']
        #elif flg2 == True:
        #   ret['email'] = ret['pri_email']
        #else:
        #   ret = None
    #logging.debug(memberName)
    #logging.debug(priName)
    logging.debug(ret)
    return ret
def checkbywpd(memData):
    if memData['pri_email'] in USERADDRESS:
        if memData['email'] in USERADDRESS:
            return True

    return False

def Process():
    getProcess()

def getProcess():
    global pricnt
    global memcnt
    pricEmail = 'ichinose-takahiro@919.jp'
    priEmail = 'ichinose-takahiro@919.jp'

    # カレンダーデータを取得
    clList = getcalendarData()
    logging.debug('------------start----------')
    # 列の設定
    dictkey=['SCD_SID','SCD_RSSID','SCE_SID','SCD_GRP_SID','SUMMARY','DESCRIPTION','BIKO','COLORID','RESOURCE','SCD_DAILY','STARTDATE','ENDDATE','SEI','MEI','PRISEI','PRIMEI','PUBLICFLG','EDITFLG','BYDAY_SU','BYDAY_MO','BYDAY_TU','BYDAY_WE','BYDAY_TH','BYDAY_FR','BYDAY_SA','SCE_DAY','SCE_WEEK','SCE_DAILY','SCE_MONTH_YEARLY','SCE_DAY_YEARLY']
    csvf = open(CSVFILE, 'w')
    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    for clData in clList:
        logging.debug(str(pricnt)+':'+str(memcnt))
        clData = json.loads(clData,encoding='utf-8')
        writeData = clData
        memData = getMemberAddress(clData)
        if memData is None:
            logging.warn('not name:::::SCD_SID:'+ writeData['SCD_SID'])
            continue
        logging.debug(memData)
        if checkbywpd(memData) == True:
            w.writerow(writeData)

    csvf.close()

    logging.debug('-----------End---------------')

if __name__ == '__main__':
    Process()

