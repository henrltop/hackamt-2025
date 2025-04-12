from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_unidades, name='listar_unidades'),
    path('<int:pk>/', views.detalhe_unidade, name='detalhe_unidade'),
    path('nova/', views.adicionar_unidade, name='adicionar_unidade'),
    path('<int:pk>/editar/', views.editar_unidade, name='editar_unidade'),
]