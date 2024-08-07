# futsal_app/views.py
from django.shortcuts import render
from .models import Game, Player, Quarter, Action  # Ensure this import is correct

def game_overview(request, game_id=None):
    if game_id:
        game = Game.objects.get(id=game_id)
        quarters = Quarter.objects.filter(game=game)
        players = Player.objects.filter(team=game)
        
        context = {
            'game': game,
            'quarters': quarters,
            'players': players,
        }
        return render(request, 'game_overview.html', context)
    else:
        games = Game.objects.all()
        context = {
            'games': games,
        }
        return render(request, 'home.html', context)

def quarter_detail(request, game_id, quarter_number):
    game = Game.objects.get(id=game_id)
    quarter = Quarter.objects.get(game=game, number=quarter_number)
    actions = Action.objects.filter(quarter=quarter)
    
    context = {
        'game': game,
        'quarter': quarter,
        'actions': actions,
    }
    return render(request, 'quarter_detail.html', context)
