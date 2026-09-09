import pytest
from models.job import Job
from core.deduplicator import Deduplicator
from storage.state_store import StateStore

class TestSlidingWindowResilience:
    def test_sliding_window_deduplication_and_failure_recovery(self, tmp_path):
        """
        Simula o cenário do audit:
        - Execução 10:00: vaga A coletada e persistida.
        - Execução 11:00 (FALHA no cron ou rede): nenhuma execução ocorre.
        - Execução 12:00: vaga A ainda é coletada pela janela de 2h (r7200),
          e uma nova vaga B publicada às 10:30 é descoberta.
        Resultado esperado:
        - Vaga A é reconhecida como já vista (zero duplicação/spam).
        - Vaga B é identificada e qualificada para processamento.
        """
        state_file = tmp_path / "test_seen.json"
        store = StateStore(str(state_file))
        
        # 1. Execução 10:00 (Vaga A publicada às 09:30)
        job_a = Job(
            title="Desenvolvedor Node.js Junior",
            company="Tech Corp",
            workplace_type="remote",
            location="Brasil",
            description="Vaga de entrada com Node e TypeScript"
        )
        job_a.add_source("linkedin", "li_1001", "https://linkedin.com/jobs/view/1001")
        
        fp_a = job_a.fingerprint
        store.mark_seen(fp_a, ["li_1001"])
        store.save()
        
        # 2. Execução 12:00 (após falha na janela anterior)
        # O coletor traz novamente vaga A (janela de 2h) + nova vaga B
        job_b = Job(
            title="Desenvolvedor React Junior",
            company="Startup Inc",
            workplace_type="remote",
            location="Brasil",
            description="Vaga de entrada com React e Next.js"
        )
        job_b.add_source("linkedin", "li_1002", "https://linkedin.com/jobs/view/1002")
        
        # Recarrega o estado como ocorre no GitHub Actions
        store_new_run = StateStore(str(state_file))
        
        # Teste de Deduplicação
        dedup = Deduplicator()
        unique = dedup.process([job_a, job_b])
        assert len(unique) == 2
        
        # Teste de Filtro de Estado (Já Vistas)
        seen_status = {
            j.fingerprint: store_new_run.is_seen(j.fingerprint, list(j.sources.values())[0].source_job_id)
            for j in unique
        }
        
        assert seen_status[job_a.fingerprint] is True   # Já vista às 10:00 -> NÃO NOTIFICAR
        assert seen_status[job_b.fingerprint] is False  # Nova vaga descoberta -> NOTIFICAR
