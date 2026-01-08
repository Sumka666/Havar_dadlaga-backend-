from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import User
from common.jwt import create_token
from common.passwords import hash_password, verify_password


class Login(APIView):

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response({"error": "Имэйл болон нууц үг шаардлагатай"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Хэрэглэгч олдсонгүй"}, status=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(password, user.password):
            return Response({"error": "Нууц үг буруу"}, status=status.HTTP_401_UNAUTHORIZED)

        # Create token without role payload (role not used in this project)
        token = create_token(user.id, None)
        return Response({
            "token": token,
            "user_id": user.id,
            "username": user.userName
        })




