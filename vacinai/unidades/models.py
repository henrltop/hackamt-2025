# unidades/models.py
from django.db import models

class Municipio(models.Model):
    nome = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    
    def __str__(self):
        return f"{self.nome}/{self.uf}"
    
    class Meta:
        ordering = ['uf', 'nome']

class Bairro(models.Model):
    nome = models.CharField(max_length=100)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, related_name='bairros')
    
    def __str__(self):
        return f"{self.nome} - {self.municipio.nome}/{self.municipio.uf}"
    
    class Meta:
        ordering = ['municipio', 'nome']
        unique_together = ['nome', 'municipio']

class UnidadeSaude(models.Model):
    nome = models.CharField(max_length=200)
    codigo_cnes = models.CharField(max_length=10, unique=True, blank=True, null=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    bairro = models.ForeignKey(Bairro, on_delete=models.SET_NULL, null=True, blank=True, related_name='unidades')
    endereco = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    horario_funcionamento = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    ativa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ['municipio', 'nome']