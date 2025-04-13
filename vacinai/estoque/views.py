from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Lote, EstoqueImunobiologico, RegistroAbertura, TipoImunobiologico, DistribuicaoLote
from .forms import LoteForm, EstoqueForm, RegistroAberturaForm, TipoImunobiologicoForm
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
    
    # Calcular informações relevantes
    doses_disponiveis = lote.quantidade_frascos_central * lote.tipo_imunobiologico.doses_por_frasco
    frascos_distribuidos = lote.quantidade_frascos - lote.quantidade_frascos_central
    now = timezone.now().date()
    
    context = {
        'lote': lote,
        'estoques': estoques,
        'doses_disponiveis': doses_disponiveis,
        'frascos_distribuidos': frascos_distribuidos,
        'now': now
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
    
    # Ordenar por validade (mais próximos do vencimento primeiro)
    estoques = estoques.order_by('lote__data_validade', 'lote__tipo_imunobiologico__nome')
    
    # Anexar informações adicionais aos lotes para facilitar o template
    now = timezone.now().date()
    for estoque in estoques:
        # Calcular os dias até o vencimento
        estoque.lote.dias_ate_vencimento = (estoque.lote.data_validade - now).days
        
        # Não é mais necessário calcular o total_doses_disponiveis aqui
        # Isso agora é uma property do modelo EstoqueImunobiologico
    
    # Paginação
    paginator = Paginator(estoques, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    estoques_paginados = paginator.get_page(page_number)
    
    # Obter todos os tipos de imunobiológicos para o filtro
    tipos_imuno = TipoImunobiologico.objects.all().order_by('nome')
    
    # Obter todas as unidades para o filtro (apenas para admin)
    unidades = None
    if request.user.perfilusuario.tipo != 'GESTOR':
        unidades = UnidadeSaude.objects.filter(ativa=True).order_by('nome')
    
    # Construir a string de consulta para a paginação
    request_query = ''
    for key, value in request.GET.items():
        if key != 'page':
            request_query += f'&{key}={value}'
    
    context = {
        'estoques': estoques_paginados,
        'tipos_imuno': tipos_imuno,
        'unidades': unidades,
        'request_query': request_query,
        'now': now,
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
            
            # VALIDAÇÃO DE SEGURANÇA: Verificar se a quantidade é válida
            if estoque.quantidade_frascos <= 0:
                messages.error(request, "A quantidade de frascos deve ser maior que zero.")
                return render(request, 'estoque/atualizar_estoque.html', {'form': form, 'unidade': unidade})
            
            # VALIDAÇÃO DE SEGURANÇA: Verificar se o lote não está vencido
            if estoque.lote.data_validade < timezone.now().date():
                messages.error(request, "Não é possível adicionar lotes já vencidos.")
                return render(request, 'estoque/atualizar_estoque.html', {'form': form, 'unidade': unidade})
            
            # VALIDAÇÃO DE SEGURANÇA: Verificar se há frascos suficientes no estoque central
            if estoque.lote.quantidade_frascos_central < estoque.quantidade_frascos:
                messages.error(request, f"Quantidade insuficiente no estoque central. Disponível: {estoque.lote.quantidade_frascos_central} frascos.")
                return render(request, 'estoque/atualizar_estoque.html', {'form': form, 'unidade': unidade})
            
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
            
            # Atualizar o estoque central
            estoque.lote.quantidade_frascos_central -= estoque.quantidade_frascos
            estoque.lote.save()
            
            # Registrar a distribuição para rastreabilidade
            DistribuicaoLote.objects.create(
                lote=estoque.lote,
                unidade=unidade,
                quantidade_frascos=estoque.quantidade_frascos,
                data_distribuicao=timezone.now(),
                usuario=request.user,
                observacoes=f"Distribuição realizada via formulário de atualização de estoque."
            )
            
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
    # Verificar se o usuário é gestor de estoque
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
    # Verificar se o usuário é gestor de UBS
    if request.user.perfilusuario.tipo != 'GESTOR':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor
    unidade = request.user.perfilusuario.unidade_gestao
    if not unidade:
        messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
        return redirect('home')
    
    # Se um estoque específico foi fornecido na URL
    estoque_id = request.GET.get('estoque')
    estoque_selecionado = None
    
    if estoque_id:
        try:
            estoque_selecionado = EstoqueImunobiologico.objects.get(
                id=estoque_id,
                unidade=unidade,
                quantidade_frascos__gt=0,
                lote__data_validade__gte=timezone.now().date()
            )
        except EstoqueImunobiologico.DoesNotExist:
            messages.error(request, "Estoque selecionado não existe ou não está disponível.")
            estoque_selecionado = None
    
    # Obter tipos de imunobiológicos disponíveis na UBS
    tipos_imuno = TipoImunobiologico.objects.filter(
        lote__estoqueimunobiologico__unidade=unidade,
        lote__estoqueimunobiologico__quantidade_frascos__gt=0,
        lote__data_validade__gte=timezone.now().date()
    ).distinct().order_by('nome')
    
    if request.method == 'POST':
        # Extrair dados do formulário
        estoque_id = request.POST.get('estoque_id')
        data_hora_abertura = request.POST.get('data_hora_abertura')
        responsavel = request.POST.get('responsavel')
        doses_aplicadas_imediatas = int(request.POST.get('doses_aplicadas_imediatas', 0))
        motivo_abertura = request.POST.get('motivo_abertura')
        outro_motivo = request.POST.get('outro_motivo', '')
        observacoes = request.POST.get('observacoes', '')
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar se todos os campos obrigatórios estão preenchidos
        if not all([estoque_id, data_hora_abertura, responsavel, motivo_abertura]):
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            return redirect('registrar_abertura')
        
        # Obter o estoque
        try:
            estoque = EstoqueImunobiologico.objects.get(pk=estoque_id)
        except EstoqueImunobiologico.DoesNotExist:
            messages.error(request, "Estoque não encontrado.")
            return redirect('registrar_abertura')
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar se pertence à unidade do gestor
        if estoque.unidade != unidade:
            messages.error(request, "Você não tem permissão para manipular este estoque.")
            return redirect('registrar_abertura')
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar se ainda há frascos disponíveis
        if estoque.quantidade_frascos <= 0:
            messages.error(request, "Não há frascos disponíveis neste lote.")
            return redirect('registrar_abertura')
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar se o lote não está vencido
        if estoque.lote.data_validade < timezone.now().date():
            messages.error(request, "Não é possível abrir frascos de lotes vencidos.")
            return redirect('registrar_abertura')
        
        # VALIDAÇÃO DE SEGURANÇA: Verificar se as doses aplicadas imediatas não excedem o máximo do frasco
        if doses_aplicadas_imediatas > estoque.lote.tipo_imunobiologico.doses_por_frasco:
            messages.error(request, f"O número de doses aplicadas não pode exceder o máximo por frasco ({estoque.lote.tipo_imunobiologico.doses_por_frasco}).")
            return redirect('registrar_abertura')
        
        # Montar descrição do motivo
        if motivo_abertura == 'OUTRO':
            motivo_descricao = outro_motivo
        else:
            motivos_dict = {
                'DEMANDA': 'Atendimento de demanda',
                'CAMPANHA': 'Campanha de vacinação',
                'AGENDAMENTO': 'Agendamento prévio'
            }
            motivo_descricao = motivos_dict.get(motivo_abertura, motivo_abertura)
        
        # Registrar a abertura com transação para garantir integridade
        try:
            with transaction.atomic():
                # Registrar a abertura
                abertura = RegistroAbertura.objects.create(
                    estoque=estoque,
                    data_hora_abertura=data_hora_abertura,
                    responsavel=responsavel,
                    doses_utilizadas=doses_aplicadas_imediatas,
                    doses_perdidas=0,  # Inicialmente não há doses perdidas
                    motivo=motivo_descricao,
                    observacoes=observacoes,
                    usuario=request.user
                )
                
                # Reduzir a quantidade de frascos disponíveis
                estoque.quantidade_frascos -= 1
                estoque.save()
                
                messages.success(request, "Abertura de frasco registrada com sucesso!")
                
                # Se houve aplicações imediatas, redirecionar para registrar as aplicações
                if doses_aplicadas_imediatas > 0:
                    return redirect('registrar_aplicacao_abertura', abertura_id=abertura.id)
                
                return redirect('listar_aberturas')
        except Exception as e:
            messages.error(request, f"Erro ao registrar abertura: {str(e)}")
            return redirect('registrar_abertura')
    
    context = {
        'tipos_imuno': tipos_imuno,
        'unidade': unidade,
        'estoque_selecionado': estoque_selecionado
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

@login_required
def distribuir_vacinas(request):
    # Verificar se o usuário é administrador
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter tipos de imunobiológicos e unidades de saúde
    tipos_imuno = TipoImunobiologico.objects.all().order_by('nome')
    unidades_saude = UnidadeSaude.objects.filter(ativa=True).order_by('nome')
    
    context = {
        'tipos_imuno': tipos_imuno,
        'unidades_saude': unidades_saude
    }
    
    return render(request, 'estoque/distribuir_vacinas.html', context)

@login_required
def salvar_distribuicao(request):
    # Verificar se o usuário é administrador
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        lote_id = request.POST.get('lote_id')
        observacoes = request.POST.get('observacoes', '')
        
        # Obter o lote
        lote = get_object_or_404(Lote, pk=lote_id)
        
        # Calcular total a ser distribuído
        total_distribuir = 0
        for key, value in request.POST.items():
            if key.startswith('quantidade_') and int(value) > 0:
                total_distribuir += int(value)
        
        # Verificar se há frascos suficientes
        if total_distribuir > lote.quantidade_frascos_central:
            messages.error(request, f"Quantidade insuficiente no estoque central. Disponível: {lote.quantidade_frascos_central} frascos.")
            return redirect('distribuir_vacinas')
        
        # Registrar distribuições para cada UBS
        distribuicoes_realizadas = 0
        
        for key, value in request.POST.items():
            if key.startswith('quantidade_') and int(value) > 0:
                ubs_id = key.replace('quantidade_', '')
                quantidade = int(value)
                
                # Obter a UBS
                ubs = get_object_or_404(UnidadeSaude, pk=ubs_id)
                
                # Verificar se já existe estoque para este lote na UBS
                estoque_existente = EstoqueImunobiologico.objects.filter(
                    unidade=ubs,
                    lote=lote
                ).first()
                
                if estoque_existente:
                    # Atualizar estoque existente
                    estoque_existente.quantidade_frascos += quantidade
                    estoque_existente.save()
                else:
                    # Criar novo registro de estoque
                    EstoqueImunobiologico.objects.create(
                        unidade=ubs,
                        lote=lote,
                        quantidade_frascos=quantidade
                    )
                
                # Registrar a distribuição
                DistribuicaoLote.objects.create(
                    lote=lote,
                    unidade=ubs,
                    quantidade_frascos=quantidade,
                    data_distribuicao=timezone.now(),
                    usuario=request.user,
                    observacoes=observacoes
                )
                
                distribuicoes_realizadas += 1
        
        # Reduzir a quantidade do estoque central
        lote.quantidade_frascos_central -= total_distribuir
        lote.save()
        
        # Atualizar quantidade total
        lote.atualizar_quantidade_total()
        
        if distribuicoes_realizadas > 0:
            messages.success(request, f"Distribuição realizada com sucesso para {distribuicoes_realizadas} unidades de saúde!")
        else:
            messages.warning(request, "Nenhuma distribuição foi realizada. Verifique as quantidades informadas.")
        
        return redirect('listar_lotes')
    
    return redirect('distribuir_vacinas')

@login_required
def registrar_abertura(request):
    # Verificar se o usuário é gestor de UBS
    if request.user.perfilusuario.tipo != 'GESTOR':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter unidade do gestor
    unidade = request.user.perfilusuario.unidade_gestao
    if not unidade:
        messages.warning(request, "Você não está associado a nenhuma unidade de saúde.")
        return redirect('home')
    
    # Obter tipos de imunobiológicos disponíveis na UBS
    tipos_imuno = TipoImunobiologico.objects.filter(
        lote__estoqueimunobiologico__unidade=unidade,
        lote__estoqueimunobiologico__quantidade_frascos__gt=0
    ).distinct().order_by('nome')
    
    context = {
        'tipos_imuno': tipos_imuno,
        'unidade': unidade
    }
    
    return render(request, 'estoque/registro_abertura.html', context)

@login_required
def salvar_abertura(request):
    # Verificar se o usuário é gestor de UBS
    if request.user.perfilusuario.tipo != 'GESTOR':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        estoque_id = request.POST.get('estoque_id')
        data_hora_abertura = request.POST.get('data_hora_abertura')
        responsavel = request.POST.get('responsavel')
        doses_aplicadas_imediatas = int(request.POST.get('doses_aplicadas_imediatas', 0))
        motivo_abertura = request.POST.get('motivo_abertura')
        outro_motivo = request.POST.get('outro_motivo', '')
        observacoes = request.POST.get('observacoes', '')
        
        # Obter o estoque
        estoque = get_object_or_404(EstoqueImunobiologico, pk=estoque_id)
        
        # Verificar se pertence à unidade do gestor
        if estoque.unidade != request.user.perfilusuario.unidade_gestao:
            messages.error(request, "Você não tem permissão para manipular este estoque.")
            return redirect('registrar_abertura')
        
        # Verificar se ainda há frascos disponíveis
        if estoque.quantidade_frascos <= 0:
            messages.error(request, "Não há frascos disponíveis neste lote.")
            return redirect('registrar_abertura')
        
        # Montar descrição do motivo
        if motivo_abertura == 'OUTRO':
            motivo_descricao = outro_motivo
        else:
            motivos_dict = {
                'DEMANDA': 'Atendimento de demanda',
                'CAMPANHA': 'Campanha de vacinação',
                'AGENDAMENTO': 'Agendamento prévio'
            }
            motivo_descricao = motivos_dict.get(motivo_abertura, motivo_abertura)
        
        # Registrar a abertura
        abertura = RegistroAbertura.objects.create(
            estoque=estoque,
            data_hora_abertura=data_hora_abertura,
            responsavel=responsavel,
            doses_utilizadas=doses_aplicadas_imediatas,
            doses_perdidas=0,  # Inicialmente não há doses perdidas
            motivo=motivo_descricao,
            observacoes=observacoes,
            usuario=request.user
        )
        
        # Reduzir a quantidade de frascos disponíveis
        estoque.quantidade_frascos -= 1
        estoque.save()
        
        messages.success(request, "Abertura de frasco registrada com sucesso!")
        
        # Se houve aplicações imediatas, redirecionar para registrar as aplicações
        if doses_aplicadas_imediatas > 0:
            return redirect('registrar_aplicacao_abertura', abertura_id=abertura.id)
        
        return redirect('dashboard')
    
    return redirect('registrar_abertura')

# APIs para os selects dinâmicos
@login_required
def api_lotes_por_tipo(request, tipo_id):
    try:
        # Verificar se existe o tipo de imunobiológico
        tipo_imuno = get_object_or_404(TipoImunobiologico, pk=tipo_id)
        
        # Buscar todos os lotes não vencidos deste tipo, independente da quantidade
        # para verificar se há lotes cadastrados no sistema
        todos_lotes = Lote.objects.filter(
            tipo_imunobiologico_id=tipo_id,
            data_validade__gt=timezone.now().date()
        ).order_by('data_validade')
        
        # Verificar quantos lotes estão disponíveis (para debug)
        total_lotes = todos_lotes.count()
        print(f"Total de lotes encontrados: {total_lotes}")
        
        # Agora buscar apenas os que têm estoque central
        lotes = todos_lotes.filter(quantidade_frascos_central__gt=0)
        
        # Para debug: imprimir contagem de lotes com estoque
        print(f"Lotes com estoque central disponível: {lotes.count()} de {total_lotes}")
        
        # Verificar detalhes dos lotes para debugging
        for lote in todos_lotes:
            print(f"Lote: {lote.numero_lote}, Data: {lote.data_validade}, Estoque central: {lote.quantidade_frascos_central}")
            
        # Atualizar os lotes sem quantidade_frascos_central
        lotes_sem_estoque = todos_lotes.filter(quantidade_frascos_central=0)
        for lote in lotes_sem_estoque:
            if lote.quantidade_frascos > 0:
                lote.quantidade_frascos_central = lote.quantidade_frascos
                lote.save()
                print(f"Atualizado lote {lote.numero_lote} com {lote.quantidade_frascos} frascos")
        
        # Recarregar os lotes após a atualização
        if lotes_sem_estoque.exists():
            lotes = Lote.objects.filter(
                tipo_imunobiologico_id=tipo_id,
                quantidade_frascos_central__gt=0,
                data_validade__gt=timezone.now().date()
            ).order_by('data_validade')
        
        # Preparar dados para JSON
        lotes_json = []
        for lote in lotes:
            lotes_json.append({
                'id': lote.id,
                'numero_lote': lote.numero_lote,
                'data_validade': lote.data_validade.strftime('%d/%m/%Y'),
                'quantidade_frascos': lote.quantidade_frascos_central,
                'tipo_imunobiologico': {
                    'id': lote.tipo_imunobiologico.id,
                    'nome': lote.tipo_imunobiologico.nome,
                    'fabricante': lote.tipo_imunobiologico.fabricante,
                    'doses_por_frasco': lote.tipo_imunobiologico.doses_por_frasco
                }
            })
        
        return JsonResponse(lotes_json, safe=False)
    except Exception as e:
        # Log mais detalhado do erro
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao obter lotes por tipo: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e), 'details': traceback.format_exc()}, status=500)

@login_required
def api_lotes_ubs_por_tipo(request, tipo_id):
    # Para gestor de UBS - lotes disponíveis na UBS
    unidade = request.user.perfilusuario.unidade_gestao
    
    estoques = EstoqueImunobiologico.objects.filter(
        unidade=unidade,
        lote__tipo_imunobiologico_id=tipo_id,
        quantidade_frascos__gt=0,
        lote__data_validade__gt=timezone.now().date()
    ).select_related('lote', 'lote__tipo_imunobiologico').order_by('lote__data_validade')
    
    # Preparar dados para JSON
    estoques_json = []
    for estoque in estoques:
        estoques_json.append({
            'id': estoque.id,
            'quantidade_frascos': estoque.quantidade_frascos,
            'lote': {
                'id': estoque.lote.id,
                'numero_lote': estoque.lote.numero_lote,
                'data_validade': estoque.lote.data_validade.strftime('%d/%m/%Y'),
                'tipo_imunobiologico': {
                    'id': estoque.lote.tipo_imunobiologico.id,
                    'nome': estoque.lote.tipo_imunobiologico.nome,
                    'fabricante': estoque.lote.tipo_imunobiologico.fabricante,
                    'doses_por_frasco': estoque.lote.tipo_imunobiologico.doses_por_frasco,
                    'tempo_validade_apos_aberto': estoque.lote.tipo_imunobiologico.tempo_validade_apos_aberto
                }
            }
        })
    
    return JsonResponse(estoques_json, safe=False)

@login_required
def api_estoque_ubs_por_lote(request, lote_id):
    try:
        # Obter o lote para confirmação
        lote = get_object_or_404(Lote, pk=lote_id)
        
        # Obter estoques deste lote em todas as UBSs
        estoques = EstoqueImunobiologico.objects.filter(
            lote_id=lote_id
        ).values('unidade_id', 'quantidade_frascos')
        
        # Debug
        print(f"Encontrados {len(estoques)} registros de estoque para o lote {lote.numero_lote}")
        
        return JsonResponse(list(estoques), safe=False)
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao obter estoque por lote: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def relatorios(request):
    # Verificar se o usuário tem permissão
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    return render(request, 'estoque/relatorios.html')

@login_required
def relatorio_estoque(request):
    # Verificar se o usuário tem permissão
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Filtrar por tipo de imunobiológico se fornecido
    vacina_id = request.GET.get('vacina')
    
    # Gerar dados para o relatório
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        estoques = EstoqueImunobiologico.objects.filter(unidade=unidade)
        if vacina_id:
            estoques = estoques.filter(lote__tipo_imunobiologico_id=vacina_id)
    else:
        estoques = EstoqueImunobiologico.objects.all()
        if vacina_id:
            estoques = estoques.filter(lote__tipo_imunobiologico_id=vacina_id)
    
    # Agrupar por tipo de imunobiológico
    dados_estoque = {}
    
    for estoque in estoques:
        tipo = estoque.lote.tipo_imunobiologico
        
        if tipo.id not in dados_estoque:
            dados_estoque[tipo.id] = {
                'nome': tipo.nome,
                'fabricante': tipo.fabricante,
                'doses_por_frasco': tipo.doses_por_frasco,
                'frascos': 0,
                'doses': 0,
                'lotes': set()
            }
        
        dados_estoque[tipo.id]['frascos'] += estoque.quantidade_frascos
        dados_estoque[tipo.id]['doses'] += estoque.quantidade_frascos * tipo.doses_por_frasco
        dados_estoque[tipo.id]['lotes'].add(estoque.lote.numero_lote)
    
    # Converter para lista para o template
    dados_relatorio = [
        {
            'nome': dados['nome'],
            'fabricante': dados['fabricante'],
            'doses_por_frasco': dados['doses_por_frasco'],
            'frascos': dados['frascos'],
            'doses': dados['doses'],
            'lotes': len(dados['lotes'])
        }
        for tipo_id, dados in dados_estoque.items()
    ]
    
    context = {
        'dados_relatorio': dados_relatorio,
        'data_geracao': timezone.now(),
        'total_frascos': sum(item['frascos'] for item in dados_relatorio),
        'total_doses': sum(item['doses'] for item in dados_relatorio),
        'filtro_vacina': TipoImunobiologico.objects.filter(id=vacina_id).first() if vacina_id else None,
    }
    
    return render(request, 'estoque/relatorio_estoque.html', context)

# Adicionando novo método para relatório por UBS específica
@login_required
def relatorio_estoque_unidade(request, unidade_id):
    # Verificar se o usuário é administrador
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter a unidade
    unidade = get_object_or_404(UnidadeSaude, pk=unidade_id)
    
    # Obter todos os estoques desta unidade
    estoques = EstoqueImunobiologico.objects.filter(unidade=unidade)
    
    # Agrupar por tipo de imunobiológico
    dados_estoque = {}
    
    for estoque in estoques:
        tipo = estoque.lote.tipo_imunobiologico
        
        if tipo.id not in dados_estoque:
            dados_estoque[tipo.id] = {
                'nome': tipo.nome,
                'fabricante': tipo.fabricante,
                'doses_por_frasco': tipo.doses_por_frasco,
                'frascos': 0,
                'doses': 0,
                'lotes': set(),
                'vencendo_em_30_dias': 0
            }
        
        dados_estoque[tipo.id]['frascos'] += estoque.quantidade_frascos
        dados_estoque[tipo.id]['doses'] += estoque.quantidade_frascos * tipo.doses_por_frasco
        dados_estoque[tipo.id]['lotes'].add(estoque.lote.numero_lote)
        
        # Verificar se está vencendo em 30 dias
        if (estoque.lote.data_validade - timezone.now().date()).days <= 30:
            dados_estoque[tipo.id]['vencendo_em_30_dias'] += estoque.quantidade_frascos
    
    # Converter para lista para o template
    dados_relatorio = [
        {
            'nome': dados['nome'],
            'fabricante': dados['fabricante'],
            'doses_por_frasco': dados['doses_por_frasco'],
            'frascos': dados['frascos'],
            'doses': dados['doses'],
            'lotes': len(dados['lotes']),
            'vencendo_em_30_dias': dados['vencendo_em_30_dias']
        }
        for tipo_id, dados in dados_estoque.items()
    ]
    
    # Coletar histórico de aberturas dos últimos 30 dias
    aberturas = RegistroAbertura.objects.filter(
        estoque__unidade=unidade,
        data_hora_abertura__gte=timezone.now() - timezone.timedelta(days=30)
    ).order_by('-data_hora_abertura')
    
    # Calcular estatísticas de aberturas
    total_aberturas = aberturas.count()
    total_doses_aplicadas = aberturas.aggregate(Sum('doses_utilizadas'))['doses_utilizadas__sum'] or 0
    total_doses_perdidas = aberturas.aggregate(Sum('doses_perdidas'))['doses_perdidas__sum'] or 0
    
    if total_aberturas > 0:
        eficiencia = round((total_doses_aplicadas / (total_doses_aplicadas + total_doses_perdidas)) * 100, 2) if (total_doses_aplicadas + total_doses_perdidas) > 0 else 0
    else:
        eficiencia = 0
    
    context = {
        'unidade': unidade,
        'dados_relatorio': dados_relatorio,
        'data_geracao': timezone.now(),
        'total_frascos': sum(item['frascos'] for item in dados_relatorio),
        'total_doses': sum(item['doses'] for item in dados_relatorio),
        'total_aberturas': total_aberturas,
        'total_doses_aplicadas': total_doses_aplicadas,
        'total_doses_perdidas': total_doses_perdidas,
        'eficiencia': eficiencia,
        'tipo_relatorio': 'unidade'
    }
    
    return render(request, 'estoque/relatorio_estoque_unidade.html', context)

@login_required
def relatorio_distribuicao(request):
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Implementação do relatório de distribuição
    messages.info(request, "Relatório de Distribuição em desenvolvimento. Estará disponível em breve.")
    return redirect('relatorios')

@login_required
def relatorio_aplicacoes(request):
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Implementação do relatório de aplicações
    messages.info(request, "Relatório de Aplicações em desenvolvimento. Estará disponível em breve.")
    return redirect('relatorios')

@login_required
def relatorio_vencimentos(request):
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Implementação do relatório de vencimentos
    messages.info(request, "Relatório de Vencimentos em desenvolvimento. Estará disponível em breve.")
    return redirect('relatorios')

@login_required
def relatorio_eficiencia(request):
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Implementação do relatório de eficiência
    messages.info(request, "Relatório de Eficiência em desenvolvimento. Estará disponível em breve.")
    return redirect('relatorios')

@login_required
def relatorio_personalizado(request):
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Implementação do relatório personalizado
    messages.info(request, "Relatório Personalizado em desenvolvimento. Estará disponível em breve.")
    return redirect('relatorios')

@login_required
def listar_tipos_imunobiologicos(request):
    # Verificar se o usuário tem permissão
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Obter todos os tipos de imunobiológicos
    tipos = TipoImunobiologico.objects.all().order_by('nome')
    
    # Aplicar filtros se fornecidos
    nome = request.GET.get('nome')
    if nome:
        tipos = tipos.filter(nome__icontains=nome)
    
    fabricante = request.GET.get('fabricante')
    if fabricante:
        tipos = tipos.filter(fabricante__icontains=fabricante)
    
    # Paginação
    paginator = Paginator(tipos, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    tipos_paginados = paginator.get_page(page_number)
    
    context = {
        'tipos': tipos_paginados
    }
    
    return render(request, 'estoque/tipos_imunobiologicos.html', context)

@login_required
def novo_tipo_imunobiologico(request):
    # Verificar se o usuário é administrador
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = TipoImunobiologicoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f"Tipo de imunobiológico '{tipo.nome}' cadastrado com sucesso!")
            return redirect('listar_tipos_imunobiologicos')
    else:
        form = TipoImunobiologicoForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'estoque/tipo_imunobiologico_form.html', context)

