from api.db import get_db
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.permissions import JWTAuthentication


class Menu(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        # require authentication
        if not getattr(request, 'user', None):
            return Response({'error': 'authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id,name,price FROM menu")
        rows = cur.fetchall()

        # Convert sqlite row tuples into dicts for clearer API responses
        result = [{'id': r[0], 'name': r[1], 'price': r[2]} for r in rows]
        return Response(result)
