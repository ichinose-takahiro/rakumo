import ast
from django import forms
from .loginglibrary import init
checkList = []
loging = init('checkdata')


def doCheck(checkList, EVENTKEY):

    ret = True

    loging.debug(ast.literal_eval(checkList[0]))
    dictList = ast.literal_eval(checkList[0])
    keyList =  dictList.keys()
    for key in keyList:
        if key not in EVENTKEY:
            ret = False
            raise forms.ValidationError("Headline must be more than 5 characters.")
