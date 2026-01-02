"""
Testes de integracao para database (SQLite)
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import database


class TestDatabaseInit:
    """Testes para inicializacao do banco"""

    def test_init_creates_table(self, test_db):
        """init_db cria tabela jobs"""
        import sqlite3
        conn = sqlite3.connect(test_db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None
        assert result[0] == "jobs"

    def test_init_creates_directory(self, temp_dir):
        """init_db cria diretorio se necessario"""
        db_path = Path(temp_dir) / "subdir" / "test.db"
        original = database.DB_PATH
        database.DB_PATH = db_path

        database.init_db()

        assert db_path.parent.exists()
        database.DB_PATH = original


class TestAddJob:
    """Testes para add_job"""

    def test_add_job_returns_id(self, test_db):
        """add_job retorna ID do job criado"""
        job_id = test_db.add_job("etl_pipeline", {"sistemas": ["maps"]})
        assert isinstance(job_id, int)
        assert job_id > 0

    def test_add_job_increments_id(self, test_db):
        """IDs sao incrementais"""
        id1 = test_db.add_job("etl_pipeline", {})
        id2 = test_db.add_job("etl_single", {})
        id3 = test_db.add_job("etl_pipeline", {})
        assert id2 == id1 + 1
        assert id3 == id2 + 1

    def test_add_job_stores_params(self, test_db):
        """Parametros sao armazenados como JSON"""
        params = {
            "sistemas": ["amplis_reag", "maps"],
            "data_inicial": "2024-01-01",
            "opcoes": {"maps": {"excel": True}}
        }
        job_id = test_db.add_job("etl_pipeline", params)
        job = test_db.get_job(job_id)

        import json
        stored_params = json.loads(job["params"])
        assert stored_params["sistemas"] == ["amplis_reag", "maps"]
        assert stored_params["opcoes"]["maps"]["excel"] is True

    def test_add_job_default_status_pending(self, test_db):
        """Status padrao e 'pending'"""
        job_id = test_db.add_job("etl_pipeline", {})
        job = test_db.get_job(job_id)
        assert job["status"] == "pending"

    def test_add_job_sets_created_at(self, test_db):
        """created_at e definido automaticamente"""
        job_id = test_db.add_job("etl_pipeline", {})
        job = test_db.get_job(job_id)
        assert job["created_at"] is not None


class TestGetJob:
    """Testes para get_job"""

    def test_get_existing_job(self, test_db):
        """Busca job existente"""
        job_id = test_db.add_job("etl_single", {"sistemas": ["fidc"]})
        job = test_db.get_job(job_id)

        assert job is not None
        assert job["id"] == job_id
        assert job["type"] == "etl_single"

    def test_get_nonexistent_job(self, test_db):
        """Retorna None para job inexistente"""
        job = test_db.get_job(99999)
        assert job is None

    def test_get_job_returns_dict(self, test_db):
        """Retorna dict com todas as colunas"""
        job_id = test_db.add_job("etl_pipeline", {})
        job = test_db.get_job(job_id)

        assert isinstance(job, dict)
        assert "id" in job
        assert "type" in job
        assert "params" in job
        assert "status" in job
        assert "logs" in job
        assert "error_message" in job
        assert "created_at" in job


class TestUpdateJobStatus:
    """Testes para update_job_status"""

    def test_update_to_running(self, test_db):
        """Atualiza status para running"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(job_id, "running")

        job = test_db.get_job(job_id)
        assert job["status"] == "running"
        assert job["started_at"] is not None

    def test_update_to_completed(self, test_db):
        """Atualiza status para completed"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(job_id, "completed")

        job = test_db.get_job(job_id)
        assert job["status"] == "completed"
        assert job["finished_at"] is not None

    def test_update_to_error_with_message(self, test_db):
        """Atualiza status para error com mensagem"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(job_id, "error", error="Conexao falhou")

        job = test_db.get_job(job_id)
        assert job["status"] == "error"
        assert job["error_message"] == "Conexao falhou"
        assert job["finished_at"] is not None

    def test_update_to_cancelled(self, test_db):
        """Atualiza status para cancelled"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(job_id, "cancelled")

        job = test_db.get_job(job_id)
        assert job["status"] == "cancelled"


class TestAppendLog:
    """Testes para append_log"""

    def test_append_single_log(self, test_db):
        """Adiciona uma linha de log"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.append_log(job_id, "[INFO] Iniciando...")

        job = test_db.get_job(job_id)
        assert "[INFO] Iniciando..." in job["logs"]

    def test_append_multiple_logs(self, test_db):
        """Adiciona multiplas linhas de log"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.append_log(job_id, "[INFO] Linha 1")
        test_db.append_log(job_id, "[INFO] Linha 2")
        test_db.append_log(job_id, "[SUCCESS] Linha 3")

        job = test_db.get_job(job_id)
        assert "Linha 1" in job["logs"]
        assert "Linha 2" in job["logs"]
        assert "Linha 3" in job["logs"]

    def test_logs_have_newlines(self, test_db):
        """Logs sao separados por newlines"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.append_log(job_id, "Log A")
        test_db.append_log(job_id, "Log B")

        job = test_db.get_job(job_id)
        assert "\n" in job["logs"]


