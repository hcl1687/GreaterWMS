from userprofile.models import Users
from staff.models import ListModel, TypeListModel
import re, base64, json
from rest_framework.exceptions import APIException

def get_supplier_name(user):
    name = ''
    user_profile = Users.objects.filter(name=user.username).first()
    staff_name_obj = ListModel.objects.filter(openid=user_profile.openid, staff_name=user.username,).first()
    script_obj = re.findall(r'script', str(data), re.IGNORECASE)
    select_obj = re.findall(r'select', str(data), re.IGNORECASE)
    if script_obj:
        raise APIException({'detail': 'Bad Data can‘not be store'})
    elif select_obj:
        raise APIException({'detail': 'Bad Data can‘not be store'})
    else:
        return data