import ast
from django import forms
from .loginglibrary import init
checkList = []
loging = init('checkdata')


def doCheck(checkList, eventkey):

    dictList = ast.literal_eval(checkList[0])
    keyList =  dictList.keys()
    if len(keyList) != len(eventkey):
       loging.error(keyList)
       loging.error(eventkey)
       loging.error('項目数に差異があります')
       raise forms.ValidationError("項目数に差異があります")
    for key in keyList:
        if key not in eventkey:
            loging.error(keyList)
            loging.error(eventkey)
            loging.error('必要な項目が不足しています')
            raise forms.ValidationError("必要な項目が不足しています")

