"""
Custom exceptions para o ETL Dashboard
"""


class ETLException(Exception):
    """Excecao base para erros do ETL"""

    def __init__(self, message: str, code: str = "ETL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "status_code": self.status_code
        }


class ExecutionError(ETLException):
    """Erro durante execucao de pipeline"""

    def __init__(self, message: str, code: str = "EXECUTION_ERROR"):
        super().__init__(message, code, status_code=500)


class ConfigurationError(ETLException):
    """Erro de configuracao"""

    def __init__(self, message: str, code: str = "CONFIG_ERROR"):
        super().__init__(message, code, status_code=400)


class ValidationError(ETLException):
    """Erro de validacao de dados"""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, status_code=422)


class DatabaseError(ETLException):
    """Erro de banco de dados"""

    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        super().__init__(message, code, status_code=500)


class TimeoutError(ETLException):
    """Erro de timeout"""

    def __init__(self, message: str = "Operacao excedeu o tempo limite"):
        super().__init__(message, "TIMEOUT_ERROR", status_code=408)
