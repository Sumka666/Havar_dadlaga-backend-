from rest_framework.views import APIView
from rest_framework.response import Response
from api.db import auth_db
from common.jwt import create_token

class Login(APIView):
    def post(self, request):
        u = request.data.get('username')
        p = request.data.get('password')

        db = auth_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, role FROM users WHERE username=? AND password=?",
            (u, p)
        )
        row = cur.fetchone()

        if not row:
            return Response({"error": "invalid"}, status=401)

        return Response({
            "token": create_token(row[0], row[1])
        })
