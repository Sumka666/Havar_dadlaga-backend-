from django.db import models
from api.models import Food, Order, OrderFood, Category, Restaurant


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
