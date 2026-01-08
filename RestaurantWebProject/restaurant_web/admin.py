from django.contrib import admin
from restaurant_web.models import Menu, OrderStatus, OperatingHours, Inventory


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


@admin.register(OperatingHours)
class OperatingHoursAdmin(admin.ModelAdmin):
    list_display = ('ID', 'restaurant', 'day_of_week', 'open_time', 'close_time', 'is_closed')
    list_filter = ('day_of_week', 'is_closed', 'restaurant')
    search_fields = ('restaurant__resName',)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('ID', 'food', 'restaurant', 'stock_quantity', 'min_stock_level', 'unit', 'is_low_stock', 'last_updated')
    list_filter = ('restaurant', 'unit')
    search_fields = ('food__foodName', 'restaurant__resName')
    readonly_fields = ('last_updated',)
    
    def is_low_stock(self, obj):
        return obj.stock_quantity <= obj.min_stock_level
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Нөөц дуусаж байна'
