from django.db import models

class Game(models.Model):
    date = models.DateField()
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    
class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Game, on_delete=models.CASCADE)

class Quarter(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    number = models.IntegerField()
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)

class Action(models.Model):
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=10)  # 'goal' or 'assist'
    timestamp = models.TimeField()