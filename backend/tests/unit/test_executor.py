"""
Testes unitarios para ETLExecutor
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.executor import ETLExecutor


class TestConvertDateFormat:
    """Testes para _convert_date_format"""

    @pytest.fixture
    def executor(self):
        """Fixture do executor"""
        return ETLExecutor()

    def test_iso_format_conversion(self, executor):
        """Converte formato ISO para DD/MM/YYYY"""
        result = executor._convert_date_format("2024-01-15")
        assert result == "15/01/2024"

    def test_iso_format_year_start(self, executor):
        """Converte inicio do ano"""
        result = executor._convert_date_format("2024-01-01")
        assert result == "01/01/2024"

    def test_iso_format_year_end(self, executor):
        """Converte fim do ano"""
        result = executor._convert_date_format("2024-12-31")
        assert result == "31/12/2024"

    def test_already_brazilian_format(self, executor):
        """Mantem formato brasileiro"""
        result = executor._convert_date_format("15/01/2024")
        assert result == "15/01/2024"

    def test_empty_string(self, executor):
        """Retorna string vazia para entrada vazia"""
        result = executor._convert_date_format("")
        assert result == ""

    def test_none_value(self, executor):
        """Retorna None para entrada None"""
        result = executor._convert_date_format(None)
        assert result is None

    def test_invalid_format_passthrough(self, executor):
        """Passa formato invalido sem alteracao"""
        result = executor._convert_date_format("invalid-date")
        assert result == "invalid-date"


class TestParseLogLine:
    """Testes para _parse_log_line"""

    @pytest.fixture
    def executor(self):
        """Fixture do executor"""
        return ETLExecutor()

    def test_standard_format(self, executor):
        """Parseia formato padrao [LEVEL] [SISTEMA] Mensagem"""
        result = executor._parse_log_line("[INFO] [AMPLIS] Iniciando download")
        assert result["level"] == "INFO"
        assert result["sistema"] == "AMPLIS"
        assert result["mensagem"] == "Iniciando download"
        assert "timestamp" in result

    def test_success_level(self, executor):
        """Parseia nivel SUCCESS"""
        result = executor._parse_log_line("[SUCCESS] [MAPS] Processamento concluido")
        assert result["level"] == "SUCCESS"
        assert result["sistema"] == "MAPS"

    def test_error_level(self, executor):
        """Parseia nivel ERROR"""
        result = executor._parse_log_line("[ERROR] [FIDC] Falha na conexao")
        assert result["level"] == "ERROR"
        assert result["sistema"] == "FIDC"
        assert result["mensagem"] == "Falha na conexao"

    def test_warn_level(self, executor):
        """Parseia nivel WARN"""
        result = executor._parse_log_line("[WARN] [QORE] Arquivo nao encontrado")
        assert result["level"] == "WARN"

    def test_plain_text_fallback(self, executor):
        """Texto sem formato padrao vira INFO/STDOUT"""
        result = executor._parse_log_line("Linha de texto comum")
        assert result["level"] == "INFO"
        assert result["sistema"] == "STDOUT"
        assert result["mensagem"] == "Linha de texto comum"

    def test_partial_format(self, executor):
        """Formato parcial vira fallback"""
        result = executor._parse_log_line("[INFO] Sem sistema definido")
        assert result["level"] == "INFO"
        assert result["sistema"] == "STDOUT"
        assert result["mensagem"] == "[INFO] Sem sistema definido"

    def test_empty_message(self, executor):
        """Linha vazia"""
        result = executor._parse_log_line("")
        assert result["level"] == "INFO"
        assert result["mensagem"] == ""

    def test_sistema_with_spaces(self, executor):
        """Sistema com espacos"""
        result = executor._parse_log_line("[INFO] [AMPLIS REAG] Mensagem")
        assert result["sistema"] == "AMPLIS REAG"


class TestBuildCommand:
    """Testes para build_command"""

    @pytest.fixture
    def executor(self):
        """Fixture do executor"""
        return ETLExecutor()

    def test_minimal_command(self, executor):
        """Comando minimo sem parametros"""
        cmd = executor.build_command({})
        assert sys.executable in cmd[0]
        assert executor.main_script in cmd[1]
        assert "--config" in cmd

    def test_with_sistemas(self, executor):
        """Comando com lista de sistemas"""
        cmd = executor.build_command({"sistemas": ["amplis_reag", "maps"]})
        assert "--sistemas" in cmd
        sistemas_idx = cmd.index("--sistemas")
        assert cmd[sistemas_idx + 1] == "amplis_reag"
        assert cmd[sistemas_idx + 2] == "maps"

    def test_with_dates_iso(self, executor):
        """Comando com datas em formato ISO (convertidas)"""
        cmd = executor.build_command({
            "data_inicial": "2024-01-01",
            "data_final": "2024-01-31"
        })
        assert "--data-inicial" in cmd
        assert "--data-final" in cmd
        # Verifica conversao
        di_idx = cmd.index("--data-inicial")
        df_idx = cmd.index("--data-final")
        assert cmd[di_idx + 1] == "01/01/2024"
        assert cmd[df_idx + 1] == "31/01/2024"

    def test_with_limpar_flag(self, executor):
        """Comando com flag limpar"""
        cmd = executor.build_command({"limpar": True})
        assert "--limpar" in cmd

    def test_with_dry_run_flag(self, executor):
        """Comando com flag dry_run"""
        cmd = executor.build_command({"dry_run": True})
        assert "--dry-run" in cmd

    def test_without_flags_when_false(self, executor):
        """Flags nao aparecem quando False"""
        cmd = executor.build_command({"limpar": False, "dry_run": False})
        assert "--limpar" not in cmd
        assert "--dry-run" not in cmd

    def test_amplis_no_csv_option(self, executor):
        """Opcao AMPLIS sem CSV"""
        cmd = executor.build_command({
            "opcoes": {"amplis_reag": {"csv": False}}
        })
        assert "--no-csv" in cmd

    def test_amplis_no_pdf_option(self, executor):
        """Opcao AMPLIS sem PDF"""
        cmd = executor.build_command({
            "opcoes": {"amplis_master": {"pdf": False}}
        })
        assert "--no-pdf" in cmd

    def test_maps_options(self, executor):
        """Opcoes MAPS"""
        cmd = executor.build_command({
            "opcoes": {
                "maps": {
                    "excel": False,
                    "pdf": False,
                    "ativo": False,
                    "passivo": False
                }
            }
        })
        assert "--maps-no-excel" in cmd
        assert "--maps-no-pdf" in cmd
        assert "--maps-no-ativo" in cmd
        assert "--maps-no-passivo" in cmd

    def test_qore_options(self, executor):
        """Opcoes QORE"""
        cmd = executor.build_command({
            "opcoes": {
                "qore": {
                    "excel": False,
                    "pdf": False,
                    "lote_pdf": True,
                    "lote_excel": True
                }
            }
        })
        assert "--qore-no-excel" in cmd
        assert "--qore-no-pdf" in cmd
        assert "--qore-lote-pdf" in cmd
        assert "--qore-lote-excel" in cmd

    def test_full_command(self, executor):
        """Comando completo com todos os parametros"""
        cmd = executor.build_command({
            "sistemas": ["amplis_reag", "maps", "qore"],
            "data_inicial": "2024-06-01",
            "data_final": "2024-06-30",
            "limpar": True,
            "dry_run": False,
            "opcoes": {
                "amplis_reag": {"csv": True, "pdf": False},
                "maps": {"excel": True, "pdf": True},
                "qore": {"lote_pdf": True}
            }
        })
        assert "--sistemas" in cmd
        assert "--data-inicial" in cmd
        assert "--limpar" in cmd
        assert "--no-pdf" in cmd
        assert "--qore-lote-pdf" in cmd


class TestExecutorProperties:
    """Testes para propriedades do executor"""

    def test_is_running_false_initially(self):
        """is_running e False inicialmente"""
        executor = ETLExecutor()
        assert executor.is_running is False

    def test_paths_are_absolute(self):
        """Caminhos sao absolutos"""
        executor = ETLExecutor()
        assert Path(executor.root_dir).is_absolute()
        assert Path(executor.python_dir).is_absolute()
        assert Path(executor.main_script).is_absolute()
        assert Path(executor.config_path).is_absolute()


class TestExecutorCancel:
    """Testes para cancel()"""

    def test_cancel_sets_flag(self):
        """Cancel define flag _cancelled"""
        executor = ETLExecutor()
        executor.cancel()
        assert executor._cancelled is True

    def test_cancel_terminates_process(self):
        """Cancel termina processo se existir"""
        executor = ETLExecutor()
        mock_process = MagicMock()
        mock_process.returncode = None  # Processo ainda rodando
        executor.process = mock_process

        executor.cancel()

        mock_process.terminate.assert_called_once()
        assert executor._cancelled is True

    def test_cancel_no_process(self):
        """Cancel sem processo nao da erro"""
        executor = ETLExecutor()
        executor.process = None
        # Nao deve lancar excecao
        executor.cancel()
        assert executor._cancelled is True

    def test_cancel_finished_process(self):
        """Cancel nao termina processo ja finalizado"""
        executor = ETLExecutor()
        mock_process = MagicMock()
        mock_process.returncode = 0  # Processo ja terminou
        executor.process = mock_process

        executor.cancel()

        # terminate nao deve ser chamado se processo ja terminou
        mock_process.terminate.assert_not_called()
        assert executor._cancelled is True


class TestExecutorSlotId:
    """Testes para slot_id"""

    def test_default_slot_id(self):
        """Slot ID padrao e 0"""
        executor = ETLExecutor()
        assert executor.slot_id == 0

    def test_custom_slot_id(self):
        """Slot ID customizado"""
        executor = ETLExecutor(slot_id=5)
        assert executor.slot_id == 5


class TestGetExecutor:
    """Testes para funcao get_executor"""

    def test_single_mode_returns_singleton(self):
        """Modo single retorna singleton"""
        from services.executor import get_executor
        import services.executor as executor_module

        with patch('config.settings') as mock_settings:
            mock_settings.MAX_CONCURRENT_JOBS = 1
            # Reset singleton
            executor_module._executor_instance = None

            exec1 = get_executor()
            exec2 = get_executor()

            assert exec1 is exec2

    def test_pool_mode_returns_new_instance(self):
        """Modo pool retorna nova instancia"""
        from services.executor import get_executor

        with patch('config.settings') as mock_settings:
            mock_settings.MAX_CONCURRENT_JOBS = 4

            exec1 = get_executor(slot_id=0)
            exec2 = get_executor(slot_id=1)

            assert exec1 is not exec2
            assert exec1.slot_id == 0
            assert exec2.slot_id == 1


@pytest.mark.asyncio
class TestExecutorAsync:
    """Testes assincronos para executor"""

    async def test_send_log_async_callback(self):
        """_send_log funciona com callback async"""
        executor = ETLExecutor()
        received_logs = []

        async def log_callback(entry):
            received_logs.append(entry)

        await executor._send_log(log_callback, "INFO", "TEST", "Test message")

        assert len(received_logs) == 1
        assert received_logs[0]["level"] == "INFO"
        assert received_logs[0]["sistema"] == "TEST"
        assert received_logs[0]["mensagem"] == "Test message"
        assert "timestamp" in received_logs[0]

    async def test_send_log_sync_callback(self):
        """_send_log funciona com callback sync"""
        executor = ETLExecutor()
        received_logs = []

        def log_callback(entry):
            received_logs.append(entry)

        await executor._send_log(log_callback, "ERROR", "SYSTEM", "Error message")

        assert len(received_logs) == 1
        assert received_logs[0]["level"] == "ERROR"

    async def test_send_log_callback_error_handled(self):
        """_send_log trata erro no callback"""
        executor = ETLExecutor()

        async def failing_callback(entry):
            raise Exception("Callback failed")

        # Nao deve lancar excecao
        await executor._send_log(failing_callback, "INFO", "TEST", "Message")

    async def test_execute_script_not_found(self):
        """Execute retorna False se script nao existe"""
        executor = ETLExecutor()
        executor.main_script = "/nonexistent/path/main.py"

        logs = []
        async def log_callback(entry):
            logs.append(entry)

        result = await executor.execute({"sistemas": ["maps"]}, log_callback)

        assert result is False
        # Deve ter log de erro
        error_logs = [l for l in logs if l["level"] == "ERROR"]
        assert len(error_logs) > 0

    async def test_execute_already_running_single_mode(self):
        """Execute lanca erro se ja ha processo rodando (single mode)"""
        executor = ETLExecutor()
        mock_process = MagicMock()
        mock_process.returncode = None
        executor.process = mock_process

        async def log_callback(entry):
            pass

        with patch('config.settings') as mock_settings:
            mock_settings.MAX_CONCURRENT_JOBS = 1

            with pytest.raises(Exception) as exc_info:
                await executor.execute({"sistemas": ["maps"]}, log_callback)

            assert "Ja existe um processo em execucao" in str(exc_info.value)

    async def test_execute_allowed_in_pool_mode(self):
        """Execute permitido em pool mode mesmo com processo anterior"""
        executor = ETLExecutor()
        # Simular processo anterior (nao deve bloquear em pool mode)
        mock_process = MagicMock()
        mock_process.returncode = None
        executor.process = mock_process
        # Script inexistente para falhar rapido
        executor.main_script = "/nonexistent/path/main.py"

        logs = []
        async def log_callback(entry):
            logs.append(entry)

        with patch('config.settings') as mock_settings:
            mock_settings.MAX_CONCURRENT_JOBS = 4

            # Nao deve lancar excecao, mas retorna False porque script nao existe
            result = await executor.execute({"sistemas": ["maps"]}, log_callback)
            assert result is False


class TestUtcNow:
    """Testes para funcao utc_now"""

    def test_utc_now_format(self):
        """utc_now retorna formato ISO"""
        from services.executor import utc_now

        result = utc_now()

        # Deve ser string
        assert isinstance(result, str)
        # Deve ter formato ISO (YYYY-MM-DDTHH:MM:SS.mmmmmm)
        assert "T" in result
        # Deve ser parseavel
        from datetime import datetime
        parsed = datetime.fromisoformat(result)
        assert parsed is not None
