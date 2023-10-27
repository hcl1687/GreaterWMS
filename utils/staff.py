from userprofile.models import Users
from staff.models import ListModel, TypeListModel
import re, base64, json
from rest_framework.exceptions import APIException
from supplier.models import ListModel as SupplierModel

class Staff(object):
    def get_supplier_name(user):
        name = ''
        user_profile = Users.objects.filter(name=user.username).first()
        staff_name_obj = ListModel.objects.filter(staff_name=user.username,
            staff_type='Supplier').first()
        if staff_name_obj:
            supplier = SupplierModel.objects.filter(creater=staff_name_obj.staff_name).first()
            if supplier:
                name=supplier.supplier_name
        return name
    def is_supplier(staff):
        return staff.staff_type == 'Supplier'
    def is_admin(staff):
        return staff.staff_type == 'Admin'