from django.urls import path
from api.auth import Login
from api.menu import Menu

urlpatterns = [
    path('login/', Login.as_view()),
    path('menu/', Menu.as_view()),
]
