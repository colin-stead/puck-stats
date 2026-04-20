from django.db import models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    wins = models.IntegerField()
    losses = models.IntegerField()
    overtime_losses = models.IntegerField()
    points = models.IntegerField()
    rank = models.IntegerField()
