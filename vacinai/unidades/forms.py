from django import forms
from .models import UnidadeSaude

class UnidadeSaudeForm(forms.ModelForm):
    class Meta:
        model = UnidadeSaude
        fields = [
            'nome', 'codigo_cnes', 'municipio', 'endereco', 'bairro', 
            'telefone', 'email', 'horario_funcionamento', 
            'latitude', 'longitude', 'ativa'
        ]
        widgets = {
            'horario_funcionamento': forms.Textarea(attrs={'rows': 4}),
        }