import os
import json
import qrcode
import random
import hashlib
import requests
import datetime

from random import Random
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from utils.token import *


notify_url = f"{settings.SECRETS['DOMIN']}/customer/payResult/" # 回调函数，完整路由
trade_type = 'NATIVE'                   # 交易方式
APP_ID = settings.SECRETS['APP_ID']
MCH_ID = settings.SECRETS['MCH_ID']     # 商户号
API_KEY = settings.SECRETS['API_KEY']
UFDODER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"  # 微信下单api
CREATE_IP = settings.SECRETS['HOST']    # 服务器IP
WXPAY_URL = "/media/wxpay/"             # 存放支付二维码的路径


@csrf_exempt
def login(request):
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    params = {
        'appid': APP_ID,
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
    now = datetime.datetime.now()
    now_time = now.strftime("%Y%m%d%H%M%S")
    day_str = now_time[2:8]
    time_str = now_time[8:]
    customer = Customer.objects.get(id=int(get_payload(request.META.get('HTTP_TOKEN'))['customer_id']))
    customer_str = str(customer.id)[-1:]
    configuration = request.POST.get('configuration')
    config_list = configuration.split(',')
    config_cnt = 0
    for config in config_list:
        config_num = int(config)
        config_cnt += (config_num // 100 + config_num % 100)
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
    order.time = now
    order.save()
    return JsonResponse({'errno': 0, 'msg': '新建订单成功', 'id': order.id, 'identifier': identifier})


@csrf_exempt
def pay_order(request):
    order = Order.objects.get(id=int(request.POST.get('order_id')))
    if order.status != 0:
        return JsonResponse({'errno': 2002, 'msg': '订单已支付，请勿重复支付'})
    total_price = float(order.price)                # 订单总价
    order_name = order.product.name                 # 订单名
    order_detail = f'DingBotBoards-{order_name}'    # 订单描述
    order_identifier = order.identifier             # 订单号
    data_dict = wxpay(order_identifier, order_name, order_detail, total_price)  # 调用统一支付接口
    # 如果请求成功
    if data_dict.get('return_code') == 'SUCCESS':
        # 业务处理
        # 二维码名字
        qrcode_name = order_identifier + '.png'
        # 创建二维码
        img = qrcode.make(data_dict.get('code_url'))
        img_url = os.path.join(WXPAY_URL, qrcode_name)
        img.save('.' + img_url)
        return_msg = {
            'errno': 0,
            'msg': '获取支付二维码成功',
            'qrcode': img_url
        }
        return_msg = json.dumps(return_msg, ensure_ascii=False)
        return HttpResponse(return_msg)
    return_msg = {
        'code': 2001,
        'msg': '获取支付二维码失败'
    }
    return_msg = json.dumps(return_msg, ensure_ascii=False)
    return HttpResponse(return_msg)


@csrf_exempt
def get_pay_status(request):
    order = Order.objects.get(id=int(request.POST.get('order_id')))
    return JsonResponse({'errno': 0, 'status': order.status})


@csrf_exempt
def pay_result(request):
    data_dict = trans_xml_to_dict(request.body)     # 回调数据转字典
    print('支付回调结果', data_dict)
    sign = data_dict.pop('sign')                    # 取出签名
    back_sign = get_sign(data_dict, API_KEY)        # 计算签名
    # 验证签名是否与回调签名相同
    if sign == back_sign and data_dict['return_code'] == 'SUCCESS':
        order_identifier = data_dict['out_trade_no']
        # 处理支付成功逻辑，根据订单号修改后台数据库状态
        order = Order.objects.get(identifier=order_identifier)
        order.status = 1
        order.save()
        os.remove('.' + os.path.join(WXPAY_URL, order_identifier + '.png'))
        # 返回接收结果给微信，否则微信会每隔8分钟发送post请求
        return HttpResponse(trans_dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'}))
    return HttpResponse(trans_dict_to_xml({'return_code': 'FAIL', 'return_msg': 'SIGNERROR'}))


def random_str(randomlength=8):
    """
    生成随机字符串
    :param randomlength: 字符串长度
    :return:
    """
    strs = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        strs += chars[random.randint(0, length)]
    print(strs)
    return strs


# 请求统一支付接口
def wxpay(order_identifier, order_name, order_price_detail, order_total_price):
    nonce_str = random_str()  # 拼接出随机的字符串即可，我这里是用  时间+随机数字+5个随机字母
    total_fee = int(float(order_total_price) * 100)    # 付款金额，单位是分，必须是整数
    print(total_fee)
    params = {
        'appid': APP_ID,                    # APPID
        'mch_id': MCH_ID,                   # 商户号
        'nonce_str': nonce_str,             # 随机字符串
        'out_trade_no': order_identifier,   # 订单编号，可自定义
        'total_fee': total_fee,             # 订单总金额
        'spbill_create_ip': CREATE_IP,      # 自己服务器的IP地址
        'notify_url': notify_url,           # 回调地址，微信支付成功后会回调这个url，告知商户支付结果
        'body': order_name,                 # 商品描述
        'detail': order_price_detail,       # 商品描述
        'trade_type': trade_type,           # 扫码支付类型
    }

    sign = get_sign(params, API_KEY)        # 获取签名
    params['sign'] = sign                   # 添加签名到参数字典
    xml = trans_dict_to_xml(params)         # 转换字典为XML
    response = requests.request('post', UFDODER_URL, data=xml.encode()) # 以POST方式向微信公众平台服务器发起请求
    data_dict = trans_xml_to_dict(response.content)                     # 将请求返回的数据转为字典
    print(data_dict)
    return data_dict


def get_sign(data_dict, key):
    """
    签名函数
    :param data_dict: 需要签名的参数，格式为字典
    :param key: 密钥 ，即上面的API_KEY
    :return: 字符串
    """
    params_list = sorted(data_dict.items(), key=lambda e: e[0], reverse=False)  # 参数字典倒排序为列表
    params_str = "&".join(u"{}={}".format(k, v) for k, v in params_list) + '&key=' + key
    # 组织参数字符串并在末尾添加商户交易密钥
    md5 = hashlib.md5()                     # 使用MD5加密模式
    md5.update(params_str.encode('utf-8'))  # 将参数字符串传入
    sign = md5.hexdigest().upper()          # 完成加密并转为大写
    print(sign)
    return sign


def trans_dict_to_xml(data_dict):
    """
    定义字典转XML的函数
    :param data_dict:
    :return:
    """
    data_xml = []
    for k in sorted(data_dict.keys()):  # 遍历字典排序后的key
        v = data_dict.get(k)            # 取出字典中key对应的value
        if k == 'detail' and not v.startswith('<![CDATA['): # 添加XML标记
            v = '<![CDATA[{}]]>'.format(v)
        data_xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
    return '<xml>{}</xml>'.format(''.join(data_xml))        # 返回XML


def trans_xml_to_dict(data_xml):
    """
    XML转字典
    :param data_xml:
    :return:
    """
    data_dict = {}
    try:
        import xml.etree.cElementTree as eT
    except ImportError:
        import xml.etree.ElementTree as eT
    root = eT.fromstring(data_xml)
    for child in root:
        data_dict[child.tag] = child.text
    return data_dict


@csrf_exempt
def get_order_list(request):
    customer = Customer.objects.get(id=int(get_payload(request.META.get('HTTP_TOKEN'))['customer_id']))
    orders = Order.objects.filter(customer=customer).order_by('-time')
    data = [
        {
            'id': order.id,
            'identifier': order.identifier,
            'status': order.status,
            'time': str(order.time)[:10],
            'customer_name': order.customer_name,
            'price': float(order.price),
        } for order in orders
    ]
    return JsonResponse({'errno': 0, 'data': data})


@csrf_exempt
def get_order_info(request):
    order = Order.objects.get(id=int(request.POST.get('order_id')))
    return JsonResponse({
        'errno': 0,
        'identifier': order.identifier,
        'product_info': {
            'id': order.product.id,
            'name': order.product.name,
        },
        'configuration': order.configuration,
        'price': float(order.price),
        'status': order.status,
        'customer_name': order.customer_name,
        'phone': order.phone,
        'address': order.address,
        'time': order.time.strftime("%Y-%m-%d %H:%M:%S")
    })
