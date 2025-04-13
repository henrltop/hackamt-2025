from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_unidades, name='listar_unidades'),
    path('<int:pk>/', views.detalhe_unidade, name='detalhe_unidade'),
    path('nova/', views.adicionar_unidade, name='adicionar_unidade'),
    path('<int:pk>/editar/', views.editar_unidade, name='editar_unidade'),
    # unidades/urls.py (adicionar)
    path('municipios/', views.listar_municipios, name='listar_municipios'),
    path('municipios/novo/', views.adicionar_municipio, name='adicionar_municipio'),
    path('municipios/<int:pk>/editar/', views.editar_municipio, name='editar_municipio'),
    path('bairros/', views.listar_bairros, name='listar_bairros'),
    path('bairros/novo/', views.adicionar_bairro, name='adicionar_bairro'),
    path('bairros/<int:pk>/editar/', views.editar_bairro, name='editar_bairro'),
    path('importar-cnes/', views.importar_unidades_cnes, name='importar_unidades_cnes'),
    path('api/bairros-por-municipio/<int:municipio_id>/', views.api_bairros_por_municipio, name='api_bairros_por_municipio'),
    ]