from django.urls import path
from api.auth import Login
from api.menu import Menu
from .views import login_view

urlpatterns = [
    path('login/', Login.as_view()),
    path('menu/', Menu.as_view()),
    path('login1/', login_view, name='api-login'),
]
