from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User

@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    # currently passwords are plaintext in your model — consider hashing in future
    if user.password != password:
        return Response({'detail': 'invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'success': True, 'user': {'userID': user.userID, 'userName': user.userName, 'email': user.email}})