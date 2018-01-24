### GroupSessionのユーザーのデータを取ってくるやつ。所属グループも取得
#!/bin/python
# -*- coding: utf-8 -*-

import json
import pycurl
import io
import xml.etree.ElementTree as ET
import xmltodict
import csv

def writeCSV(jsonData, w):

    for data in jsonData["ResultSet"]["Result"]:
        print(data['GroupSet']['@Count'])
        if int(data['GroupSet']['@Count']) <= 0:
           target_dict = {'Usrsid':data['Usrsid'],
                           'Usisei': data['Usisei'],
                           'Usimei': data['Usimei'],
                           'GroupCount': data['GroupSet']['@Count'],
                           'GroupSid': '',
                           'GroupName': '',
                           }
           w.writerow(target_dict)
        else:
            if int(data['GroupSet']['@Count']) == 1:
                groupList = [data['GroupSet']['Group']]
            else:
                groupList = data['GroupSet']['Group']
            for group in groupList:
                print('----')
                print(group)
                target_dict = {'Usrsid': data['Usrsid'],
                               'Usisei': data['Usisei'],
                               'Usimei': data['Usimei'],
                               'GroupCount': data['GroupSet']['@Count'],
                               'GroupSid': str(group['GrpSid']),
                               'GroupName': group['GrpName']
                               }
                w.writerow(target_dict)

def getJsonData(page):
    url = 'https://gs.919.jp/gsession/api/user/search.do?page='+str(page)

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url);
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.HTTPHEADER, ["Content-type: application/vnd.ogc.sld+xml"])
    c.setopt(pycurl.USERPWD, 'ssp:ssp')
    #c.setopt(pycurl.HTTPPOST, [('usid', '526')])
    c.setopt(pycurl.HTTPPOST, [('usid', '526')])
    c.setopt(pycurl.COOKIEFILE, 'cookie'+str(page)+'.txt')
    b = io.BytesIO()
    c.setopt(pycurl.WRITEFUNCTION, b.write)
    print('start')
    response = c.perform()
    ret = b.getvalue()
    http_code = c.getinfo(pycurl.HTTP_CODE)
    dict = xmltodict.parse(ret)
    jsondata = json.dumps(dict, ensure_ascii=False, indent=4)
    jsondata = json.loads(jsondata, encoding='UTF-8')
    b.close()
    return jsondata

def main():

    jsondata = getJsonData(1)
    csvf = open('/var/www/html/googleapi/data/userGroup.csv', 'w')

    # 列の設定
    dictkey=['Usrsid','Usisei','Usimei','GroupCount','GroupSid','GroupName']
    w = csv.DictWriter(csvf, dictkey) # キーの取得
    w.writeheader() # ヘッダー書き込み

    writeCSV(jsondata,w)

    # 各行書き込み
    pagetoken = 2
    maxPage = jsondata["ResultSet"]['@MaxPage']
    cnt = pagetoken
    while cnt <= int(maxPage):
        jsondata = getJsonData(cnt)
        writeCSV(jsondata, w)
        cnt = cnt+1

    csvf.close()


if __name__ == '__main__':
    main()