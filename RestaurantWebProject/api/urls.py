from django.urls import path
from api.auth import Login, Register
from api.menu import Menu

urlpatterns = [
    path('login/', Login.as_view()),
    path('register/', Register.as_view()),
    path('menu/', Menu.as_view()),
]
