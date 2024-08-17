# futsal_app/views.py
from django.shortcuts import render, get_object_or_404
from .models import Game, Quarter, Action, Player

def home(request):
    games = Game.objects.all()  # 모든 게임을 가져옴
    context = {
        'games': games,
    }
    return render(request, 'home.html', context)

def game_overview(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    quarter = game.quarters.first()  # 첫 번째 쿼터의 정보를 기본으로 가져옴
    actions = Action.objects.filter(quarter=quarter)
    
    context = {
        'game': game,
        'quarter': quarter,
        'actions': actions,
    }
    return render(request, 'game_overview.html', context)

def quarter_detail(request, game_id, quarter_number=1):
    game = get_object_or_404(Game, id=game_id)
    quarter = get_object_or_404(Quarter, game=game, number=quarter_number)
    players = Player.objects.filter(team=game)
    
    context = {
        'game': game,
        'quarter': quarter,
        'players': players,
    }
    return render(request, 'quarter_detail.html', context)
