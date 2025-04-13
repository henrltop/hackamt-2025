from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm, GestorRegistrationForm
from unidades.models import Municipio, UnidadeSaude
from django.contrib.auth.models import User

@login_required
def cadastro(request):
    # Apenas administradores podem cadastrar novos usuários
    if not request.user.is_authenticated or request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Apenas administradores podem cadastrar novos usuários gestores.")
        return redirect('home')
        
    if request.method == 'POST':
        form = GestorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Atualizar perfil com dados adicionais
            user.perfilusuario.cpf = form.cleaned_data.get('cpf')
            user.perfilusuario.data_nascimento = form.cleaned_data.get('data_nascimento')
            user.perfilusuario.telefone = form.cleaned_data.get('telefone')
            user.perfilusuario.municipio = form.cleaned_data.get('municipio')
            user.perfilusuario.tipo = 'GESTOR'  # Define o tipo como GESTOR
            user.perfilusuario.unidade_gestao = form.cleaned_data.get('unidade_gestao')  # Vincula à UBS
            user.perfilusuario.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta de gestor criada para {username}! O usuário já pode fazer login.')
            return redirect('listar_usuarios')
    else:
        form = GestorRegistrationForm()
    
    return render(request, 'usuarios/cadastro.html', {'form': form, 'title': 'Cadastrar Novo Gestor'})

@login_required
def perfil(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.perfilusuario)
        
        if u_form.is_valid() and p_form.is_valid():
            # Garantir que não altere a UBS vinculada sem permissão adequada
            if request.user.perfilusuario.tipo != 'ADMIN':
                p_form.instance.unidade_gestao = request.user.perfilusuario.unidade_gestao
                p_form.instance.tipo = request.user.perfilusuario.tipo
            
            u_form.save()
            p_form.save()
            messages.success(request, 'Seu perfil foi atualizado!')
            return redirect('perfil')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.perfilusuario)
        
        # Desabilitar campos de UBS e tipo para não-admins
        if request.user.perfilusuario.tipo != 'ADMIN':
            p_form.fields['unidade_gestao'].disabled = True
            p_form.fields['tipo'].disabled = True
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'usuarios/perfil.html', context)

@login_required
def alterar_senha(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Manter o usuário logado
            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'usuarios/alterar_senha.html', {'form': form})

@login_required
def cadastrar_gestor(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = GestorRegistrationForm(request.POST)
        if form.is_valid():
            # Criar o usuário
            user = form.save()
            
            # Atualizar o perfil para GESTOR
            user.perfilusuario.tipo = 'GESTOR'
            user.perfilusuario.unidade_gestao = form.cleaned_data.get('unidade_gestao')
            user.perfilusuario.cpf = form.cleaned_data.get('cpf')
            user.perfilusuario.data_nascimento = form.cleaned_data.get('data_nascimento')
            user.perfilusuario.telefone = form.cleaned_data.get('telefone')
            user.perfilusuario.municipio = form.cleaned_data.get('municipio')
            user.perfilusuario.save()
            
            messages.success(request, f'Conta de gestor criada para {user.username}!')
            return redirect('listar_usuarios')
    else:
        form = GestorRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Cadastrar Gestor de UBS'
    }
    return render(request, 'usuarios/cadastrar_gestor.html', context)

@login_required
def listar_usuarios(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    usuarios_gestores = User.objects.filter(perfilusuario__tipo='GESTOR').select_related('perfilusuario__unidade_gestao')
    
    context = {
        'usuarios': usuarios_gestores,
        'title': 'Gestores de UBS'
    }
    return render(request, 'usuarios/listar_usuarios.html', context)