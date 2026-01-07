from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.db import auth_db
from common.jwt import create_token
import bcrypt


class Login(APIView):
    """Login view that returns a JWT when credentials are valid.

    Expects JSON body with `username` and `password`.
    """

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        db = auth_db()
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT id, role, password FROM users WHERE username=?",
                (username,)
            )
            row = cur.fetchone()

            if not row:
                return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            user_id, role, stored_password = row[0], row[1], row[2]

            # stored_password may be bcrypt-hashed or plaintext (legacy).
            ok = False
            if isinstance(stored_password, str) and stored_password.startswith('$2'):
                try:
                    ok = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    ok = False
            else:
                # legacy plaintext fallback
                ok = (password == stored_password)

            if not ok:
                return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            token = create_token(user_id, role)
            return Response({"token": token})
        finally:
            try:
                db.close()
            except Exception:
                pass


class Register(APIView):
    """Register a new user and store a bcrypt-hashed password.

    Expects JSON body with `username` and `password`. Returns 201 on success.
    """

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        db = auth_db()
        cur = db.cursor()
        try:
            # ensure username is unique
            cur.execute("SELECT id FROM users WHERE username=?", (username,))
            if cur.fetchone():
                return Response({"error": "username exists"}, status=status.HTTP_400_BAD_REQUEST)

            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_str = hashed.decode('utf-8')

            # default role is 'customer' (must match DB CHECK constraint)
            cur.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (username, hashed_str, 'customer'))
            db.commit()
            return Response({"status": "created"}, status=status.HTTP_201_CREATED)
        finally:
            try:
                db.close()
            except Exception:
                pass
