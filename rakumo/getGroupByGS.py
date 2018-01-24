### ユーザーのデータを取ってくるやつや
#!/bin/python
# -*- coding: utf-8 -*-

import json
import pycurl
import io
import xml.etree.ElementTree as ET
import xmltodict

def main():

    url = 'https://gs.919.jp/gsession/api/schedule/groupl.do'

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url);
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.HTTPHEADER, ["Content-type: application/vnd.ogc.sld+xml"])
    c.setopt(pycurl.USERPWD, 'ssp:ssp')
    c.setopt(pycurl.HTTPPOST, [('usid', '526')])
    c.setopt(pycurl.COOKIEFILE, 'cookie.txt')
    c.setopt(pycurl.POST, 1)
    b = io.BytesIO()
    c.setopt(pycurl.WRITEFUNCTION, b.write)

    response = c.perform()
    ret = b.getvalue()
    http_code = c.getinfo(pycurl.HTTP_CODE)
    dict = xmltodict.parse(ret)
    jsondata = json.dumps(dict, ensure_ascii=False, indent=4)
    print(jsondata)



if __name__ == '__main__':
    main()