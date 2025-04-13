from django.core.management.base import BaseCommand
from estoque.models import Lote

class Command(BaseCommand):
    help = 'Atualiza o campo quantidade_frascos_central para todos os lotes que têm esse valor zerado'

    def handle(self, *args, **options):
        # Buscar lotes sem quantidade_frascos_central definido (zero)
        lotes_para_atualizar = Lote.objects.filter(quantidade_frascos_central=0)
        count = lotes_para_atualizar.count()
        
        self.stdout.write(self.style.SUCCESS(f'Encontrados {count} lotes para atualizar'))
        
        # Atualizar cada lote
        for lote in lotes_para_atualizar:
            lote.quantidade_frascos_central = lote.quantidade_frascos
            lote.save(update_fields=['quantidade_frascos_central'])
            self.stdout.write(f'Lote {lote.numero_lote} atualizado com {lote.quantidade_frascos_central} frascos')
        
        self.stdout.write(self.style.SUCCESS(f'Atualização concluída. {count} lotes foram atualizados.'))
