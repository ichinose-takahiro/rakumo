import ast
from django import forms
from .loginglibrary import init
checkList = []
loging = init('checkdata')


def doCheck(checkList, eventkey):

    dictList = ast.literal_eval(checkList[0])
    keyList =  dictList.keys()
    if len(keyList) != len(eventkey):
       raise forms.ValidationError("項目数に差異があります")
    for key in keyList:
        if key not in eventkey:
            raise forms.ValidationError("必要な項目が不足しています")

