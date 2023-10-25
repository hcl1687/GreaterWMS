from userprofile.models import Users
from staff.models import ListModel, TypeListModel
import re, base64, json
from rest_framework.exceptions import APIException

class Staff(object):
    def get_supplier_name(user):
        name = ''
        user_profile = Users.objects.filter(name=user.username).first()
        staff_name_obj = ListModel.objects.filter(openid=user_profile.openid, staff_name=user.username,
            staff_type='Supplier').first()
        if staff_name_obj:
            name=staff_name_obj.staff_name
        return name
    def is_supplier(staff):
        return staff.staff_type == 'Supplier'
    def is_admin(staff):
        return staff.staff_type == 'Admin'