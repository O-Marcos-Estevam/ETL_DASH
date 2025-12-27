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

logger = logging.getLogger(__name__)


def utc_now() -> str:
    """Retorna timestamp ISO atual"""
    return datetime.now().isoformat()


class ETLExecutor:
    """Executor de pipelines ETL via subprocess"""

    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self._cancelled = False

        # Caminhos relativos ao backend
        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        self.python_dir = os.path.join(self.root_dir, "python")
        self.main_script = os.path.join(self.python_dir, "main.py")
        self.config_path = os.path.join(self.root_dir, "config", "credentials.json")

        logger.info(f"ETLExecutor initialized: root={self.root_dir}")

    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """
        Constroi comando para executar main.py com argumentos

        Args:
            params: Parametros do job (sistemas, datas, opcoes)

        Returns:
            Lista de argumentos para subprocess
        """
        cmd = [sys.executable, self.main_script]

        # Sistemas
        sistemas = params.get("sistemas", [])
        if sistemas:
            cmd.extend(["--sistemas"] + sistemas)

        # Datas
        if params.get("data_inicial"):
            cmd.extend(["--data-inicial", params["data_inicial"]])
        if params.get("data_final"):
            cmd.extend(["--data-final", params["data_final"]])

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
            # Criar processo
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.python_dir,
                env=env
            )

            # Ler output com timeout
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
            logger.error(f"Erro na execucao: {e}")
            await self._send_log(log_callback, "ERROR", "SISTEMA",
                                 f"Erro na execucao: {str(e)}")
            return False
        finally:
            self.process = None

    async def _stream_output(self, log_callback: Callable):
        """Processa output do processo linha a linha"""
        while True:
            if self._cancelled:
                break

            line = await self.process.stdout.readline()
            if not line:
                break

            decoded = line.decode("utf-8", errors="replace").strip()
            if decoded:
                parsed = self._parse_log_line(decoded)
                await self._send_log_dict(log_callback, parsed)

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


# Singleton
_executor_instance: Optional[ETLExecutor] = None


def get_executor() -> ETLExecutor:
    """Retorna instancia singleton do ETLExecutor"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ETLExecutor()
    return _executor_instance
