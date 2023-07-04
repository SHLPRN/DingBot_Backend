import random
import requests
import datetime

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from utils.token import *


@csrf_exempt
def login(request):
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    params = {
        'appid': settings.SECRETS['APP_ID'],
        'secret': settings.SECRETS['APP_SECRET'],
        'code': request.POST.get('code'),
        'grant_type': 'authorization_code'
    }
    data = requests.get(url, params=params).json()
    openid = data["openid"]
    customers = Customer.objects.filter(openid=openid)
    customer = None
    msg = '登录成功'
    if len(customers) == 0:
        new_customer = Customer()
        new_customer.openid = openid
        new_customer.save()
        customer = new_customer
        msg = '注册成功'
    else:
        customer = customers.first()
    token = create_token('customer', customer.id)
    return JsonResponse({'errno': 0, 'msg': msg, 'token': token})


@csrf_exempt
def add_order(request):
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    day_str = now_time[2:8]
    time_str = now_time[8:]
    customer = Customer.objects.get(id=int(get_payload(request.META.get('HTTP_TOKEN'))['customer_id']))
    customer_str = str(customer.id)[-1:]
    configuration = request.POST.get('configuration')
    config_list = configuration.split(',')
    config_cnt = 0
    for config in config_list:
        config_cnt += int(config)
    config_cnt %= 1000
    phone = request.POST.get('phone')
    random_str = str('%03d' % random.randint(0, 999))
    identifier = day_str + phone[10] + time_str + str(config_cnt).zfill(3) + random_str + customer_str
    order = Order()
    order.identifier = identifier
    order.customer = customer
    order.product = Product.objects.get(id=int(request.POST.get('product_id')))
    order.configuration = configuration
    order.price = float(request.POST.get('price'))
    order.status = 0
    order.customer_name = request.POST.get('customer_name')
    order.phone = phone
    order.address = request.POST.get('address')
    order.save()
    return JsonResponse({'errno': 0, 'msg': '新建订单成功', 'id': order.id, 'identifier': identifier})
