from django.shortcuts import render
from estoque.models import TipoImunobiologico, EstoqueImunobiologico
from unidades.models import UnidadeSaude, Municipio
from django.db.models import Sum, F, ExpressionWrapper, IntegerField

def home(request):
    tipos_imuno = TipoImunobiologico.objects.all()[:6]  # Limitar para 6 tipos
    unidades = UnidadeSaude.objects.filter(ativa=True)[:6]  # Limitar para 6 unidades
    
    context = {
        'tipos_imuno': tipos_imuno,
        'unidades': unidades,
    }
    return render(request, 'core/home.html', context)

def sobre(request):
    return render(request, 'core/sobre.html')

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
    
    context = {
        'unidades': unidades,
        'tipos_imuno': tipos_imuno,
        'municipios': municipios,
    }
    return render(request, 'core/mapa.html', context)