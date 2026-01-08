from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import User
from common.jwt import create_token
import bcrypt


class Login(APIView):
    """Login view that returns a JWT when credentials are valid.

    Uses the Django `User` model from `api.models` and returns a token
    including the user's `role` (e.g., `customer` or `driver`).
    """

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        stored_password = user.password or ''

        ok = False
        if isinstance(stored_password, str) and stored_password.startswith('$2'):
            try:
                ok = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
            except Exception:
                ok = False
        else:
            ok = (password == stored_password)

        if not ok:
            return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token = create_token(user.id, user.role)
        return Response({"token": token})


class Register(APIView):
    """Register a new user and store a bcrypt-hashed password.

    Validates `role` (defaults to `customer`) and uses the Django ORM to
    create the `User` model instance.
    """

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        role = (request.data.get('role') or '').strip().lower()

        allowed_roles = {'customer', 'driver'}

        if not username or not password:
            return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        if not role:
            role = 'customer'
        if role not in allowed_roles:
            return Response({"error": "invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "username exists"}, status=status.HTTP_400_BAD_REQUEST)

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user = User.objects.create(username=username, password=hashed, role=role)
        return Response({"status": "created", "id": user.id}, status=status.HTTP_201_CREATED)
