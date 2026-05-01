from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Seller)
admin.site.register(user)
admin.site.register(products)
admin.site.register(Orders)
admin.site.register(meals)
admin.site.register(OrderItem)
admin.site.register(Dietitian)
admin.site.register(DietitianSlot)
admin.site.register(DietitianLeave)
admin.site.register(DietitianMessage)
admin.site.register(Appointment)
