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
    path('distribuir/', views.distribuir_vacinas, name='distribuir_vacinas'),
    path('distribuir/salvar/', views.salvar_distribuicao, name='salvar_distribuicao'),

    # Para registro de abertura (UBS)
    path('registro-abertura/', views.registrar_abertura, name='registrar_abertura'),
    path('registro-abertura/salvar/', views.salvar_abertura, name='salvar_abertura'),

    # APIs para os selects dinâmicos
    path('api/lotes-por-tipo/<int:tipo_id>/', views.api_lotes_por_tipo, name='api_lotes_por_tipo'),
    path('api/lotes-ubs-por-tipo/<int:tipo_id>/', views.api_lotes_ubs_por_tipo, name='api_lotes_ubs_por_tipo'),
    path('api/estoque-ubs-por-lote/<int:lote_id>/', views.api_estoque_ubs_por_lote, name='api_estoque_ubs_por_lote'),
    path('api/lote-info/<int:lote_id>/', views.api_lote_info, name='api_lote_info'),
    
    # Relatórios
    path('relatorios/', views.relatorios, name='relatorios'),
    path('relatorios/estoque/', views.relatorio_estoque, name='relatorio_estoque'),
    path('relatorios/estoque/unidade/<int:unidade_id>/', views.relatorio_estoque_unidade, name='relatorio_estoque_unidade'),
    path('relatorios/distribuicao/', views.relatorio_distribuicao, name='relatorio_distribuicao'),
    path('relatorios/aplicacoes/', views.relatorio_aplicacoes, name='relatorio_aplicacoes'),
    path('relatorios/vencimentos/', views.relatorio_vencimentos, name='relatorio_vencimentos'),
    path('relatorios/eficiencia/', views.relatorio_eficiencia, name='relatorio_eficiencia'),
    path('relatorios/personalizado/', views.relatorio_personalizado, name='relatorio_personalizado'),

    # Tipos de Imunobiológicos
    path('tipos-imunobiologicos/', views.listar_tipos_imunobiologicos, name='listar_tipos_imunobiologicos'),
    path('tipos-imunobiologicos/novo/', views.novo_tipo_imunobiologico, name='novo_tipo_imunobiologico'),
    path('tipos-imunobiologicos/<int:pk>/', views.detalhe_tipo_imunobiologico, name='detalhe_tipo_imunobiologico'),
    path('tipos-imunobiologicos/<int:pk>/editar/', views.editar_tipo_imunobiologico, name='editar_tipo_imunobiologico'),
]