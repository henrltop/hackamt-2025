# notificacoes/models.py
from django.db import models
from django.contrib.auth.models import User
from estoque.models import TipoImunobiologico
from unidades.models import Municipio

class PreferenciaNotificacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_imunobiologico = models.ForeignKey(TipoImunobiologico, on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    notificar_email = models.BooleanField(default=True)
    notificar_app = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('usuario', 'tipo_imunobiologico', 'municipio')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_imunobiologico.nome} - {self.municipio.nome}"

class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('DISPONIBILIDADE', 'Vacina Disponível'),
        ('VENCIMENTO', 'Alerta de Vencimento'),
        ('ESTOQUE_BAIXO', 'Estoque Baixo'),
        ('SISTEMA', 'Mensagem do Sistema'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
    
    class Meta:
        ordering = ['-data_envio']