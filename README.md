# 📈 Vacinaí - Sistema de Gestão e Acesso Inteligente à Vacinação

## 🔧 HackaMT - Desafio 2 (Desafio Atacado)

### Tema
Combate ao desperdício de imunobiológicos e ampliação do acesso às vacinas.

### Problemas Identificados
- Falta de controle em tempo real do estoque de vacinas nas UBSs
- Descarte desnecessário de vacinas multidoses com validade curta
- Ausência de integração entre UBSs e canais de informação
- População sem acesso a dados atualizados sobre disponibilidade vacinal

## 🌟 Objetivo
Desenvolver um sistema digital que integre informações de estoque vacinal com os cidadãos, otimize a gestão dos imunobiológicos e evite desperdícios, oferecendo integração ao ConecteSUS e sistema de notificações inteligentes.

## 🔗 Solução Proposta: Vacinaí

### Aplicativo Web/Mobile para Cidadãos
- **Consulta Inteligente**: Busca por tipo de vacina e UBS com geolocalização e filtros
- **Sistema de Notificações**: Alertas via push/email/SMS quando vacinas estiverem disponíveis
- **Mapa Interativo**: Visualização das UBSs próximas e disponibilidade em tempo real

### Painel Administrativo para Gestores
- **Dashboard de Controle**: Monitoramento de estoque em tempo real
- **Sistema de Alertas**: Notificações automáticas para estoque crítico e vacinas próximas do vencimento
- **Gestão de Lotes**: Cadastro e rastreamento de lotes de vacinas
- **Relatórios Analíticos**: Geração de insights por localidade, faixa etária e tipo de vacina

### Integrações Tecnológicas
- Integração com ConecteSUS
- API RESTful para comunicação com sistemas das UBSs
- Preparação para integrações futuras com sistemas estaduais e municipais

## 🧠 Diferenciais Técnicos
- **Notificações Inteligentes**: Sistema baseado no perfil e interesse do usuário
- **Georreferenciamento em Tempo Real**: Localização precisa de disponibilidade vacinal
- **IA Preditiva** (roadmap futuro): Sistema de alertas baseado em análise de dados
- **Business Intelligence**: Painel público com visualização de dados vacinais

## 👨‍💻 Equipe Multidisciplinar
- **Desenvolvimento (3)**: 
  - Henrique: Backend
  - Brenno: Frontend
  - Khesner: Integrações
- **Design e Marketing (1)**:
  - Borges: UX/UI, identidade visual e estratégia de divulgação
- **Negócios (1)**:
  - Dudu: Planejamento estratégico, pitch e gestão de entregas

## 📅 Backlog Estruturado

Cada item do backlog possui:
- Título da tarefa
- Tipo (Feature, Design, Estratégico)
- Prioridade (Alta, Média, Baixa)
- Sprint planejado (1 a 4)
- Status atual
- Critérios de aceitação

### Exemplos de Itens Prioritários:
1. **Criar sistema de busca por vacina por UBS**
   - Tipo: Feature
   - Prioridade: Alta
   - Sprint: 1

2. **Implementar notificações para cidadãos quando vacinas estiverem disponíveis**
   - Tipo: Feature
   - Prioridade: Alta
   - Sprint: 2

3. **Desenvolver painel administrativo para visualização de estoque**
   - Tipo: Feature
   - Prioridade: Alta
   - Sprint: 2

## 📊 Alinhamento com Critérios do HackaMT

| Critério | Como o Vacinaí Atende |
|----------|------------------------|
| Adequação ao Desafio | Solução foca diretamente no problema do controle e acesso às vacinas |
| Viabilidade da Solução | Tecnologia acessível, APIs existentes, arquitetura modular e escalável |
| Grau de Inovação | Notificações inteligentes, mapa interativo, BI vacinal com potencial preditivo |
| Potencial de Impacto Social | Redução significativa de perdas, aumento da adesão vacinal e economia de recursos públicos |
| Desenvolvimento da Equipe | Equipe multidisciplinar com competências complementares e papéis bem definidos |

## 📱 Tecnologias Utilizadas
- **Frontend**: React, React Native
- **Backend**: Python, Django
- **Banco de Dados**: PostgreSQL
- **Infraestrutura**: Docker, AWS
- **Análise de Dados**: Pandas, Power BI

## 🚀 Como Executar o Projeto

### Requisitos
- Python 3.8+
- Node.js 14+
- PostgreSQL 12+

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/sua-organizacao/vacinai.git
cd vacinai
```

2. **Configure o ambiente virtual (recomendado)**
```bash
python -m venv venv
```

**Ativação no Windows:**
```bash
venv\Scripts\activate
```

**Ativação no macOS/Linux:**
```bash
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o settings.py**
```bash
cp vacinai/settings.example.py vacinai/settings.py
```
Edite o arquivo settings.py com suas configurações locais.

**Por que configurar o settings.py?**
- Contém configurações essenciais para conexão com banco de dados
- Armazena chaves de API para integrações com ConecteSUS
- Define variáveis de ambiente específicas para desenvolvimento/produção
- Configura parâmetros de segurança da aplicação

5. **Execute as migrações**
```bash
python manage.py migrate
```

6. **Inicie o servidor**
```bash
python manage.py runserver
```

## 📌 Conclusão
O Vacinaí é uma solução tecnológica realista, escalável e de impacto imediato, promovendo eficiência na imunização, economia de recursos públicos e maior adesão da população através da tecnologia integrada. Nossa abordagem combina inovação tecnológica com foco na experiência do usuário para resolver um problema crítico de saúde pública.

## 📞 Contato
Para mais informações sobre o projeto, entre em contato com:
- Email: equipe@vacinai.com.br
- GitHub: github.com/sua-organizacao/vacinai