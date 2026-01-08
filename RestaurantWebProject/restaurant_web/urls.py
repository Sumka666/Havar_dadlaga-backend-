from django.urls import path
from .views import (
    dashboard,
    MenuListView,
    MenuDetailView,
    OrderListView,
    OrderDetailView,
    OrderApproveView,
)

urlpatterns = [
    path('', dashboard, name='restaurant-dashboard'),
    path('menu/', MenuListView.as_view(), name='menu-list'),
    path('menu/<int:food_id>/', MenuDetailView.as_view(), name='menu-detail'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/approve/', OrderApproveView.as_view(), name='order-approve'),
]