@login_required
def detalhe_tipo_imunobiologico(request, pk):
    # Verificar se o usuário tem permissão
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    tipo = get_object_or_404(TipoImunobiologico, pk=pk)
    
    # Obter lotes deste tipo de imunobiológico
    lotes = Lote.objects.filter(tipo_imunobiologico=tipo).order_by('-data_validade')
    
    context = {
        'tipo': tipo,
        'lotes': lotes
    }
    
    return render(request, 'estoque/detalhe_tipo_imunobiologico.html', context)

@login_required
def editar_tipo_imunobiologico(request, pk):
    # Verificar se o usuário é administrador
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    tipo = get_object_or_404(TipoImunobiologico, pk=pk)
    
    if request.method == 'POST':
        form = TipoImunobiologicoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tipo de imunobiológico '{tipo.nome}' atualizado com sucesso!")
            return redirect('detalhe_tipo_imunobiologico', pk=tipo.pk)
    else:
        form = TipoImunobiologicoForm(instance=tipo)
    
    context = {
        'form': form,
        'tipo': tipo
    }
    
    return render(request, 'estoque/tipo_imunobiologico_form.html', context)

@login_required
def api_lote_info(request, lote_id):
    """API para obter informações detalhadas de um lote específico"""
    try:
        lote = get_object_or_404(Lote, pk=lote_id)
        
        # Preparar dados para JSON
        dados_lote = {
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'data_fabricacao': lote.data_fabricacao.strftime('%d/%m/%Y'),
            'data_validade': lote.data_validade.strftime('%d/%m/%Y'),
            'quantidade_frascos': lote.quantidade_frascos,
            'quantidade_frascos_central': lote.quantidade_frascos_central,
            'tipo_imunobiologico': {
                'id': lote.tipo_imunobiologico.id,
                'nome': lote.tipo_imunobiologico.nome,
                'fabricante': lote.tipo_imunobiologico.fabricante,
                'doses_por_frasco': lote.tipo_imunobiologico.doses_por_frasco
            }
        }
        
        return JsonResponse(dados_lote)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)