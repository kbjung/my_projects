# futsalweb/urls.py
from django.contrib import admin
from django.urls import path
from futsal_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.game_overview, name='game_overview'),  # 초기 화면 URL
    path('game/<int:game_id>/', views.game_overview, name='game_overview'),
    path('game/<int:game_id>/quarter/<int:quarter_number>/', views.quarter_detail, name='quarter_detail'),
]
