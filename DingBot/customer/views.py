from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *


@csrf_exempt
def get_product_list(request):
    categorys = Category.objects.filter(level=int(request.POST.get('level')))
    data = []
    for category in categorys:
        product_categorys = ProductCategory.objects.filter(category=category)
        product_list = [
            {
                'id': product_category.product.id,
                'name': product_category.product.name,
                'image': product_category.product.image,
            } for product_category in product_categorys
        ]
        data.append({
            'name': category.name,
            'product_list': product_list,
        })
    return JsonResponse({'errno': 0, 'data': data})


@csrf_exempt
def get_product(request):
    product = Product.objects.get(id=int(request.POST.get('product_id')))
    views = View.objects.filter(product=product)
    modules = Module.objects.filter(product=product).order_by('order')
    view_list = [
        {
            'id': view.id,
            'name': view.name,
            'image': view.image,
        } for view in views
    ]
    module_list = []
    for module in modules:
        choices = Choice.objects.filter(module=module).order_by('order')
        choice_list = [
            {
                'id': choice.id,
                'name': choice.name,
                'price': choice.price,
            } for choice in choices
        ]
        module_list.append({
            'id': module.id,
            'name': module.name,
            'choice_list': choice_list,
        })
    data = {
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'view_list': view_list,
        'module_list': module_list,
    }
    return JsonResponse({'errno': 0, 'data': data})


@csrf_exempt
def get_choice_image(request):
    choice = Choice.objects.get(id=int(request.POST.get('choice_id')))
    view = View.objects.get(id=int(request.POST.get('view_id')))
    choice_image = ChoiceImage.objects.filter(Q(choice=choice) & Q(view=view)).first()
    return JsonResponse({'errno': 0, 'image': choice_image.image})
