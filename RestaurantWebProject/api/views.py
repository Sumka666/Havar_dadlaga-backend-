from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password, make_password
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({'detail': 'Имэйл болон нууц үг шаардлагатай'}, status=status.HTTP_400_BAD_REQUEST)

    auth_result = _authenticate_credentials(email, password)
    if isinstance(auth_result, Response):
        return auth_result
    user, tokens = auth_result
    return Response({'success': True, 'message': 'Амжилттай нэвтэрлээ', 'tokens': tokens, 'user': {'userID': user.userID, 'userName': user.userName, 'email': user.email, 'role': getattr(user, 'role', None)}})


def _authenticate_credentials(email, password):
    """Authenticate by email/password. Returns (user, tokens) or a Response on error."""
    if not email or not password:
        return Response({'detail': 'Имэйл болон нууц үг шаардлагатай'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Хэрэглэгч олдсонгүй'}, status=status.HTTP_401_UNAUTHORIZED)

    password_ok = False
    try:
        password_ok = check_password(password, user.password)
    except Exception:
        password_ok = False

    # If stored password is plain and matches, migrate to hashed value
    if not password_ok and user.password == password:
        user.password = make_password(password)
        try:
            user.save(update_fields=['password'])
        except Exception:
            pass
        password_ok = True

    if not password_ok:
        return Response({'detail': 'Нууц үг буруу'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    tokens = {'refresh': str(refresh), 'access': str(refresh.access_token)}
    return user, tokens


@api_view(['POST'])
def login_user_view(request):
    """Login endpoint only for users with role 'user'. Missing role treated as user for compatibility."""
    email = request.data.get('email')
    password = request.data.get('password')
    auth_result = _authenticate_credentials(email, password)
    if isinstance(auth_result, Response):
        return auth_result
    user, tokens = auth_result
    # enforce role == 'user' if role exists
    if hasattr(user, 'role'):
        try:
            user_role = str(user.role).lower()
        except Exception:
            user_role = ''
        if user_role != 'user':
            return Response({'detail': 'Хандах зөвшөөрөлгүй: зөвхөн хэрэглэгч нэвтэрч болно'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'success': True, 'message': 'Амжилттай нэвтэрлээ', 'tokens': tokens, 'user': {'userID': user.userID, 'userName': user.userName, 'email': user.email, 'role': getattr(user, 'role', None)}})


@api_view(['POST'])
def login_driver_view(request):
    """Login endpoint only for users with role 'driver'."""
    email = request.data.get('email')
    password = request.data.get('password')
    auth_result = _authenticate_credentials(email, password)
    if isinstance(auth_result, Response):
        return auth_result
    user, tokens = auth_result
    if not hasattr(user, 'role'):
        return Response({'detail': 'Хэрэглэгчийн загвар дээр `role` талбар байхгүй тул жолоочийг шалгах боломжгүй'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_role = str(user.role).lower()
    except Exception:
        user_role = ''
    if user_role != 'driver':
        return Response({'detail': 'Хандах зөвшөөрөлгүй: зөвхөн жолооч нэвтрэх боломжтой'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'success': True, 'message': 'Амжилттай нэвтэрлээ', 'tokens': tokens, 'user': {'userID': user.userID, 'userName': user.userName, 'email': user.email, 'role': getattr(user, 'role', None)}})