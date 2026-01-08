from django.contrib import admin
from restaurant_web.models import Menu, OrderStatus


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('menuID', 'food', 'restaurant', 'category', 'is_available', 'created_at')
    list_filter = ('is_available', 'category', 'restaurant', 'created_at')
    search_fields = ('food__foodName', 'restaurant__resName')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('statusID', 'order', 'status', 'created_at', 'updated_by')
    list_filter = ('status', 'created_at')
    search_fields = ('order__orderID', 'notes')
    readonly_fields = ('created_at',)
