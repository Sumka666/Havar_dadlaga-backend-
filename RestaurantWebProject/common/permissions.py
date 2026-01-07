import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.conf import settings


class JWTAuthentication(BaseAuthentication):
	"""Simple JWT authentication for DRF views.

	Expects `Authorization: Bearer <token>` header. On success returns a
	lightweight `user` object (dict) with `id` and `role` available as
	`request.user` and the decoded token as `request.auth`.
	"""

	def authenticate(self, request):
		auth = request.META.get('HTTP_AUTHORIZATION', '')
		if not auth:
			return None

		parts = auth.split()
		if len(parts) != 2 or parts[0].lower() != 'bearer':
			raise exceptions.AuthenticationFailed('Invalid token header')

		token = parts[1]
		try:
			payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
		except jwt.ExpiredSignatureError:
			raise exceptions.AuthenticationFailed('Token has expired')
		except jwt.InvalidTokenError:
			raise exceptions.AuthenticationFailed('Invalid token')

		user = type('User', (), {})()
		user.id = payload.get('user_id')
		user.role = payload.get('role')

		return (user, payload)

