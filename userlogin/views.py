from django.http import JsonResponse
from utils.fbmsg import FBMsg
from django.contrib import auth
from django.contrib.auth.models import User
import json
from userprofile.models import Users
from staff.models import ListModel as staff
from rest_framework_simplejwt.tokens import RefreshToken
from utils.staff import Staff

def login(request, *args, **kwargs):
    post_data = json.loads(request.body.decode())
    data = {
        "name": post_data.get('name'),
        "password": post_data.get('password'),
    }
    ip = request.META.get('HTTP_X_FORWARDED_FOR') if request.META.get(
        'HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
    if User.objects.filter(username=str(data['name'])).exists():
        user = auth.authenticate(username=str(data['name']), password=str(data['password']))
        if user is None:
            err_ret = FBMsg.err_ret()
            err_ret['data'] = data
            return JsonResponse(err_ret)
        else:
            auth.login(request, user)
            user_detail = Users.objects.filter(user_id=user.id).first()
            staff_obj = staff.objects.filter(staff_name=str(user_detail.name)).first()
            staff_id = staff_obj.id

            refresh = RefreshToken.for_user(user)

            data = {
                "name": data['name'],
                'openid': user_detail.openid if Staff.is_admin(staff_obj) else staff_obj.openid,
                "user_id": staff_id,
                "refresh_token": str(refresh),
                "access_token": str(refresh.access_token)
            }
            ret = FBMsg.ret()
            ret['ip'] = ip
            ret['data'] = data
            return JsonResponse(ret)
    else:
        err_ret = FBMsg.err_ret()
        err_ret['ip'] = ip
        err_ret['data'] = data
        return JsonResponse(err_ret)
