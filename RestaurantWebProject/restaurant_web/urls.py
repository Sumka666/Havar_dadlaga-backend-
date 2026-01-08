from django.urls import path
from .views import (
    dashboard,
    MenuListView,
    MenuDetailView,
    OrderListView,
    OrderDetailView,
    OrderApproveView,
    RevenueReportView,
    DeliveryListView,
    DeliveryDetailView,
    RestaurantProfileView,
    OperatingHoursListView,
    CouponListView,
    CouponDetailView,
    ReviewListView,
    ReviewDetailView,
    InventoryListView,
    InventoryDetailView,
    WorkerListView,
    WorkerDetailView,
)

urlpatterns = [
    # Dashboard
    path('', dashboard, name='restaurant-dashboard'),
    
    # Menu Management
    path('menu/', MenuListView.as_view(), name='menu-list'),
    path('menu/<int:food_id>/', MenuDetailView.as_view(), name='menu-detail'),
    
    # Order Management
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/approve/', OrderApproveView.as_view(), name='order-approve'),
    
    # Reports
    path('revenue-report/', RevenueReportView.as_view(), name='revenue-report'),
    
    # Delivery Tracking
    path('deliveries/', DeliveryListView.as_view(), name='delivery-list'),
    path('deliveries/<int:delivery_id>/', DeliveryDetailView.as_view(), name='delivery-detail'),
    
    # Restaurant Profile
    path('restaurant/<int:restaurant_id>/', RestaurantProfileView.as_view(), name='restaurant-profile'),
    
    # Operating Hours
    path('restaurant/<int:restaurant_id>/hours/', OperatingHoursListView.as_view(), name='operating-hours'),
    
    # Promotions/Coupons
    path('coupons/', CouponListView.as_view(), name='coupon-list'),
    path('coupons/<int:coupon_id>/', CouponDetailView.as_view(), name='coupon-detail'),
    
    # Reviews/Comments
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
    
    # Inventory Management
    path('inventory/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:inventory_id>/', InventoryDetailView.as_view(), name='inventory-detail'),
    
    # Staff/Workers Management
    path('workers/', WorkerListView.as_view(), name='worker-list'),
    path('workers/<int:worker_id>/', WorkerDetailView.as_view(), name='worker-detail'),
]
