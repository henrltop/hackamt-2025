from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.forms import modelformset_factory
from .models import Notificacao, PreferenciaNotificacao
from .forms import PreferenciaNotificacaoForm
from estoque.models import TipoImunobiologico
from unidades.models import Municipio

@login_required
def listar_notificacoes(request):
    # Obter notificações do usuário, ordenadas por data (mais recentes primeiro)
    notificacoes = Notificacao.objects.filter(usuario=request.user).order_by('-data_envio')
    
    # Verificar se há notificações não lidas
    not_all_read = notificacoes.filter(lida=False).exists()
    
    # Paginação
    paginator = Paginator(notificacoes, 10)  # 10 notificações por página
    page_number = request.GET.get('page')
    notificacoes_paginadas = paginator.get_page(page_number)
    
    context = {
        'notificacoes': notificacoes_paginadas,
        'not_all_read': not_all_read
    }
    
    return render(request, 'notificacoes/listar.html', context)

@login_required
def marcar_lida(request, pk):
    # Obter a notificação
    notificacao = get_object_or_404(Notificacao, pk=pk, usuario=request.user)
    
    # Marcar como lida
    notificacao.lida = True
    notificacao.save()
    
    # Redirecionar de volta para a lista de notificações
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/notificacoes/'))

@login_required
def marcar_todas_lidas(request):
    # Marcar todas as notificações do usuário como lidas
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    
    messages.success(request, "Todas as notificações foram marcadas como lidas.")
    
    # Redirecionar de volta para a lista de notificações
    return redirect('notificacoes')

@login_required
def preferencias_notificacao(request):
    # Obter todas as preferências do usuário
    preferencias = PreferenciaNotificacao.objects.filter(usuario=request.user)
    
    # Criar formset para editar todas as preferências de uma vez
    PreferenciaFormSet = modelformset_factory(
        PreferenciaNotificacao,
        fields=('id', 'usuario', 'tipo_imunobiologico', 'municipio', 'notificar_email', 'notificar_app'),
        extra=0
    )
    
    if request.method == 'POST':
        formset = PreferenciaFormSet(request.POST, queryset=preferencias)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Preferências de notificação atualizadas com sucesso!")
            return redirect('preferencias_notificacao')
    else:
        formset = PreferenciaFormSet(queryset=preferencias)
    
    # Formulário para adicionar nova preferência
    form_new = PreferenciaNotificacaoForm()
    
    context = {
        'forms': formset,
        'form_new': form_new
    }
    
    return render(request, 'notificacoes/preferencias.html', context)

@login_required
def adicionar_preferencia(request):
    if request.method == 'POST':
        form = PreferenciaNotificacaoForm(request.POST)
        if form.is_valid():
            # Verificar se já existe preferência para esta vacina e município
            tipo_imunobiologico = form.cleaned_data['tipo_imunobiologico']
            municipio = form.cleaned_data['municipio']
            
            # Verificar se a preferência já existe
            preferencia_existente = PreferenciaNotificacao.objects.filter(
                usuario=request.user,
                tipo_imunobiologico=tipo_imunobiologico,
                municipio=municipio
            ).exists()
            
            if preferencia_existente:
                messages.warning(request, "Esta preferência já existe.")
            else:
                # Criar nova preferência
                preferencia = form.save(commit=False)
                preferencia.usuario = request.user
                preferencia.save()
                messages.success(request, "Preferência de notificação adicionada com sucesso!")
            
            return redirect('preferencias_notificacao')
    
    # Redirecionar de volta para a página de preferências se não for POST
    return redirect('preferencias_notificacao')