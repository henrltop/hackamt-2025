from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import UnidadeSaude, Municipio
from .forms import UnidadeSaudeForm
from estoque.models import EstoqueImunobiologico

def listar_unidades(request):
    # Iniciar queryset
    unidades = UnidadeSaude.objects.all()
    
    # Aplicar filtros se fornecidos
    nome = request.GET.get('nome')
    if nome:
        unidades = unidades.filter(nome__icontains=nome)
    
    municipio_id = request.GET.get('municipio')
    if municipio_id:
        unidades = unidades.filter(municipio_id=municipio_id)
    
    ativo = request.GET.get('ativo')
    if ativo == '1':
        unidades = unidades.filter(ativa=True)
    elif ativo == '0':
        unidades = unidades.filter(ativa=False)
    
    # Ordenar por nome
    unidades = unidades.order_by('nome')
    
    # Paginação
    paginator = Paginator(unidades, 10)  # 10 unidades por página
    page_number = request.GET.get('page')
    unidades_paginadas = paginator.get_page(page_number)
    
    # Obter todos os municípios para o filtro
    municipios = Municipio.objects.all().order_by('uf', 'nome')
    
    context = {
        'unidades': unidades_paginadas,
        'municipios': municipios
    }
    
    return render(request, 'unidades/listar.html', context)

def detalhe_unidade(request, pk):
    unidade = get_object_or_404(UnidadeSaude, pk=pk)
    
    # Obter estoque da unidade
    estoques = EstoqueImunobiologico.objects.filter(unidade=unidade)
    estoque_vazio = not estoques.exists()
    
    context = {
        'unidade': unidade,
        'estoques': estoques,
        'estoque_vazio': estoque_vazio
    }
    
    return render(request, 'unidades/detalhes.html', context)

@login_required
def adicionar_unidade(request):
    # Verificar se o usuário é gestor ou admin
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = UnidadeSaudeForm(request.POST)
        if form.is_valid():
            unidade = form.save()
            messages.success(request, f"Unidade {unidade.nome} cadastrada com sucesso!")
            return redirect('listar_unidades')
    else:
        form = UnidadeSaudeForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'unidades/unidade_form.html', context)

@login_required
def editar_unidade(request, pk):
    # Verificar se o usuário é gestor ou admin
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    unidade = get_object_or_404(UnidadeSaude, pk=pk)
    
    # Se for gestor, verificar se é a unidade dele
    if request.user.perfilusuario.tipo == 'GESTOR' and request.user.perfilusuario.unidade_gestao != unidade:
        messages.error(request, "Você não tem permissão para editar esta unidade.")
        return redirect('listar_unidades')
    
    if request.method == 'POST':
        form = UnidadeSaudeForm(request.POST, instance=unidade)
        if form.is_valid():
            form.save()
            messages.success(request, f"Unidade {unidade.nome} atualizada com sucesso!")
            return redirect('detalhe_unidade', pk=unidade.pk)
    else:
        form = UnidadeSaudeForm(instance=unidade)
    
    context = {
        'form': form,
        'unidade': unidade
    }
    
    return render(request, 'unidades/unidade_form.html', context)