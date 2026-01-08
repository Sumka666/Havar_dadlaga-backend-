from django.db import models
from api.models import Food, Order, OrderFood, Category, Restaurant, Worker


class Menu(models.Model):
    """
    Menu model for restaurant web management
    Groups foods by restaurant and category
    """
    menuID = models.BigAutoField(primary_key=True)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='menu_items')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menus')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_menu'
        ordering = ['category', 'food__foodName']

    def __str__(self):
        return f"{self.food.foodName} - {self.restaurant.resName}"


class OrderStatus(models.Model):
    """
    Order status history tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Хүлээгдэж буй'),
        ('approved', 'Батлагдсан'),
        ('preparing', 'Бэлтгэж байна'),
        ('ready', 'Бэлэн'),
        ('delivered', 'Хүргэгдсэн'),
        ('cancelled', 'Цуцлагдсан'),
    ]

    statusID = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'tbl_order_status'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order.orderID} - {self.status}"


class OperatingHours(models.Model):
    """
    Рестораны ажиллах цаг
    """
    DAY_CHOICES = [
        ('monday', 'Даваа'),
        ('tuesday', 'Мягмар'),
        ('wednesday', 'Лхагва'),
        ('thursday', 'Пүрэв'),
        ('friday', 'Баасан'),
        ('saturday', 'Бямба'),
        ('sunday', 'Ням'),
    ]

    ID = models.BigAutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='operating_hours')
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'tbl_operating_hours'
        unique_together = ('restaurant', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.restaurant.resName} - {self.get_day_of_week_display()}"


class Inventory(models.Model):
    """
    Бараа материалын нөөц (хоолны нөөц)
    """
    ID = models.BigAutoField(primary_key=True)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='inventory')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='inventories')
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10)  # Хамгийн бага нөөц
    unit = models.CharField(max_length=50, default='ш')  # Нэгж (ш, кг, г)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tbl_inventory'
        unique_together = ('food', 'restaurant')
        
    def __str__(self):
        return f"{self.food.foodName} - {self.stock_quantity} {self.unit}"
    
    @property
    def is_low_stock(self):
        """Нөөц дуусаж байгаа эсэхийг шалгах"""
        return self.stock_quantity <= self.min_stock_level
