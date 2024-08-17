# futsal_app/models.py
from django.db import models

class Game(models.Model):
    date = models.DateField()
    location = models.CharField(max_length=100)
    opponent = models.CharField(max_length=100)
    total_wins = models.IntegerField()
    total_draws = models.IntegerField()
    total_losses = models.IntegerField()

    def __str__(self):
        return f"{self.date} {self.location} vs {self.opponent}"

class Quarter(models.Model):
    game = models.ForeignKey(Game, related_name='quarters', on_delete=models.CASCADE)
    number = models.IntegerField()
    score = models.CharField(max_length=10)

    def __str__(self):
        return f"Quarter {self.number}"

class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Game, related_name='players', on_delete=models.CASCADE)
    goals = models.IntegerField()
    assists = models.IntegerField()

    def __str__(self):
        return self.name

class Action(models.Model):
    quarter = models.ForeignKey(Quarter, related_name='actions', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name='actions', on_delete=models.CASCADE)
    goal_player = models.ForeignKey(Player, related_name='goal_actions', on_delete=models.CASCADE)
    assist_player = models.ForeignKey(Player, related_name='assist_actions', on_delete=models.CASCADE)
    goal_count = models.IntegerField()
    assist_count = models.IntegerField()
    timer = models.CharField(max_length=10)  # 예시용으로 타이머를 문자열로 저장

    def __str__(self):
        return f"Action by {self.player.name} in Quarter {self.quarter.number}"
