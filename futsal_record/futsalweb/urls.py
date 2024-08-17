# futsalweb/urls.py
from django.contrib import admin
from django.urls import path
from futsal_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # 기본 경로에서 home 뷰로 이동
    path('game/<int:game_id>/', views.game_overview, name='game_overview'),  # game_overview 뷰로 연결
    path('game/<int:game_id>/quarter/<int:quarter_number>/', views.quarter_detail, name='quarter_detail'),  # quarter_detail 뷰로 연결
]
