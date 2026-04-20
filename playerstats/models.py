from django.db import models

# Create your models here.
class Player(models.Model):
    name = models.CharField(max_length=200)
    games = models.IntegerField()
    number = models.IntegerField()
    goals = models.IntegerField()
    assists = models.IntegerField()
    points = models.IntegerField()
    ranking = models.IntegerField()
