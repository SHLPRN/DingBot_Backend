import time
import os.path

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
    return JsonResponse({'errno': 0, 'token': token})


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
    for order1 in range(1, module_num + 1):
        module = Module()
        module.name = request.POST.get(f'module_{order1}_name')
        module.order = order1
        module.product = product
        module.save()
        choice_num = int(request.POST.get(f'module_{order1}_choice_num'))
        for order2 in range(1, choice_num + 1):
            choice = Choice()
            choice.name = request.POST.get(f'module_{order1}_choice_{order2}_name')
            choice.price = float(request.POST.get(f'module_{order1}_choice_{order2}_price'))
            choice.order = order2
            choice.module = module
            choice.save()
    return JsonResponse({'errno': 0, 'msg': '添加组件成功'})


@csrf_exempt
def add_choice_image(request):
    view = View.objects.get(id=int(request.POST.get('view_id')))
    choice = Choice.objects.get(id=int(request.POST.get('choice_id')))
    choice_image = ChoiceImage()
    choice_image_image = request.FILES.get('image')
    choice_image.image = "WAIT"
    choice_image.choice = choice
    choice_image.view = view
    choice_image.save()
    choice_image.image = handle_image(choice_image_image,
                                      os.path.join(CHOICE_URL, f'choice_image_{choice_image.id}' +
                                                   os.path.splitext(str(choice_image_image.name))[1]))
    choice_image.save()
    return JsonResponse({'errno': 0, 'msg': '添加可选项视角图成功'})


@csrf_exempt
def get_product_list(request):
    products = Product.objects.all()
    data = [
        {
            'id': product.id,
            'name': product.name,
            'price': product.price,
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
            choice_images = ChoiceImage.objects.filter(choice=choice)
            choice_view_list = [
                choice_image.view.name for choice_image in choice_images
            ]
            choice_list.append({
                'id': choice.id,
                'name': choice.name,
                'view_list': choice_view_list,
            })
        module_list.append({
            'id': module.id,
            'name': module.name,
            'choice_list': choice_list,
        })
    return JsonResponse({'errno': 0, 'view_list': view_list, 'module_list': module_list})


def handle_image(image, path):
    with open('.' + path, 'wb+') as f:
        for chunk in image.chunks():
            f.write(chunk)
    return path
