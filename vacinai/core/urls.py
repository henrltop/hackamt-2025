from django.urls import path
from . import views

urlpatterns = [
    path('', views.mapa_vacinas, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    path('sobre/', views.sobre, name='sobre'),
    path('mapa/', views.mapa_vacinas, name='mapa'),
    path('admin/cadastros/', views.admin_cadastros, name='admin_cadastros'),
]