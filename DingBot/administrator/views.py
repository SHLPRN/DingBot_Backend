import time
import os.path

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from utils.token import *


PRODUCT_URL = '/media/product/'
VIEW_URL = '/media/view/'
CHOICE_URL = '/media/choice/'


@csrf_exempt
def login(request):
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    administrators = Administrator.objects.filter(phone=phone)
    if not administrators.exists():
        return JsonResponse({'errno': 1004, 'msg': '用户不存在'})
    administrator = administrators.first()
    token = create_token('admin', administrator.id)
    return JsonResponse({'errno': 0, 'msg': '登录成功', 'token': token})


@csrf_exempt
def add_product(request):
    product = Product()
    product.name = request.POST.get('name')
    product.description = request.POST.get('description')
    product.price = float(request.POST.get('price'))
    product_image = request.FILES.get('image')
    product.image = "WAIT"
    product.save()
    product.image = handle_image(product_image, os.path.join(PRODUCT_URL, f'product_{product.id}' +
                                                             os.path.splitext(str(product_image.name))[1]))
    product.save()
    for category in request.POST.get('category').split(','):
        product_category = ProductCategory()
        product_category.product = product
        product_category.category = Category.objects.get(id=category)
        product_category.save()
    view_num = int(request.POST.get('view_num'))
    for order in range(1, view_num + 1):
        view = View()
        view.name = request.POST.get(f'view_{order}_name')
        view_image = request.FILES.get(f'view_{order}_image')
        view.image = "WAIT"
        view.product = product
        view.save()
        view.image = handle_image(view_image, os.path.join(VIEW_URL, f'view_{view.id}' +
                                                           os.path.splitext(str(view_image.name))[1]))
        view.save()
    return JsonResponse({'errno': 0, 'msg': '添加产品成功'})


@csrf_exempt
def add_module(request):
    product = Product.objects.get(id=int(request.POST.get('product_id')))
    module_num = int(request.POST.get('module_num'))
    now_num = len(Module.objects.filter(product=product))
    for order1 in range(1, module_num + 1):
        module = Module()
        module.name = request.POST.get(f'module_{order1}_name')
        module.order = order1 + now_num
        module.product = product
        module.save()
        choice_num = int(request.POST.get(f'module_{order1}_choice_num'))
        for order2 in range(1, choice_num + 1):
            choice = Choice()
            choice.name = request.POST.get(f'module_{order1}_choice_{order2}_name')
            choice.price = float(request.POST.get(f'module_{order1}_choice_{order2}_price'))
            choice.order = order2
            choice.module = module
            choice_has_choice = int(request.POST.get(f'module_{order1}_choice_{order2}_has_choice'))
            choice.has_choice = choice_has_choice
            choice_choice = {'choice_num': 0}
            if choice_has_choice == 1:
                choice_choice_num = int(request.POST.get(f'module_{order1}_choice_{order2}_choice_num'))
                choice_choice['choice_num'] = choice_choice_num
                for order3 in range(1, choice_choice_num + 1):
                    choice_choice[f'{order3}'] = {
                        'name': request.POST.get(f'module_{order1}_choice_{order2}_choice_{order3}_name'),
                        'price': float(request.POST.get(f'module_{order1}_choice_{order2}_choice_{order3}_price')),
                        'view': {}
                    }
            choice.choice = str(choice_choice)
            choice.save()
    return JsonResponse({'errno': 0, 'msg': '添加组件成功'})


@csrf_exempt
def add_choice_image(request):
    view = View.objects.get(id=int(request.POST.get('view_id')))
    choice = Choice.objects.get(id=int(request.POST.get('choice_id')))
    has_choice = int(request.POST.get('has_choice'))
    choice_image_image = request.FILES.get('image')
    if has_choice == 0:
        choice_image = ChoiceImage()
        choice_image.image = "WAIT"
        choice_image.choice = choice
        choice_image.view = view
        choice_image.save()
        choice_image.image = handle_image(choice_image_image,
                                          os.path.join(CHOICE_URL, f'choice_image_{choice_image.id}' +
                                                       os.path.splitext(str(choice_image_image.name))[1]))
        choice_image.save()
    else:
        choice_order = request.POST.get('choice_order')
        choice_dict = eval(choice.choice)
        choice_dict[choice_order]['view'][str(view.id)] = handle_image(choice_image_image,
                                          os.path.join(CHOICE_URL,
                                                       f'choice_image_{choice.id}_{choice_order}_{view.id}' +
                                                       os.path.splitext(str(choice_image_image.name))[1]))
        choice.choice = str(choice_dict)
        choice.save()
    return JsonResponse({'errno': 0, 'msg': '添加可选项视角图成功'})


