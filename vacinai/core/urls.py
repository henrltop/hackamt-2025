from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('mapa/', views.mapa_vacinas, name='mapa'),
    path('admin/cadastros/', views.admin_cadastros, name='admin_cadastros'),
]