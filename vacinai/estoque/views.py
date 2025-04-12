from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from .models import Lote, EstoqueImunobiologico, RegistroAbertura, TipoImunobiologico
from .forms import LoteForm, EstoqueForm, RegistroAberturaForm
from unidades.models import UnidadeSaude
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor ou todas as unidades para admin
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        if not unidade:
            messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
            return redirect('home')
        
        # Filtrar por unidade específica
        lotes_proximos_vencimento = Lote.objects.filter(
            estoqueimunobiologico__unidade=unidade,
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
            estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().order_by('data_validade')
        
        registros_abertos = RegistroAbertura.objects.filter(
            estoque__unidade=unidade,
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(days=1)
        ).order_by('data_hora_abertura')
        
        # Estatísticas para o dashboard
        total_vacinas = TipoImunobiologico.objects.filter(
            lote__estoqueimunobiologico__unidade=unidade,
            lote__estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().count()
        
        total_doses = sum([
            estoque.total_doses_disponiveis for estoque in 
            EstoqueImunobiologico.objects.filter(unidade=unidade)
        ])
        
        vacinas_vencendo = Lote.objects.filter(
            estoqueimunobiologico__unidade=unidade,
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
            estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().count()
        
        frascos_abertos = RegistroAbertura.objects.filter(
            estoque__unidade=unidade,
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(hours=48)
        ).count()
        
        # Dados de estoque por tipo de vacina
        estoques = []
        for tipo in TipoImunobiologico.objects.all():
            estoque_items = EstoqueImunobiologico.objects.filter(
                unidade=unidade,
                lote__tipo_imunobiologico=tipo
            )
            
            if estoque_items.exists():
                frascos = estoque_items.aggregate(total=Sum('quantidade_frascos'))['total'] or 0
                doses = sum([item.total_doses_disponiveis for item in estoque_items])
                
                estoques.append({
                    'vacina': tipo.nome,
                    'fabricante': tipo.fabricante,
                    'publico_alvo': tipo.get_publico_alvo_display(),
                    'frascos': frascos,
                    'doses': doses
                })
    else:
        # Para administradores, mostrar dados gerais
        lotes_proximos_vencimento = Lote.objects.filter(
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
            estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().order_by('data_validade')[:10]
        
        registros_abertos = RegistroAbertura.objects.filter(
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(days=1)
        ).order_by('data_hora_abertura')[:10]
        
        # Estatísticas para o dashboard
        total_vacinas = TipoImunobiologico.objects.count()
        
        total_doses = sum([
            estoque.total_doses_disponiveis for estoque in 
            EstoqueImunobiologico.objects.all()
        ])
        
        vacinas_vencendo = Lote.objects.filter(
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
            estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().count()
        
        frascos_abertos = RegistroAbertura.objects.filter(
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(hours=48)
        ).count()
        
        # Dados de estoque por tipo de vacina
        estoques = []
        for tipo in TipoImunobiologico.objects.all():
            estoque_items = EstoqueImunobiologico.objects.filter(
                lote__tipo_imunobiologico=tipo
            )
            
            if estoque_items.exists():
                frascos = estoque_items.aggregate(total=Sum('quantidade_frascos'))['total'] or 0
                doses = sum([item.total_doses_disponiveis for item in estoque_items])
                
                estoques.append({
                    'vacina': tipo.nome,
                    'fabricante': tipo.fabricante,
                    'publico_alvo': tipo.get_publico_alvo_display(),
                    'frascos': frascos,
                    'doses': doses
                })
    
    context = {
        'lotes_proximos_vencimento': lotes_proximos_vencimento,
        'registros_abertos': registros_abertos,
        'total_vacinas': total_vacinas,
        'total_doses': total_doses,
        'vacinas_vencendo': vacinas_vencendo,
        'frascos_abertos': frascos_abertos,
        'estoques': estoques
    }
    
    return render(request, 'estoque/dashboard.html', context)

@login_required
def listar_lotes(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Iniciar queryset de lotes
    lotes = Lote.objects.all().order_by('-data_cadastro')
    
    # Aplicar filtros se fornecidos
    vacina_id = request.GET.get('vacina')
    if vacina_id:
        lotes = lotes.filter(tipo_imunobiologico_id=vacina_id)
    
    status = request.GET.get('status')
    if status == 'valido':
        lotes = lotes.filter(data_validade__gt=timezone.now().date())
    elif status == 'vencendo':
        lotes = lotes.filter(
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30)
        )
    elif status == 'vencido':
        lotes = lotes.filter(data_validade__lt=timezone.now().date())
    
    numero_lote = request.GET.get('numero_lote')
    if numero_lote:
        lotes = lotes.filter(numero_lote__icontains=numero_lote)
    
    # Paginação
    paginator = Paginator(lotes, 10)  # 10 lotes por página
    page_number = request.GET.get('page')
    lotes_paginados = paginator.get_page(page_number)
    
    # Obter todos os tipos de imunobiológicos para o filtro
    tipos_imuno = TipoImunobiologico.objects.all()
    
    context = {
        'lotes': lotes_paginados,
        'tipos_imuno': tipos_imuno
    }
    
    return render(request, 'estoque/lotes.html', context)

@login_required
def novo_lote(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = LoteForm(request.POST)
        if form.is_valid():
            lote = form.save()
            messages.success(request, f"Lote {lote.numero_lote} cadastrado com sucesso!")
            return redirect('listar_lotes')
    else:
        form = LoteForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'estoque/lote_form.html', context)

@login_required
def detalhe_lote(request, pk):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    lote = get_object_or_404(Lote, pk=pk)
    estoques = EstoqueImunobiologico.objects.filter(lote=lote)
    
    context = {
        'lote': lote,
        'estoques': estoques
    }
    
    return render(request, 'estoque/detalhe_lote.html', context)

@login_required
def editar_lote(request, pk):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    lote = get_object_or_404(Lote, pk=pk)
    
    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lote {lote.numero_lote} atualizado com sucesso!")
            return redirect('detalhe_lote', pk=lote.pk)
    else:
        form = LoteForm(instance=lote)
    
    context = {
        'form': form,
        'lote': lote
    }
    
    return render(request, 'estoque/lote_form.html', context)

@login_required
def listar_estoque(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor ou todas as unidades para admin
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        if not unidade:
            messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
            return redirect('home')
        
        estoques = EstoqueImunobiologico.objects.filter(unidade=unidade)
    else:
        # Para administradores, mostrar estoque de todas as unidades
        estoques = EstoqueImunobiologico.objects.all()
    
    # Aplicar filtros se fornecidos
    vacina_id = request.GET.get('vacina')
    if vacina_id:
        estoques = estoques.filter(lote__tipo_imunobiologico_id=vacina_id)
    
    unidade_id = request.GET.get('unidade')
    if unidade_id and request.user.perfilusuario.tipo != 'GESTOR':
        estoques = estoques.filter(unidade_id=unidade_id)
    
    status = request.GET.get('status')
    if status == 'disponivel':
        estoques = estoques.filter(quantidade_frascos__gt=0)
    elif status == 'indisponivel':
        estoques = estoques.filter(quantidade_frascos=0)
    
    # Paginação
    paginator = Paginator(estoques, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    estoques_paginados = paginator.get_page(page_number)
    
    # Obter todos os tipos de imunobiológicos para o filtro
    tipos_imuno = TipoImunobiologico.objects.all()
    
    # Obter todas as unidades para o filtro (apenas para admin)
    unidades = None
    if request.user.perfilusuario.tipo != 'GESTOR':
        unidades = UnidadeSaude.objects.filter(ativa=True)
    
    context = {
        'estoques': estoques_paginados,
        'tipos_imuno': tipos_imuno,
        'unidades': unidades
    }
    
    return render(request, 'estoque/estoque.html', context)

@login_required
def atualizar_estoque(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        if not unidade:
            messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
            return redirect('home')
    else:
        # Para administradores, mostrar todas as unidades
        unidade = None
        if request.method != 'POST':
            unidades = UnidadeSaude.objects.filter(ativa=True)
            return render(request, 'estoque/selecionar_unidade.html', {'unidades': unidades})
    
    # Processar o formulário se for POST
    if request.method == 'POST':
        # Se admin, obter a unidade selecionada
        if request.user.perfilusuario.tipo != 'GESTOR':
            unidade_id = request.POST.get('unidade')
            if not unidade_id:
                messages.error(request, "Por favor, selecione uma unidade.")
                return redirect('atualizar_estoque')
            unidade = get_object_or_404(UnidadeSaude, pk=unidade_id)
        
        form = EstoqueForm(request.POST)
        if form.is_valid():
            estoque = form.save(commit=False)
            estoque.unidade = unidade
            
            # Verificar se já existe estoque para este lote nesta unidade
            estoque_existente = EstoqueImunobiologico.objects.filter(
                unidade=unidade,
                lote=estoque.lote
            ).first()
            
            if estoque_existente:
                # Atualizar estoque existente
                estoque_existente.quantidade_frascos += estoque.quantidade_frascos
                estoque_existente.save()
                messages.success(request, f"Estoque atualizado com sucesso! {estoque.quantidade_frascos} frascos adicionados.")
            else:
                # Criar novo registro de estoque
                estoque.save()
                messages.success(request, f"Estoque criado com sucesso! {estoque.quantidade_frascos} frascos adicionados.")
            
            return redirect('listar_estoque')
    else:
        form = EstoqueForm()
    
    context = {
        'form': form,
        'unidade': unidade
    }
    
    return render(request, 'estoque/atualizar_estoque.html', context)

@login_required
def atualizar_estoque_unidade(request, unidade_id):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter a unidade
    unidade = get_object_or_404(UnidadeSaude, pk=unidade_id)
    
    # Verificar se o gestor tem permissão para esta unidade
    if request.user.perfilusuario.tipo == 'GESTOR' and request.user.perfilusuario.unidade_gestao != unidade:
        messages.error(request, "Você não tem permissão para gerenciar esta unidade.")
        return redirect('listar_estoque')
    
    # Processar o formulário se for POST
    if request.method == 'POST':
        form = EstoqueForm(request.POST)
        if form.is_valid():
            estoque = form.save(commit=False)
            estoque.unidade = unidade
            
            # Verificar se já existe estoque para este lote nesta unidade
            estoque_existente = EstoqueImunobiologico.objects.filter(
                unidade=unidade,
                lote=estoque.lote
            ).first()
            
            if estoque_existente:
                # Atualizar estoque existente
                estoque_existente.quantidade_frascos += estoque.quantidade_frascos
                estoque_existente.save()
                messages.success(request, f"Estoque atualizado com sucesso! {estoque.quantidade_frascos} frascos adicionados.")
            else:
                # Criar novo registro de estoque
                estoque.save()
                messages.success(request, f"Estoque criado com sucesso! {estoque.quantidade_frascos} frascos adicionados.")
            
            return redirect('detalhe_unidade', pk=unidade.pk)
    else:
        form = EstoqueForm()
    
    context = {
        'form': form,
        'unidade': unidade
    }
    
    return render(request, 'estoque/atualizar_estoque.html', context)

@login_required
def listar_aberturas(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor ou todas as unidades para admin
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        if not unidade:
            messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
            return redirect('home')
        
        registros = RegistroAbertura.objects.filter(estoque__unidade=unidade)
    else:
        # Para administradores, mostrar registros de todas as unidades
        registros = RegistroAbertura.objects.all()
    
    # Aplicar filtros se fornecidos
    vacina_id = request.GET.get('vacina')
    if vacina_id:
        registros = registros.filter(estoque__lote__tipo_imunobiologico_id=vacina_id)
    
    unidade_id = request.GET.get('unidade')
    if unidade_id and request.user.perfilusuario.tipo != 'GESTOR':
        registros = registros.filter(estoque__unidade_id=unidade_id)
    
    status = request.GET.get('status')
    if status == 'valido':
        registros = registros.filter(
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(days=1)
        )
    elif status == 'vencido':
        registros = registros.filter(
            data_hora_abertura__lt=timezone.now() - timezone.timedelta(days=1)
        )
    
    # Ordenar por data de abertura (mais recentes primeiro)
    registros = registros.order_by('-data_hora_abertura')
    
    # Paginação
    paginator = Paginator(registros, 10)  # 10 registros por página
    page_number = request.GET.get('page')
    registros_paginados = paginator.get_page(page_number)
    
    # Obter todos os tipos de imunobiológicos para o filtro
    tipos_imuno = TipoImunobiologico.objects.all()
    
    # Obter todas as unidades para o filtro (apenas para admin)
    unidades = None
    if request.user.perfilusuario.tipo != 'GESTOR':
        unidades = UnidadeSaude.objects.filter(ativa=True)
    
    context = {
        'registros': registros_paginados,
        'tipos_imuno': tipos_imuno,
        'unidades': unidades
    }
    
    return render(request, 'estoque/registros.html', context)

@login_required
def registrar_abertura(request):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        if not unidade:
            messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
            return redirect('home')
    else:
        # Para administradores, mostrar todas as unidades
        unidade = None
        if request.method != 'POST':
            unidades = UnidadeSaude.objects.filter(ativa=True)
            return render(request, 'estoque/selecionar_unidade.html', {'unidades': unidades, 'acao': 'registrar_abertura'})
    
    # Processar o formulário se for POST
    if request.method == 'POST':
        # Se admin, obter a unidade selecionada
        if request.user.perfilusuario.tipo != 'GESTOR':
            unidade_id = request.POST.get('unidade')
            if not unidade_id:
                messages.error(request, "Por favor, selecione uma unidade.")
                return redirect('registrar_abertura')
            unidade = get_object_or_404(UnidadeSaude, pk=unidade_id)
        
        form = RegistroAberturaForm(request.POST, unidade=unidade)
        if form.is_valid():
            registro = form.save()
            messages.success(request, f"Abertura de frasco registrada com sucesso!")
            return redirect('listar_aberturas')
    else:
        form = RegistroAberturaForm(unidade=unidade)
    
    context = {
        'form': form,
        'unidade': unidade
    }
    
    return render(request, 'estoque/registro_abertura.html', context)

@login_required
def registrar_abertura_unidade(request, unidade_id):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter a unidade
    unidade = get_object_or_404(UnidadeSaude, pk=unidade_id)
    
    # Verificar se o gestor tem permissão para esta unidade
    if request.user.perfilusuario.tipo == 'GESTOR' and request.user.perfilusuario.unidade_gestao != unidade:
        messages.error(request, "Você não tem permissão para gerenciar esta unidade.")
        return redirect('listar_aberturas')
    
    # Processar o formulário se for POST
    if request.method == 'POST':
        form = RegistroAberturaForm(request.POST, unidade=unidade)
        if form.is_valid():
            registro = form.save()
            messages.success(request, f"Abertura de frasco registrada com sucesso!")
            return redirect('detalhe_unidade', pk=unidade.pk)
    else:
        form = RegistroAberturaForm(unidade=unidade)
    
    context = {
        'form': form,
        'unidade': unidade
    }
    
    return render(request, 'estoque/registro_abertura.html', context)

@login_required
def atualizar_registro_abertura(request, pk):
    # Verificar se o usuário é gestor
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter o registro
    registro = get_object_or_404(RegistroAbertura, pk=pk)
    
    # Verificar se o gestor tem permissão para esta unidade
    if request.user.perfilusuario.tipo == 'GESTOR' and request.user.perfilusuario.unidade_gestao != registro.estoque.unidade:
        messages.error(request, "Você não tem permissão para gerenciar este registro.")
        return redirect('listar_aberturas')
    
    # Processar o formulário se for POST
    if request.method == 'POST':
        form = RegistroAberturaForm(request.POST, instance=registro, unidade=registro.estoque.unidade)
        if form.is_valid():
            form.save()
            messages.success(request, f"Registro de abertura atualizado com sucesso!")
            return redirect('listar_aberturas')
    else:
        form = RegistroAberturaForm(instance=registro, unidade=registro.estoque.unidade)
    
    context = {
        'form': form,
        'registro': registro
    }
    
    return render(request, 'estoque/registro_abertura.html', context)