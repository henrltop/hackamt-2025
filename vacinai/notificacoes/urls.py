from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_notificacoes, name='notificacoes'),
    path('<int:pk>/lida/', views.marcar_lida, name='marcar_lida'),
    path('marcar-todas/', views.marcar_todas_lidas, name='marcar_todas_lidas'),
    path('preferencias/', views.preferencias_notificacao, name='preferencias_notificacao'),
    path('preferencias/adicionar/', views.adicionar_preferencia, name='adicionar_preferencia'),
]