from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import User
from common.jwt import create_token
from common.passwords import hash_password, verify_password


class Login(APIView):

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response({"error": "username болон password шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(userName=username).first()
        if not user:
            return Response({"error": "Хэрэглэгч олдсонгүй"}, status=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(password, user.password):
            return Response({"error": "Нууц үг буруу"}, status=status.HTTP_401_UNAUTHORIZED)

        # Role distinction
        if user.role == "driver":
            role_text = "Жолооч"
        elif user.role == "customer":
            role_text = "Хэрэглэгч"
        else:
            role_text = user.role

        token = create_token(user.id, user.role)
        return Response({
            "token": token,
            "role": user.role,
            "role_text": role_text,
            "user_id": user.id,
            "username": user.userName
        })




