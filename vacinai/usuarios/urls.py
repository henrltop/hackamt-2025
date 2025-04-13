from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.cadastrar_gestor, name='cadastro'),  # Redireciona para a função de cadastrar gestor
    path('perfil/', views.perfil, name='perfil'),
    path('senha/', views.alterar_senha, name='alterar_senha'),
    path('cadastrar-gestor/', views.cadastrar_gestor, name='cadastrar_gestor'),
    path('listar-usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('editar-usuario/<int:pk>/', views.editar_usuario, name='editar_usuario'),
]