class TestGetPendingJob:
    """Testes para get_pending_job"""

    def test_get_pending_returns_oldest(self, test_db):
        """Retorna job pendente mais antigo"""
        id1 = test_db.add_job("etl_pipeline", {"order": 1})
        id2 = test_db.add_job("etl_pipeline", {"order": 2})
        id3 = test_db.add_job("etl_pipeline", {"order": 3})

        pending = test_db.get_pending_job()
        assert pending["id"] == id1

    def test_get_pending_ignores_running(self, test_db):
        """Ignora jobs em execucao"""
        id1 = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(id1, "running")
        id2 = test_db.add_job("etl_pipeline", {})

        pending = test_db.get_pending_job()
        assert pending["id"] == id2

    def test_get_pending_returns_none_when_empty(self, test_db):
        """Retorna None quando nao ha pendentes"""
        pending = test_db.get_pending_job()
        assert pending is None


class TestGetRunningJob:
    """Testes para get_running_job"""

    def test_get_running_job(self, test_db):
        """Retorna job em execucao"""
        job_id = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(job_id, "running")

        running = test_db.get_running_job()
        assert running is not None
        assert running["id"] == job_id

    def test_get_running_returns_none_when_no_running(self, test_db):
        """Retorna None quando nao ha job rodando"""
        test_db.add_job("etl_pipeline", {})  # pending

        running = test_db.get_running_job()
        assert running is None


class TestListJobs:
    """Testes para list_jobs"""

    def test_list_all_jobs(self, test_db):
        """Lista todos os jobs"""
        test_db.add_job("etl_pipeline", {})
        test_db.add_job("etl_single", {})
        test_db.add_job("etl_pipeline", {})

        jobs = test_db.list_jobs()
        assert len(jobs) == 3

    def test_list_with_status_filter(self, test_db):
        """Lista jobs por status"""
        id1 = test_db.add_job("etl_pipeline", {})
        id2 = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(id1, "completed")

        pending = test_db.list_jobs(status="pending")
        completed = test_db.list_jobs(status="completed")

        assert len(pending) == 1
        assert len(completed) == 1
        assert pending[0]["id"] == id2
        assert completed[0]["id"] == id1

    def test_list_with_limit(self, test_db):
        """Respeita limite"""
        for i in range(10):
            test_db.add_job("etl_pipeline", {"i": i})

        jobs = test_db.list_jobs(limit=5)
        assert len(jobs) == 5

    def test_list_with_offset(self, test_db):
        """Respeita offset"""
        for i in range(10):
            test_db.add_job("etl_pipeline", {"i": i})

        jobs = test_db.list_jobs(limit=5, offset=5)
        assert len(jobs) == 5

    def test_list_ordered_by_created_desc(self, test_db):
        """Ordenado por created_at decrescente"""
        test_db.add_job("etl_pipeline", {"order": 1})
        test_db.add_job("etl_pipeline", {"order": 2})
        test_db.add_job("etl_pipeline", {"order": 3})

        jobs = test_db.list_jobs()
        # Mais recente primeiro
        import json
        assert json.loads(jobs[0]["params"])["order"] == 3


class TestGetNextPendingJob:
    """Testes para get_next_pending_job"""

    def test_returns_pending_when_none_running(self, test_db):
        """Retorna pendente quando nao ha running"""
        job_id = test_db.add_job("etl_pipeline", {})

        next_job = test_db.get_next_pending_job()
        assert next_job is not None
        assert next_job["id"] == job_id

    def test_returns_none_when_job_running(self, test_db):
        """Retorna None quando ha job rodando"""
        id1 = test_db.add_job("etl_pipeline", {})
        test_db.update_job_status(id1, "running")
        test_db.add_job("etl_pipeline", {})  # pending

        next_job = test_db.get_next_pending_job()
        assert next_job is None

    def test_returns_none_when_no_pending(self, test_db):
        """Retorna None quando nao ha pendentes"""
        next_job = test_db.get_next_pending_job()
        assert next_job is None
