# estoque/models.py
from django.db import models
from unidades.models import UnidadeSaude
from django.utils import timezone

class TipoImunobiologico(models.Model):
    PUBLICO_CHOICES = [
        ('TODOS', 'Todos'),
        ('CRIANCAS', 'Crianças'),
        ('ADOLESCENTES', 'Adolescentes'),
        ('ADULTOS', 'Adultos'),
        ('IDOSOS', 'Idosos'),
        ('GESTANTES', 'Gestantes'),
    ]
    
    nome = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100)
    doses_necessarias = models.PositiveIntegerField(default=1)
    intervalo_doses = models.PositiveIntegerField(default=0, help_text="Intervalo em dias")
    publico_alvo = models.CharField(max_length=20, choices=PUBLICO_CHOICES, default='TODOS')
    tempo_validade_apos_aberto = models.PositiveIntegerField(help_text="Tempo em horas após abertura do frasco")
    doses_por_frasco = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.nome} - {self.fabricante}"
    
    class Meta:
        ordering = ['nome']

class Lote(models.Model):
    tipo_imunobiologico = models.ForeignKey(TipoImunobiologico, on_delete=models.CASCADE)
    numero_lote = models.CharField(max_length=30)
    data_fabricacao = models.DateField()
    data_validade = models.DateField()
    quantidade_frascos = models.PositiveIntegerField()
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tipo_imunobiologico.nome} - Lote {self.numero_lote}"
    
    @property
    def esta_vencido(self):
        return timezone.now().date() > self.data_validade
    
    @property
    def dias_para_vencer(self):
        delta = self.data_validade - timezone.now().date()
        return delta.days
    
    class Meta:
        ordering = ['data_validade']

class EstoqueImunobiologico(models.Model):
    unidade = models.ForeignKey(UnidadeSaude, on_delete=models.CASCADE)
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE)
    quantidade_frascos = models.PositiveIntegerField()
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.unidade.nome} - {self.lote.tipo_imunobiologico.nome} - {self.quantidade_frascos} frascos"
    
    @property
    def total_doses_disponiveis(self):
        registros = self.registroabertura_set.filter(
            data_hora_abertura__gte=timezone.now() - timezone.timedelta(hours=self.lote.tipo_imunobiologico.tempo_validade_apos_aberto)
        )
        
        frascos_abertos = registros.count()
        doses_utilizadas = sum(r.doses_utilizadas for r in registros)
        doses_perdidas = sum(r.doses_perdidas for r in registros)
        
        doses_disponiveis_frascos_fechados = (self.quantidade_frascos - frascos_abertos) * self.lote.tipo_imunobiologico.doses_por_frasco
        doses_disponiveis_frascos_abertos = sum([
            max(0, r.lote.tipo_imunobiologico.doses_por_frasco - r.doses_utilizadas - r.doses_perdidas)
            for r in registros if r.esta_na_validade
        ])
        
        return doses_disponiveis_frascos_fechados + doses_disponiveis_frascos_abertos

class RegistroAbertura(models.Model):
    estoque = models.ForeignKey(EstoqueImunobiologico, on_delete=models.CASCADE)
    data_hora_abertura = models.DateTimeField(default=timezone.now)
    doses_utilizadas = models.PositiveIntegerField(default=0)
    doses_perdidas = models.PositiveIntegerField(default=0)
    
    @property
    def horario_validade(self):
        validade_horas = self.estoque.lote.tipo_imunobiologico.tempo_validade_apos_aberto
        return self.data_hora_abertura + timezone.timedelta(hours=validade_horas)
    
    @property
    def esta_na_validade(self):
        return timezone.now() < self.horario_validade
    
    @property
    def doses_restantes(self):
        total_doses = self.estoque.lote.tipo_imunobiologico.doses_por_frasco
        return max(0, total_doses - self.doses_utilizadas - self.doses_perdidas)
    
    def __str__(self):
        return f"{self.estoque.lote.tipo_imunobiologico.nome} - {self.data_hora_abertura.strftime('%d/%m/%Y %H:%M')}"