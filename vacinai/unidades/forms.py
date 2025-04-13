# unidades/forms.py
from django import forms
from .models import UnidadeSaude, Municipio, Bairro

class UnidadeSaudeForm(forms.ModelForm):
    class Meta:
        model = UnidadeSaude
        fields = [
            'nome', 'codigo_cnes', 'municipio', 'bairro', 'endereco', 
            'telefone', 'email', 'horario_funcionamento', 
            'latitude', 'longitude', 'ativa'
        ]
        widgets = {
            'horario_funcionamento': forms.Textarea(attrs={'rows': 4}),
        }

class MunicipioForm(forms.ModelForm):
    class Meta:
        model = Municipio
        fields = ['nome', 'uf']

class BairroForm(forms.ModelForm):
    class Meta:
        model = Bairro
        fields = ['nome', 'municipio']