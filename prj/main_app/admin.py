from django.contrib import admin

# Register your models here.
from .models import *
from django.contrib import admin


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
