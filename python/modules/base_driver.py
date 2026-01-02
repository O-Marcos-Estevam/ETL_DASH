"""
Base Driver - Selenium WebDriver centralizado para automacoes
Suporta Chrome instalado ou Chrome portatil
"""
import logging
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# Tentar importar config, mas funcionar mesmo sem
try:
    from config import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)


def get_chrome_path() -> Optional[Path]:
    """Retorna caminho do Chrome portatil se existir"""
    if settings and settings.CHROME_PATH.exists():
        return settings.CHROME_PATH
    return None


def get_chromedriver_path() -> Optional[Path]:
    """Retorna caminho do ChromeDriver portatil se existir"""
    if settings and settings.CHROMEDRIVER_PATH.exists():
        return settings.CHROMEDRIVER_PATH
    return None


def create_driver(
    download_path: Optional[str] = None,
    headless: bool = False,
    timeout: int = 30
) -> webdriver.Chrome:
    """
    Cria e configura Chrome WebDriver.
    Usa Chrome portatil se disponivel, senao usa Chrome do sistema.
    
    Args:
        download_path: Diretorio para downloads
        headless: Executar em modo headless (sem janela)
        timeout: Timeout padrao para waits
        
    Returns:
        webdriver.Chrome configurado
    """
    options = Options()
    
    # Usar Chrome portatil se disponivel
    chrome_path = get_chrome_path()
    if chrome_path:
        options.binary_location = str(chrome_path)
        logger.info(f"Usando Chrome portatil: {chrome_path}")
    
    # Configuracoes de download
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    
    if download_path:
        prefs["download.default_directory"] = str(Path(download_path).resolve())
    
    options.add_experimental_option("prefs", prefs)
    
    # Modo headless
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    
    # Opcoes para estabilidade
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Desativar notificacoes e popups
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Servico com ChromeDriver portatil
    service = None
    chromedriver_path = get_chromedriver_path()
    if chromedriver_path:
        service = Service(str(chromedriver_path))
        logger.info(f"Usando ChromeDriver portatil: {chromedriver_path}")
    
    # Criar driver
    driver = webdriver.Chrome(options=options, service=service)
    driver.implicitly_wait(timeout)
    
    logger.info("Chrome WebDriver criado com sucesso")
    return driver


def create_wait(driver: webdriver.Chrome, timeout: int = 30) -> WebDriverWait:
    """Cria WebDriverWait para o driver"""
    return WebDriverWait(driver, timeout)


class DriverManager:
    """Context manager para gerenciar ciclo de vida do driver"""
    
    def __init__(
        self,
        download_path: Optional[str] = None,
        headless: bool = False,
        timeout: int = 30
    ):
        self.download_path = download_path
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def __enter__(self) -> 'DriverManager':
        self.driver = create_driver(
            download_path=self.download_path,
            headless=self.headless,
            timeout=self.timeout
        )
        self.wait = create_wait(self.driver, self.timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver encerrado")
            except Exception as e:
                logger.warning(f"Erro ao encerrar driver: {e}")
        return False
    
    def screenshot(self, name: str = "screenshot") -> Optional[Path]:
        """Captura screenshot para debug"""
        if not self.driver:
            return None
            
        if self.download_path:
            path = Path(self.download_path) / f"{name}.png"
        else:
            path = Path(f"{name}.png")
            
        try:
            self.driver.save_screenshot(str(path))
            logger.info(f"Screenshot salvo: {path}")
            return path
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot: {e}")
            return None
