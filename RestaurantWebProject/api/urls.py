from django.urls import path
from api.auth import Login
from api.menu import Menu
from .views import login_view, login_user_view, login_driver_view

urlpatterns = [
    path('login/', Login.as_view()),
    path('menu/', Menu.as_view()),
    path('login1/', login_view, name='api-login'),
    path('login/user/', login_user_view, name='api-login-user'),
    path('login/driver/', login_driver_view, name='api-login-driver'),
]
