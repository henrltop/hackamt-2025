from django import forms
from .models import Lote, EstoqueImunobiologico, RegistroAbertura

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['tipo_imunobiologico', 'numero_lote', 'data_fabricacao', 'data_validade', 'quantidade_frascos']
        widgets = {
            'data_fabricacao': forms.DateInput(attrs={'type': 'date'}),
            'data_validade': forms.DateInput(attrs={'type': 'date'})
        }

class EstoqueForm(forms.ModelForm):
    class Meta:
        model = EstoqueImunobiologico
        fields = ['lote', 'quantidade_frascos']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar lotes que ainda não venceram
        from django.utils import timezone
        self.fields['lote'].queryset = Lote.objects.filter(
            data_validade__gte=timezone.now().date()
        ).order_by('tipo_imunobiologico__nome', 'data_validade')

class RegistroAberturaForm(forms.ModelForm):
    class Meta:
        model = RegistroAbertura
        fields = ['estoque', 'data_hora_abertura', 'doses_utilizadas', 'doses_perdidas']
        widgets = {
            'data_hora_abertura': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
    
    def __init__(self, *args, **kwargs):
        unidade = kwargs.pop('unidade', None)
        super().__init__(*args, **kwargs)
        
        if unidade:
            # Filtrar estoque por unidade e que tenham frascos disponíveis
            self.fields['estoque'].queryset = EstoqueImunobiologico.objects.filter(
                unidade=unidade,
                quantidade_frascos__gt=0
            ).select_related('lote__tipo_imunobiologico')
    
    def clean(self):
        cleaned_data = super().clean()
        estoque = cleaned_data.get('estoque')
        doses_utilizadas = cleaned_data.get('doses_utilizadas')
        doses_perdidas = cleaned_data.get('doses_perdidas')
        
        if estoque and doses_utilizadas is not None and doses_perdidas is not None:
            doses_por_frasco = estoque.lote.tipo_imunobiologico.doses_por_frasco
            total_doses = doses_utilizadas + doses_perdidas
            
            if total_doses > doses_por_frasco:
                raise forms.ValidationError(
                    f"O total de doses utilizadas e perdidas ({total_doses}) não pode ser maior que o número de doses por frasco ({doses_por_frasco})."
                )
        
        return cleaned_data