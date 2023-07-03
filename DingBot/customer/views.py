import random
import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from utils.token import *


@csrf_exempt
def login(request):
    token = create_token('customer', int(request.POST.get('customer_id')))
    return JsonResponse({'errno': 0, 'token': token})


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
