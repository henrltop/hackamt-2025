from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('lotes/', views.listar_lotes, name='listar_lotes'),
    path('lotes/novo/', views.novo_lote, name='novo_lote'),
    path('lotes/<int:pk>/', views.detalhe_lote, name='detalhe_lote'),
    path('lotes/<int:pk>/editar/', views.editar_lote, name='editar_lote'),
    path('estoque/', views.listar_estoque, name='listar_estoque'),
    path('estoque/atualizar/', views.atualizar_estoque, name='atualizar_estoque'),
    path('estoque/atualizar/<int:unidade_id>/', views.atualizar_estoque_unidade, name='atualizar_estoque_unidade'),
    path('registros/', views.listar_aberturas, name='listar_aberturas'),
    path('registros/novo/', views.registrar_abertura, name='registrar_abertura'),
    path('registros/novo/<int:unidade_id>/', views.registrar_abertura_unidade, name='registrar_abertura_unidade'),
    path('registros/<int:pk>/', views.atualizar_registro_abertura, name='atualizar_registro_abertura'),
]