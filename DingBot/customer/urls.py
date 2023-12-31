from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('addOrder/', add_order, name='addOrder'),
    path('payOrder/', pay_order, name='payOrder'),
    path('getPayStatus/', get_pay_status, name='getPayStatus'),
    path('payResult/', pay_result, name='payResult'),
    path('getOrderList/', get_order_list, name='getOrderList'),
    path('getOrderInfo/', get_order_info, name='getOrderInfo'),
]
