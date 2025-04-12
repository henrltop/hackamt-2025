# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from unidades.models import UnidadeSaude, Municipio
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    TIPO_CHOICES = [
        ('CIDADAO', 'Cidadão'),
        ('GESTOR', 'Gestor de Unidade'),
        ('ADMIN', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='CIDADAO')
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True)
    unidade_gestao = models.ForeignKey(UnidadeSaude, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'perfilusuario'):
        PerfilUsuario.objects.create(usuario=instance)
    instance.perfilusuario.save()