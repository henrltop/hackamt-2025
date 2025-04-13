from django.shortcuts import render
from estoque.models import TipoImunobiologico, EstoqueImunobiologico, Lote
from unidades.models import UnidadeSaude, Municipio
from django.db.models import Sum, F, ExpressionWrapper, IntegerField, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone


def mapa_vacinas(request):
    # Obter unidades com prefetch para otimizar consultas
    unidades = UnidadeSaude.objects.filter(ativa=True).prefetch_related(
        'estoqueimunobiologico_set__lote__tipo_imunobiologico'
    )
    
    # Filtrar por vacina se fornecido na query string
    vacina_id = request.GET.get('vacina')
    if vacina_id:
        unidades = unidades.filter(
            estoqueimunobiologico__lote__tipo_imunobiologico_id=vacina_id,
            estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct()
    
    # Obter todos os tipos de imunobiológicos para o filtro
    tipos_imuno = TipoImunobiologico.objects.all()
    
    # Obter todos os municípios para o filtro
    municipios = Municipio.objects.all()
    
    # Verificar se Cáceres está nos municípios e obter seu ID
    caceres_id = None
    for municipio in municipios:
        if municipio.nome.lower() == 'cáceres' or municipio.nome.lower() == 'caceres':
            caceres_id = municipio.id
            break
    
    context = {
        'unidades': unidades,
        'tipos_imuno': tipos_imuno,
        'municipios': municipios,
        'caceres_id': caceres_id,
        'is_homepage': request.path == '/',
    }
    return render(request, 'core/mapa.html', context)


@login_required
def home(request):
    """
    View para o painel de gestão (dashboard) que mostra informações
    de gestão e estatísticas para usuários autenticados.
    """
    # Verificar se o usuário tem permissão para acessar
    if request.user.perfilusuario.tipo == 'CIDADAO':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    # Preparar dados para o painel de gestão
    
    # Estatísticas gerais
    total_ubs = UnidadeSaude.objects.filter(ativa=True).count()
    total_tipos_vacinas = TipoImunobiologico.objects.count()
    
    total_doses = EstoqueImunobiologico.objects.filter(
        quantidade_frascos__gt=0
    ).annotate(
        doses_disponiveis=F('quantidade_frascos') * F('lote__tipo_imunobiologico__doses_por_frasco')
    ).aggregate(total=Sum('doses_disponiveis'))['total'] or 0
    
    lotes_a_vencer = Lote.objects.filter(
        data_validade__gte=timezone.now().date(),
        data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
    ).count()
    
    # Para gestores, filtrar por UBS
    if request.user.perfilusuario.tipo == 'GESTOR':
        unidade = request.user.perfilusuario.unidade_gestao
        
        # Dados específicos da UBS
        ubs_tipos_vacinas = TipoImunobiologico.objects.filter(
            lote__estoqueimunobiologico__unidade=unidade,
            lote__estoqueimunobiologico__quantidade_frascos__gt=0
        ).distinct().count()
        
        ubs_doses = EstoqueImunobiologico.objects.filter(
            unidade=unidade,
            quantidade_frascos__gt=0
        ).annotate(
            doses_disponiveis=F('quantidade_frascos') * F('lote__tipo_imunobiologico__doses_por_frasco')
        ).aggregate(total=Sum('doses_disponiveis'))['total'] or 0
        
        ubs_ampolas_abertas = 0  # Implementar contagem real
        
        ubs_lotes_a_vencer = Lote.objects.filter(
            estoqueimunobiologico__unidade=unidade,
            data_validade__gte=timezone.now().date(),
            data_validade__lte=timezone.now().date() + timezone.timedelta(days=30),
        ).distinct().count()
        
        context = {
            'unidade': unidade,
            'ubs_tipos_vacinas': ubs_tipos_vacinas,
            'ubs_doses': ubs_doses,
            'ubs_ampolas_abertas': ubs_ampolas_abertas,
            'ubs_lotes_a_vencer': ubs_lotes_a_vencer,
        }
    else:
        # Para administradores, mostrar dados gerais
        context = {
            'total_ubs': total_ubs,
            'total_tipos_vacinas': total_tipos_vacinas,
            'total_doses': total_doses,
            'lotes_a_vencer': lotes_a_vencer,
        }
        
        # Adicionar lista de lotes disponíveis para distribuição
        lotes_disponiveis = Lote.objects.filter(
            quantidade_frascos_central__gt=0,
            data_validade__gt=timezone.now().date()
        ).order_by('data_validade')
        
        context['lotes_disponiveis'] = lotes_disponiveis
    
    # Obter tipos de imunobiológicos e UBSs para ações rápidas
    context['tipos_imuno'] = TipoImunobiologico.objects.all()[:6]
    context['unidades'] = UnidadeSaude.objects.filter(ativa=True)[:6]
    
    return render(request, 'core/dashboard.html', context)


def sobre(request):
    return render(request, 'core/sobre.html')


@login_required
def admin_cadastros(request):
    # Verificar se o usuário é administrador
    try:
        if request.user.perfilusuario.tipo != 'ADMIN':
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect('home')
    except AttributeError:
        messages.error(request, "Erro ao verificar permissões de usuário.")
        return redirect('home')
    
    return render(request, 'core/admin_cadastros.html')
