from django.urls import path
from .views import *

urlpatterns = [
    path('getProductList/', get_product_list, name='getProductList'),
    path('getProduct/', get_product, name='getProduct'),
    path('getChoiceImage/', get_choice_image, name='getChoiceImage'),
]
