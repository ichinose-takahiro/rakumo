from django import forms
checkList = []

def doCheck(upDateList, EVENTKEY):

    ret = True

    checkList = dict(upDateList)
    keyList = checkList.keys()
    for key in keyList:
        if key not in EVENTKEY:
            ret = False

    raise forms.ValidationError("You forgot to retype your password.")
