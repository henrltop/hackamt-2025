# Criar o arquivo core/management/commands/setup_initial_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from unidades.models import Municipio, UnidadeSaude

class Command(BaseCommand):
    help = 'Configura usuários iniciais do sistema'
    
    def handle(self, *args, **options):
        # Verificar se existe superusuário
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Criando superusuário admin...')
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            # Definir como ADMIN
            user.perfilusuario.tipo = 'ADMIN'
            user.perfilusuario.save()
        else:
            user = User.objects.filter(is_superuser=True).first()
            user.perfilusuario.tipo = 'ADMIN'
            user.perfilusuario.save()
            self.stdout.write('Superusuário já existe, configurado como ADMIN')
        
        # Criar município e UBS de exemplo se não existirem
        if not Municipio.objects.filter(nome='Cáceres').exists():
            municipio = Municipio.objects.create(nome='Cáceres', uf='MT')
            self.stdout.write('Município Cáceres/MT criado')
            
            # Criar UBS de exemplo
            ubs = UnidadeSaude.objects.create(
                nome='UBS Central',
                municipio=municipio,
                endereco='Av. Principal, 123',
                ativa=True
            )
            self.stdout.write('UBS Central criada')
            
            # Criar usuário gestor para a UBS
            if not User.objects.filter(username='gestor').exists():
                gestor = User.objects.create_user(
                    username='gestor',
                    email='gestor@example.com',
                    password='gestorpassword',
                    first_name='Gestor',
                    last_name='da UBS'
                )
                gestor.perfilusuario.tipo = 'GESTOR'
                gestor.perfilusuario.unidade_gestao = ubs
                gestor.perfilusuario.save()
                self.stdout.write('Usuário gestor criado para UBS Central')
        
        self.stdout.write(self.style.SUCCESS('Configuração inicial concluída com sucesso!'))