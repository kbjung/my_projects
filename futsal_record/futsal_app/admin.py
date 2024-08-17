# futsal_app/admin.py
from django.contrib import admin
from futsal_app.models import Game, Quarter, Player, Action

admin.site.register(Game)
admin.site.register(Quarter)
admin.site.register(Player)
admin.site.register(Action)
