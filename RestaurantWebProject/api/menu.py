from rest_framework.views import APIView
from rest_framework.response import Response
from api.db import restaurant_db
from common.jwt import decode_token

class Menu(APIView):

    def get(self, request):
        db = restaurant_db()
        cur = db.cursor()
        cur.execute("SELECT id,name,price FROM menu")
        return Response(cur.fetchall())

    def post(self, request):
        token = request.headers['Authorization'].split()[1]
        role = decode_token(token)['role']

        if role != 'staff':
            return Response({"error": "forbidden"}, status=403)

        db = restaurant_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO menu (name,price) VALUES (?,?)",
            (request.data['name'], request.data['price'])
        )
        db.commit()
        return Response({"message": "menu added"})
