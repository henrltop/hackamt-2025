from django.shortcuts import render
from estoque.models import TipoImunobiologico, EstoqueImunobiologico
from unidades.models import UnidadeSaude, Municipio
from django.db.models import Sum, F, ExpressionWrapper, IntegerField
from django.contrib import messages # Adicione esta linha se ainda não estiver importado
from django.contrib.auth.decorators import login_required # Adicione esta linha
from django.shortcuts import render, redirect # Adicione redirect se ainda não estiver importado


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
        'caceres_id': caceres_id,  # Passar o ID de Cáceres para o template
        'is_homepage': request.path == '/',  # Identificar se é a página inicial
    }
    return render(request, 'core/mapa.html', context)

@login_required
def admin_cadastros(request):
    # Verificar se o usuário é administrador
    try:
        # Esta versão adiciona tratamento de erros para o caso do usuário
        # não ter um perfil associado ou o perfil não ter o atributo 'tipo'
        if request.user.perfilusuario.tipo != 'ADMIN':
            messages.error(request, "Você não tem permissão para acessar esta página.")
            return redirect('home')
    except AttributeError:
        # A versão original não tratava esta exceção, o que poderia causar
        # erros 500 se o usuário não tivesse um perfil associado
        messages.error(request, "Erro ao verificar permissões de usuário.")
        return redirect('home')
    
    return render(request, 'core/admin_cadastros.html')
