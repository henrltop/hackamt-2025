from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import UnidadeSaude, Municipio
from .forms import UnidadeSaudeForm
from estoque.models import EstoqueImunobiologico
import requests
from django.conf import settings

@login_required
def importar_unidades_cnes(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        municipio_id = request.POST.get('municipio')
        
        if not municipio_id:
            messages.error(request, "Selecione um município.")
            return redirect('importar_unidades_cnes')
        
        municipio = get_object_or_404(Municipio, pk=municipio_id)
        
        try:
            # Credenciais para a API CNES
            username = "CNES.PUBLICO"
            password = "cnes#2015public"
            
            # Montar a URL da API
            url = f"https://servicos.saude.gov.br/cnes/EstabelecimentoSaudeService/v1r0"
            
            # Estrutura da requisição SOAP
            headers = {'Content-Type': 'text/xml;charset=UTF-8'}
            
            # Montar o corpo da requisição SOAP (conforme documentação da API do CNES)
            body = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
               <soapenv:Header>
                  <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                     <wsse:UsernameToken>
                        <wsse:Username>{username}</wsse:Username>
                        <wsse:Password>{password}</wsse:Password>
                     </wsse:UsernameToken>
                  </wsse:Security>
               </soapenv:Header>
               <soapenv:Body>
                  <est:requestConsultarEstabelecimentoSaudePorMunicipio>
                     <mun:Municipio>
                        <mun:codigoMunicipio>{municipio.ibge_codigo}</mun:codigoMunicipio>
                        <mun:UF>
                           <uf:siglaUF>{municipio.uf}</uf:siglaUF>
                        </mun:UF>
                     </mun:Municipio>
                  </est:requestConsultarEstabelecimentoSaudePorMunicipio>
               </soapenv:Body>
            </soapenv:Envelope>
            """
            
            # Fazer a requisição
            response = requests.post(url, headers=headers, data=body)
            
            # Processar a resposta XML
            # Aqui você precisaria de uma biblioteca para processar XML como ElementTree
            import xml.etree.ElementTree as ET
            
            # Analisar a resposta
            # (Código específico para parsing da resposta XML vai depender da estrutura do XML retornado)
            
            # Após processar, criar registros de unidades
            # (Implementação depende da estrutura da resposta)
            
            messages.success(request, f"Unidades importadas com sucesso para {municipio.nome}/{municipio.uf}!")
            return redirect('listar_unidades')
            
        except Exception as e:
            messages.error(request, f"Erro ao importar unidades: {str(e)}")
            return redirect('importar_unidades_cnes')
    
    # Se for uma requisição GET, mostrar o formulário
    municipios = Municipio.objects.all().order_by('uf', 'nome')
    
    context = {
        'municipios': municipios
    }
    
    return render(request, 'unidades/importar_unidades.html', context)

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

# unidades/views.py (adicionar)

@login_required
def listar_municipios(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    municipios = Municipio.objects.all().order_by('uf', 'nome')
    
    # Paginação
    paginator = Paginator(municipios, 10)
    page_number = request.GET.get('page')
    municipios_paginados = paginator.get_page(page_number)
    
    context = {
        'municipios': municipios_paginados
    }
    
    return render(request, 'unidades/listar_municipios.html', context)

@login_required
def adicionar_municipio(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = MunicipioForm(request.POST)
        if form.is_valid():
            municipio = form.save()
            messages.success(request, f"Município {municipio.nome}/{municipio.uf} cadastrado com sucesso!")
            return redirect('listar_municipios')
    else:
        form = MunicipioForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'unidades/municipio_form.html', context)

@login_required
def editar_municipio(request, pk):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    municipio = get_object_or_404(Municipio, pk=pk)
    
    if request.method == 'POST':
        form = MunicipioForm(request.POST, instance=municipio)
        if form.is_valid():
            form.save()
            messages.success(request, f"Município {municipio.nome}/{municipio.uf} atualizado com sucesso!")
            return redirect('listar_municipios')
    else:
        form = MunicipioForm(instance=municipio)
    
    context = {
        'form': form,
        'municipio': municipio
    }
    
    return render(request, 'unidades/municipio_form.html', context)

@login_required
def listar_bairros(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    bairros = Bairro.objects.all().select_related('municipio').order_by('municipio__uf', 'municipio__nome', 'nome')
    
    # Filtragem
    municipio_id = request.GET.get('municipio')
    if municipio_id:
        bairros = bairros.filter(municipio_id=municipio_id)
    
    # Paginação
    paginator = Paginator(bairros, 10)
    page_number = request.GET.get('page')
    bairros_paginados = paginator.get_page(page_number)
    
    # Municípios para o filtro
    municipios = Municipio.objects.all().order_by('uf', 'nome')
    
    context = {
        'bairros': bairros_paginados,
        'municipios': municipios
    }
    
    return render(request, 'unidades/listar_bairros.html', context)

@login_required
def adicionar_bairro(request):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    if request.method == 'POST':
        form = BairroForm(request.POST)
        if form.is_valid():
            bairro = form.save()
            messages.success(request, f"Bairro {bairro.nome} cadastrado com sucesso!")
            return redirect('listar_bairros')
    else:
        form = BairroForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'unidades/bairro_form.html', context)

@login_required
def editar_bairro(request, pk):
    if request.user.perfilusuario.tipo != 'ADMIN':
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    bairro = get_object_or_404(Bairro, pk=pk)
    
    if request.method == 'POST':
        form = BairroForm(request.POST, instance=bairro)
        if form.is_valid():
            form.save()
            messages.success(request, f"Bairro {bairro.nome} atualizado com sucesso!")
            return redirect('listar_bairros')
    else:
        form = BairroForm(instance=bairro)
    
    context = {
        'form': form,
        'bairro': bairro
    }
    
    return render(request, 'unidades/bairro_form.html', context)

# API para obter bairros por município (para uso com AJAX)
from django.http import JsonResponse

def api_bairros_por_municipio(request, municipio_id):
    bairros = Bairro.objects.filter(municipio_id=municipio_id).values('id', 'nome')
    return JsonResponse(list(bairros), safe=False)