@csrf_exempt
def get_product_list(request):
    products = Product.objects.all()
    data = [
        {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.image,
        } for product in products
    ]
    return JsonResponse({'errno': 0, 'data': data})


@csrf_exempt
def get_product(request):
    product = Product.objects.get(id=int(request.POST.get('product_id')))
    views = View.objects.filter(product=product)
    view_list = [
        {
            'id': view.id,
            'name': view.name,
        } for view in views
    ]
    modules = Module.objects.filter(product=product).order_by('order')
    module_list = []
    for module in modules:
        choices = Choice.objects.filter(module=module).order_by('order')
        choice_list = []
        for choice in choices:
            has_choice = choice.has_choice
            if has_choice == 0:
                choice_images = ChoiceImage.objects.filter(choice=choice)
                choice_view_list = [
                    {
                        'id': choice_image.view.id,
                        'name': choice_image.view.name
                    } for choice_image in choice_images
                ]
                choice_list.append({
                    'id': choice.id,
                    'name': choice.name,
                    'has_choice': choice.has_choice,
                    'view_list': choice_view_list,
                })
            else:
                choice_choice = eval(choice.choice)
                choice_choice_list = []
                for i in range(1, choice_choice['choice_num'] + 1):
                    mid_view_list = []
                    for view_id in choice_choice[f'{i}']['view']:
                        view = View.objects.get(id=int(view_id))
                        mid_view_list.append({
                                'id': view.id,
                                'name': view.name
                            })
                    choice_choice_list.append({
                        'name': choice_choice[f'{i}']['name'],
                        'view_list': mid_view_list
                    })
                choice_list.append({
                    'id': choice.id,
                    'name': choice.name,
                    'has_choice': choice.has_choice,
                    'choice_list': choice_choice_list,
                })
        module_list.append({
            'id': module.id,
            'name': module.name,
            'choice_list': choice_list,
        })
    return JsonResponse({'errno': 0, 'view_list': view_list, 'module_list': module_list})


@csrf_exempt
def delete_choice_image(request):
    view = View.objects.get(id=int(request.POST.get('view_id')))
    choice = Choice.objects.get(id=int(request.POST.get('choice_id')))
    has_choice = int(request.POST.get('has_choice'))
    if has_choice == 0:
        choice_image = ChoiceImage.objects.get(Q(view=view) & Q(choice=choice))
        os.remove('.' + choice_image.image)
        choice_image.delete()
    else:
        choice_choice = eval(choice.choice)
        choice_image = choice_choice[request.POST.get('choice_order')]['view'][f'{view.id}']
        os.remove('.' + choice_image)
        del choice_choice[request.POST.get('choice_order')]['view'][f'{view.id}']
        choice.choice = str(choice_choice)
        choice.save()
    return JsonResponse({'errno': 0, 'msg': '删除成功'})


@csrf_exempt
def get_order_list(request):
    orders = Order.objects.all().order_by('-time')
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
def search_order(request):
    orders = Order.objects.filter(identifier=request.POST.get('identifier'))
    if len(orders) == 0:
        return JsonResponse({'errno': 2001, 'msg': '订单不存在'})
    order = orders.first()
    return JsonResponse({
        'errno': 0,
        'msg': '检索成功',
        'id': order.id,
        'identifier': order.identifier,
        'status': order.status,
        'time': str(order.time)[:10],
        'customer_name': order.customer_name,
        'price': float(order.price),
    })


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


def handle_image(image, path):
    with open('.' + path, 'wb+') as f:
        for chunk in image.chunks():
            f.write(chunk)
    return path
