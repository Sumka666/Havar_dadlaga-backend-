from django.db import models


class User(models.Model):
	username = models.CharField(max_length=150, unique=True)
	password = models.CharField(max_length=128)
	# default role changed to an allowed value ('customer') to match DB CHECK
	role = models.CharField(max_length=30, default='customer')

	def __str__(self):
		return self.username
