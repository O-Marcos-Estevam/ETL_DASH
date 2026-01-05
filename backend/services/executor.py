"""
ETL Executor - Executa scripts Python ETL via subprocess
"""
import asyncio
import os
import sys
import re
import logging
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
import traceback

logger = logging.getLogger(__name__)

# Whitelist of valid system identifiers
VALID_SISTEMAS = frozenset({
    "amplis_reag",
    "amplis_master",
    "maps",
    "fidc",
    "qore",
    "britech",
    # Add other valid systems as needed
})


def validate_sistema(sistema: str) -> bool:
    """
    Validates a sistema identifier against whitelist.

    Args:
        sistema: Sistema identifier to validate

    Returns:
        True if valid, False otherwise
    """
    if not sistema or not isinstance(sistema, str):
        return False
    # Normalize and check against whitelist
    normalized = sistema.lower().strip()
    return normalized in VALID_SISTEMAS


def sanitize_sistemas(sistemas: List[str]) -> List[str]:
    """
    Sanitizes and validates a list of sistema identifiers.

    Args:
        sistemas: List of sistema identifiers

    Returns:
        List of validated sistema identifiers

    Raises:
        ValueError: If any sistema is invalid
    """
    if not sistemas:
        return []

    validated = []
    invalid = []

    for sistema in sistemas:
        normalized = str(sistema).lower().strip()
        if validate_sistema(normalized):
            validated.append(normalized)
        else:
            invalid.append(sistema)

    if invalid:
        logger.warning(f"Invalid sistemas rejected: {invalid}")
        raise ValueError(f"Invalid sistemas: {invalid}. Valid options: {sorted(VALID_SISTEMAS)}")

    return validated


def utc_now() -> str:
    """Retorna timestamp ISO atual"""
    return datetime.now().isoformat()


