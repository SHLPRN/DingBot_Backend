from django.db.models import Q, Max
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *


@csrf_exempt
def get_product_list(request):
    categorys = Category.objects.filter(level=int(request.POST.get('level')))
    level_num = Category.objects.all().aggregate(Max('level'))['level__max']
    data = []
    for category in categorys:
        product_categorys = ProductCategory.objects.filter(category=category)
        product_list = []
        for product_category in product_categorys:
            mid_categorys = ProductCategory.objects.filter(product=product_category.product)
            category_list = {}
            i = 1
            for mid_category in mid_categorys:
                category_list[f'level_{i}'] = mid_category.category.name
                i += 1
            product_list.append({
                'id': product_category.product.id,
                'category': category_list,
                'name': product_category.product.name,
                'image': product_category.product.image,
                'lowprice': float(product_category.product.price),
            })
        data.append({
            'name': category.name,
            'product_list': product_list,
        })
    return JsonResponse({'errno': 0, 'level_num': level_num, 'data': data})


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
        module_has_choice = 0
        choices = Choice.objects.filter(module=module).order_by('order')
        choice_list = []
        for choice in choices:
            choice_choice_list = []
            if choice.has_choice == 1:
                module_has_choice = 1
                choice_coice = eval(choice.choice)
                for i in range(1, choice_coice['choice_num'] + 1):
                    mid_choice = choice_coice[f'{i}']
                    choice_choice_list.append({
                        'order': i,
                        'name': mid_choice['name'],
                        'price': float(mid_choice['price'])
                    })
            choice_list.append({
                'id': choice.id,
                'name': choice.name,
                'price': float(choice.price),
                'has_choice': choice.has_choice,
                'choice_list': choice_choice_list
            })
        module_list.append({
            'id': module.id,
            'name': module.name,
            'has_choice': module_has_choice,
            'choice_list': choice_list,
        })
    data = {
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'view_list': view_list,
        'module_list': module_list,
    }
    return JsonResponse({'errno': 0, 'data': data})


@csrf_exempt
def get_choice_image(request):
    choice = Choice.objects.get(id=int(request.POST.get('choice_id')))
    view = View.objects.get(id=int(request.POST.get('view_id')))
    has_choice = int(request.POST.get('has_choice'))
    if has_choice == 0:
        choice_images = ChoiceImage.objects.filter(Q(choice=choice) & Q(view=view))
        if len(choice_images) == 0:
            return JsonResponse({'errno': 0, 'image': None})
        choice_image = choice_images.first()
        return JsonResponse({'errno': 0, 'image': choice_image.image})
    else:
        choice_choice = eval(choice.choice)
        view_list = choice_choice[request.POST.get('choice_order')]['view']
        choice_image = None
        if f'{view.id}' in view_list:
            choice_image = view_list[f'{view.id}']
        return JsonResponse({'errno': 0, 'image': choice_image})
