from django.contrib import admin
from .models import Product, Customer, Order, OrderItem, Payment, Cart, CartItem

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "price", "stock")
    search_fields = ("name", "description")

class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "email")
    search_fields = ("first_name", "email")

class OrderAdmin(admin.ModelAdmin):
    list_display = ("customer", "created_at")
    list_filter = ("customer", "created_at")
    search_fields = ("customer__name",)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity")
    list_filter = ("order",)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "paid_at")
    list_filter = ("paid_at",)
    search_fields = ("paid_at__id",)

class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username",)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")
    list_filter = ("cart", "product")

# Rejestracja modeli
admin.site.register(Product, ProductAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)