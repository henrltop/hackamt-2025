from django import forms
from .models import PreferenciaNotificacao

class PreferenciaNotificacaoForm(forms.ModelForm):
    class Meta:
        model = PreferenciaNotificacao
        fields = ['tipo_imunobiologico', 'municipio', 'notificar_email', 'notificar_app']