class ETLExecutor:
    """Executor de pipelines ETL via subprocess"""

    def __init__(self, slot_id: int = 0):
        """
        Args:
            slot_id: Worker slot identifier (for multiprocessing mode)
        """
        self.slot_id = slot_id
        self.process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

        # Caminhos relativos ao backend
        # __file__ -> services/executor.py
        # Subir 2 niveis: services -> backend -> DEV_ETL (root)
        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.python_dir = os.path.join(self.root_dir, "python")
        self.main_script = os.path.join(self.python_dir, "main.py")
        self.config_path = os.path.join(self.root_dir, "config", "credentials.json")

        logger.info(f"ETLExecutor initialized: root={self.root_dir}, slot={slot_id}")

    def _convert_date_format(self, date_str: str) -> str:
        """
        Converte data de formato ISO (YYYY-MM-DD) para DD/MM/YYYY
        ou mantém o formato se já estiver no formato correto
        """
        if not date_str:
            return date_str
        
        # Tentar parsear formato ISO
        try:
            # Formato ISO: YYYY-MM-DD
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%d/%m/%Y")
        except ValueError:
            pass
        
        # Se já estiver no formato DD/MM/YYYY, retornar como está
        # ou se for outro formato, tentar converter
        try:
            # Tentar vários formatos comuns
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%d/%m/%Y")
                except ValueError:
                    continue
        except Exception:
            pass
        
        # Se não conseguir converter, retornar original e deixar main.py tratar
        return date_str

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """
        Constroi comando para executar main.py com argumentos

        Args:
            params: Parametros do job (sistemas, datas, opcoes)

        Returns:
            Lista de argumentos para subprocess

        Raises:
            ValueError: If any sistema identifier is invalid
        """
        cmd = [sys.executable, self.main_script]

        # Sistemas - validate and sanitize against whitelist
        sistemas = params.get("sistemas", [])
        if sistemas:
            validated_sistemas = sanitize_sistemas(sistemas)
            if validated_sistemas:
                cmd.extend(["--sistemas"] + validated_sistemas)

        # Datas - converter para formato DD/MM/YYYY
        if params.get("data_inicial"):
            data_inicial = self._convert_date_format(params["data_inicial"])
            cmd.extend(["--data-inicial", data_inicial])
        if params.get("data_final"):
            data_final = self._convert_date_format(params["data_final"])
            cmd.extend(["--data-final", data_final])

        # Config path
        cmd.extend(["--config", self.config_path])

        # Limpar pastas
        if params.get("limpar"):
            cmd.append("--limpar")

        # Dry run
        if params.get("dry_run"):
            cmd.append("--dry-run")

        # Opcoes por sistema
        opcoes = params.get("opcoes", {})

        # AMPLIS options
        amplis_opts = {**opcoes.get("amplis_reag", {}), **opcoes.get("amplis_master", {})}
        if amplis_opts.get("csv") is False:
            cmd.append("--no-csv")
        if amplis_opts.get("pdf") is False:
            cmd.append("--no-pdf")

        # MAPS options
        maps_opts = opcoes.get("maps", {})
        if maps_opts.get("excel") is False:
            cmd.append("--maps-no-excel")
        if maps_opts.get("pdf") is False:
            cmd.append("--maps-no-pdf")
        if maps_opts.get("ativo") is False:
            cmd.append("--maps-no-ativo")
        if maps_opts.get("passivo") is False:
            cmd.append("--maps-no-passivo")

        # QORE options
        qore_opts = opcoes.get("qore", {})
        if qore_opts.get("excel") is False:
            cmd.append("--qore-no-excel")
        if qore_opts.get("pdf") is False:
            cmd.append("--qore-no-pdf")
        if qore_opts.get("lote_pdf"):
            cmd.append("--qore-lote-pdf")
        if qore_opts.get("lote_excel"):
            cmd.append("--qore-lote-excel")

        return cmd

    async def execute(
        self,
        params: Dict[str, Any],
        log_callback: Callable[[dict], Any],
        timeout_seconds: int = 3600
    ) -> bool:
        """
        Executa o pipeline ETL

        Args:
            params: Parametros do job
            log_callback: Funcao para receber logs (sync ou async)
            timeout_seconds: Timeout em segundos (padrao 1 hora)

        Returns:
            True se sucesso, False se erro
        """
        # In single mode (MAX_CONCURRENT_JOBS=1), check for existing process
        # In pool mode, each slot has its own executor instance
        from config import settings
        if settings.MAX_CONCURRENT_JOBS == 1:
            if self.process and self.process.returncode is None:
                raise Exception("Ja existe um processo em execucao")

        self._cancelled = False
        cmd = self.build_command(params)

        logger.info(f"Executando: {' '.join(cmd)}")

        # Enviar log inicial
        await self._send_log(log_callback, "INFO", "SISTEMA",
                             f"Iniciando execucao: {' '.join(cmd)}")

        # Configurar ambiente
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        try:
            # Verificar se o script existe
            if not os.path.exists(self.main_script):
                error_msg = f"Script nao encontrado: {self.main_script}"
                logger.error(error_msg)
                await self._send_log(log_callback, "ERROR", "SISTEMA", error_msg)
                return False

            # Criar processo
            try:
                self.process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,  # Capturar stderr separadamente
                    cwd=self.python_dir,
                    env=env
                )
            except Exception as e:
                error_msg = f"Erro ao criar processo: {str(e)}\nTraceback: {traceback.format_exc()}"
                logger.error(error_msg)
                await self._send_log(log_callback, "ERROR", "SISTEMA", 
                                     f"Erro ao iniciar processo: {str(e)}")
                return False

            # Ler output e stderr com timeout
            try:
                await asyncio.wait_for(
                    self._stream_output(log_callback),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                await self._send_log(log_callback, "ERROR", "SISTEMA",
                                     f"Timeout apos {timeout_seconds} segundos")
                self.cancel()
                return False

            # Aguardar finalizacao
            await self.process.wait()
            return_code = self.process.returncode

            # Ler stderr se houver
            if self.process.stderr:
                try:
                    stderr_data = await self.process.stderr.read()
                    if stderr_data:
                        stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
                        if stderr_text:
                            await self._send_log(log_callback, "ERROR", "SISTEMA",
                                                 f"Stderr: {stderr_text}")
                except Exception:
                    pass

            # Log final
            if self._cancelled:
                await self._send_log(log_callback, "WARN", "SISTEMA",
                                     "Execucao cancelada pelo usuario")
                return False
            elif return_code == 0:
                await self._send_log(log_callback, "SUCCESS", "SISTEMA",
                                     "Pipeline finalizado com sucesso")
                return True
            else:
                await self._send_log(log_callback, "ERROR", "SISTEMA",
                                     f"Pipeline finalizado com erro (code: {return_code})")
                return False

        except Exception as e:
            error_msg = f"Erro na execucao: {str(e)}\nTraceback: {traceback.format_exc()}"
            logger.error(error_msg)
            await self._send_log(log_callback, "ERROR", "SISTEMA",
                                 f"Erro na execucao: {str(e)}")
            return False
        finally:
            self.process = None

    async def _stream_output(self, log_callback: Callable):
        """Processa output do processo linha a linha"""
        # Ler stdout e stderr simultaneamente
        tasks = []
        
        # Task para stdout
        async def read_stdout():
            if not self.process.stdout:
                return
            while True:
                if self._cancelled:
                    break
                try:
                    line = await self.process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").strip()
                    if decoded:
                        parsed = self._parse_log_line(decoded)
                        await self._send_log_dict(log_callback, parsed)
                except Exception as e:
                    logger.error(f"Erro ao ler stdout: {e}")
                    break
        
        # Task para stderr
        async def read_stderr():
            if not self.process.stderr:
                return
            while True:
                if self._cancelled:
                    break
                try:
                    line = await self.process.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").strip()
                    if decoded:
                        # Log de stderr como erro
                        await self._send_log(log_callback, "ERROR", "STDERR", decoded)
                except Exception as e:
                    logger.error(f"Erro ao ler stderr: {e}")
                    break
        
        # Executar ambas as tasks
        if self.process.stdout:
            tasks.append(asyncio.create_task(read_stdout()))
        if self.process.stderr:
            tasks.append(asyncio.create_task(read_stderr()))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_log(self, callback: Callable, level: str, sistema: str, mensagem: str):
        """Envia log formatado"""
        log_entry = {
            "level": level,
            "sistema": sistema,
            "mensagem": mensagem,
            "timestamp": utc_now()
        }
        await self._send_log_dict(callback, log_entry)

    async def _send_log_dict(self, callback: Callable, log_entry: dict):
        """Envia dict de log via callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(log_entry)
            else:
                callback(log_entry)
        except Exception as e:
            logger.error(f"Erro ao enviar log: {e}")

    def _parse_log_line(self, line: str) -> dict:
        """
        Parseia linha de log no formato [LEVEL] [SISTEMA] Mensagem

        Args:
            line: Linha de output

        Returns:
            Dict com level, sistema, mensagem, timestamp
        """
        log_entry = {
            "level": "INFO",
            "sistema": "STDOUT",
            "mensagem": line,
            "timestamp": utc_now()
        }

        # Regex para formato: [LEVEL] [SISTEMA] Mensagem
        match = re.match(r'^\[(\w+)\]\s+\[([^\]]+)\]\s+(.+)$', line)
        if match:
            log_entry["level"] = match.group(1).upper()
            log_entry["sistema"] = match.group(2)
            log_entry["mensagem"] = match.group(3)

        return log_entry

    def cancel(self):
        """Cancela execucao em andamento"""
        self._cancelled = True
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                logger.info("Processo terminado")
            except Exception as e:
                logger.error(f"Erro ao terminar processo: {e}")

    @property
    def is_running(self) -> bool:
        """Verifica se ha processo em execucao"""
        return self.process is not None and self.process.returncode is None


# Singleton (for single mode: MAX_CONCURRENT_JOBS=1)
_executor_instance: Optional[ETLExecutor] = None


def get_executor(slot_id: int = 0) -> ETLExecutor:
    """
    Returns an ETLExecutor instance.

    - In single mode (MAX_CONCURRENT_JOBS=1): returns singleton
    - In pool mode (MAX_CONCURRENT_JOBS>1): returns new instance per slot

    Args:
        slot_id: Worker slot ID (only used in pool mode)

    Returns:
        ETLExecutor instance
    """
    from config import settings

    global _executor_instance

    if settings.MAX_CONCURRENT_JOBS == 1:
        # Single mode - return singleton
        if _executor_instance is None:
            _executor_instance = ETLExecutor(slot_id=0)
        return _executor_instance
    else:
        # Pool mode - new instance per slot (managed by pool)
        return ETLExecutor(slot_id=slot_id)
