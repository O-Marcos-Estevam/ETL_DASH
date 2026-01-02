"""
ETL Dashboard Launcher
Inicia o backend e abre o navegador automaticamente
"""
import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path


def get_app_dir() -> Path:
    """Retorna diretório base da aplicação"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Aguarda servidor ficar disponível"""
    import urllib.request
    import urllib.error
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            time.sleep(0.5)
    return False


def main():
    app_dir = get_app_dir()
    backend_exe = app_dir / "runtime" / "backend" / "etl_backend.exe"
    
    # Banner
    print("=" * 60)
    print("       ETL Dashboard v2.1.0")
    print("=" * 60)
    print()
    
    # Verificar backend
    if not backend_exe.exists():
        # Tentar path alternativo (desenvolvimento)
        backend_exe = app_dir / "backend" / "app.py"
        if backend_exe.exists():
            cmd = [sys.executable, str(backend_exe)]
        else:
            print(f"[ERRO] Backend não encontrado!")
            print(f"       Procurado em: {backend_exe}")
            input("\nPressione Enter para sair...")
            return 1
    else:
        cmd = [str(backend_exe)]
    
    # Iniciar backend
    print("[INFO] Iniciando servidor backend...")
    
    try:
        backend = subprocess.Popen(
            cmd,
            cwd=str(app_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar backend: {e}")
        input("\nPressione Enter para sair...")
        return 1
    
    # Aguardar servidor
    url = "http://localhost:4001"
    health_url = f"{url}/api/health"
    
    print("[INFO] Aguardando servidor iniciar...")
    if wait_for_server(health_url, timeout=30):
        print(f"[OK] Servidor disponível em {url}")
    else:
        print("[AVISO] Servidor demorou para responder, tentando abrir mesmo assim...")
    
    # Abrir navegador
    print(f"[INFO] Abrindo navegador: {url}")
    webbrowser.open(url)
    
    print()
    print("-" * 60)
    print("  Sistema rodando!")
    print("  Feche esta janela para encerrar o servidor.")
    print("-" * 60)
    print()
    
    # Mostrar logs do backend
    try:
        while True:
            line = backend.stdout.readline()
            if not line and backend.poll() is not None:
                break
            if line:
                print(line.decode('utf-8', errors='replace').rstrip())
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando...")
        backend.terminate()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
