import asyncio
import os
import sys
import logging

# Setup file logging for debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('executor_debug.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLExecutor:
    def __init__(self):
        self.process = None
        # Adjust path to reach 'python' dir from 'V2/backend'
        # Current: V2/backend/services
        # Root: ../../
        # Python: ../../python
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.python_dir = os.path.join(self.root_dir, "python")
        self.main_script = os.path.join(self.python_dir, "main.py")
        logger.info(f"ETLExecutor initialized: python_dir={self.python_dir}, main_script={self.main_script}")

    async def run_system(self, args: list, log_callback):
        """
        Executes main.py with provided arguments.
        Captures stdout/stderr and sends to log_callback.
        """
        if self.process and self.process.returncode is None:
            raise Exception("A job is already running")

        cmd = [sys.executable, self.main_script] + args
        
        # Debug: log paths
        print(f"[EXECUTOR DEBUG] root_dir: {self.root_dir}")
        print(f"[EXECUTOR DEBUG] python_dir: {self.python_dir}")
        print(f"[EXECUTOR DEBUG] main_script: {self.main_script}")
        print(f"[EXECUTOR DEBUG] main_script exists: {os.path.exists(self.main_script)}")
        print(f"[EXECUTOR DEBUG] command: {' '.join(cmd)}")
        
        # Determine ENV variables (if needed)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        try:
            # IMPORTANT: CWD must be 'python' directory for imports to work
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.python_dir,
                env=env
            )

            if asyncio.iscoroutinefunction(log_callback):
                await log_callback({
                    "level": "INFO", 
                    "sistema": "SYSTEM", 
                    "mensagem": f"Process started: {' '.join(cmd)}",
                    "timestamp": UtcNow()
                })
            else:
                 log_callback({
                    "level": "INFO", 
                    "sistema": "SYSTEM", 
                    "mensagem": f"Process started: {' '.join(cmd)}",
                    "timestamp": UtcNow()
                })

            # Stream output
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    # Parse log line if it matches [LEVEL] [SYSTEM] MSG format
                    parsed_log = self._parse_log_line(decoded_line)
                    if asyncio.iscoroutinefunction(log_callback):
                        await log_callback(parsed_log)
                    else:
                        log_callback(parsed_log)

            await self.process.wait()
            
            returnCode = self.process.returncode
            status = "SUCCESS" if returnCode == 0 else "ERROR"
            
            if asyncio.iscoroutinefunction(log_callback):
                await log_callback({
                    "level": "INFO", 
                    "sistema": "SYSTEM", 
                    "mensagem": f"Process finished with code {returnCode}",
                    "timestamp": UtcNow()
                })
            else:
                 log_callback({
                    "level": "INFO", 
                    "sistema": "SYSTEM", 
                    "mensagem": f"Process finished with code {returnCode}",
                    "timestamp": UtcNow()
                })
            
            return returnCode == 0

        except Exception as e:
            import traceback
            error_msg = f"Execution failed: {str(e)}\n{traceback.format_exc()}"
            print(f"[EXECUTOR ERROR] {error_msg}")
            error_log = {
                "level": "ERROR", 
                "sistema": "SYSTEM", 
                "mensagem": error_msg,
                "timestamp": UtcNow()
            }
            if asyncio.iscoroutinefunction(log_callback):
                await log_callback(error_log)
            else:
                log_callback(error_log)
            return False

    def _parse_log_line(self, line: str) -> dict:
        """
        Parses legacy log lines like: [INFO] [SISTEMA] Message
        Returns structured log dict.
        """
        import re
        from datetime import datetime

        # Default structure
        log_entry = {
            "level": "INFO",
            "sistema": "STDOUT",
            "mensagem": line,
            "timestamp": datetime.now().isoformat()
        }

        # Regex for legacy format: [LEVEL] [SYSTEM] Message
        # Example: [INFO] [SISTEMA] Iniciando pipeline
        match = re.match(r'^\[(\w+)\]\s+\[([^\]]+)\]\s+(.+)$', line)
        if match:
            log_entry["level"] = match.group(1)
            log_entry["sistema"] = match.group(2)
            log_entry["mensagem"] = match.group(3)
        
        return log_entry

def UtcNow():
    from datetime import datetime
    return datetime.now().isoformat()

# Singleton instance
executor = ETLExecutor()
