"""
ETL Pipeline - Main Entry Point
Executa os pipelines de ETL chamados pelo Dashboard Java
"""
import argparse
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Adiciona modules ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def log(level: str, sistema: str, mensagem: str):
    """Log formatado para parsing pelo Java"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{level}] [{sistema}] {mensagem}", flush=True)

def load_credentials(config_path: str) -> dict:
    """Carrega credenciais do arquivo JSON"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        log("ERROR", "SISTEMA", f"Arquivo de credenciais não encontrado: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log("ERROR", "SISTEMA", f"Erro ao ler JSON de credenciais: {e}")
        sys.exit(1)

def run_amplis(credentials: dict, data_inicial: str, data_final: str, 
               baixar_csv: bool = True, baixar_pdf: bool = True,
               tipo: str = "reag"):
    """Executa download AMPLIS"""
    from amplis_V02 import run_amplis as amplis_run
    
    sistema_nome = f"AMPLIS - {tipo.upper()}"
    log("INFO", sistema_nome, "Iniciando execução")
    
    try:
        creds = credentials["amplis"][tipo]
        paths = credentials["paths"]
        
        if not creds["username"] or not creds["password"]:
            log("ERROR", sistema_nome, "Credenciais não configuradas")
            return False
        
        if baixar_csv:
            log("INFO", sistema_nome, "Baixando arquivos CSV...")
        if baixar_pdf:
            log("INFO", sistema_nome, "Baixando arquivos PDF...")
        
        # Chama o módulo real
        amplis_run(
            creds["username"], 
            creds["password"], 
            creds["url"],
            credentials["amplis"]["master"]["username"] if tipo == "reag" else None,
            credentials["amplis"]["master"]["password"] if tipo == "reag" else None,
            credentials["amplis"]["master"]["url"] if tipo == "reag" else None,
            paths.get("csv", ""),
            paths.get("pdf", ""),
            data_inicial,
            data_final,
            baixar_pdf,
            baixar_csv
        )
        
        log("SUCCESS", sistema_nome, "Execução concluída com sucesso")
        return True
        
    except Exception as e:
        log("ERROR", sistema_nome, f"Erro: {str(e)}")
        return False

def clear_folders(folders: list):
    """Limpa as pastas especificadas"""
    import shutil
    
    log("INFO", "SISTEMA", f"Limpando {len(folders)} pasta(s)...")
    
    for folder in folders:
        if not folder or not os.path.exists(folder):
            continue
        try:
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            log("SUCCESS", "SISTEMA", f"Pasta limpa: {folder}")
        except Exception as e:
            log("ERROR", "SISTEMA", f"Erro ao limpar {folder}: {e}")
    
    log("SUCCESS", "SISTEMA", "Limpeza concluída")

def main():
    parser = argparse.ArgumentParser(description='ETL Pipeline Executor')
    parser.add_argument('--config', default='config/credentials.json', 
                        help='Caminho para arquivo de credenciais')
    parser.add_argument('--sistemas', nargs='+', 
                        choices=['amplis_reag', 'amplis_master', 'maps', 'fidc', 'jcot', 'britech', 'qore', 'trustee'],
                        help='Sistemas a executar')
    parser.add_argument('--data-inicial', help='Data inicial (DD/MM/YYYY)')
    parser.add_argument('--data-final', help='Data final (DD/MM/YYYY)')
    parser.add_argument('--limpar', action='store_true', help='Limpar pastas antes de executar')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar o que seria executado')
    parser.add_argument('--csv', action='store_true', default=True, help='Baixar CSV (AMPLIS)')

    parser.add_argument('--pdf', action='store_true', default=True, help='Baixar PDF (AMPLIS)')
    parser.add_argument('--fidc-fundos', help='JSON lista de fundos FIDC')
    parser.add_argument('--maps-fundos', help='JSON lista de fundos MAPS')
    parser.add_argument('--qore-fundos', help='JSON lista de fundos QORE')
    
    args = parser.parse_args()
    
    # Resolve caminho do config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', args.config)
    if not os.path.exists(config_path):
        config_path = args.config
    
    log("INFO", "SISTEMA", "Carregando configurações...")
    credentials = load_credentials(config_path)
    
    # Data padrão: D-1
    if not args.data_inicial:
        args.data_inicial = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    if not args.data_final:
        args.data_final = args.data_inicial
    
    log("INFO", "SISTEMA", f"Período: {args.data_inicial} até {args.data_final}")
    
    if args.dry_run:
        log("INFO", "SISTEMA", f"[DRY-RUN] Sistemas: {args.sistemas}")
        return 0
    
    # Limpar pastas se solicitado
    if args.limpar:
        paths = credentials.get("paths", {})
        folders_to_clean = [v for v in paths.values() if v]
        clear_folders(folders_to_clean)
    
    # Executar sistemas
    sistemas = args.sistemas or []
    total = len(sistemas)
    sucesso = 0
    erros = 0
    
    log("INFO", "SISTEMA", f"Iniciando pipeline com {total} sistema(s)")
    
    for sistema in sistemas:
        try:
            if sistema == 'amplis_reag':
                if run_amplis(credentials, args.data_inicial, args.data_final, 
                             args.csv, args.pdf, "reag"):
                    sucesso += 1
                else:
                    erros += 1
            elif sistema == 'amplis_master':
                if run_amplis(credentials, args.data_inicial, args.data_final,
                             args.csv, args.pdf, "master"):
                    sucesso += 1
                else:
                    erros += 1
            elif sistema == 'maps':
                log("INFO", "MAPS", "Iniciando execução")
                try:
                    from maps_download_consolidado import run_maps_completo
                    creds = credentials["maps"]
                    paths = credentials["paths"]
                    
                    # Determine funds
                    fundos = []
                    if args.maps_fundos:
                        fundos = json.loads(args.maps_fundos)
                    elif not creds.get("usar_todos", True):
                        fundos = creds.get("fundos_selecionados", [])
                        
                    run_maps_completo(
                        creds["url"],
                        paths.get("maps", ""),
                        paths.get("pdf", ""),
                        paths.get("maps", ""),
                        creds["username"],
                        creds["password"],
                        args.data_inicial,
                        args.data_final,
                        True, True, True, True, fundos
                    )
                    log("SUCCESS", "MAPS", "Execução concluída com sucesso")
                    sucesso += 1
                except Exception as e:
                    log("ERROR", "MAPS", f"Erro: {str(e)}")
                    erros += 1
            elif sistema == 'fidc':
                log("INFO", "FIDC ESTOQUE", "Iniciando execução")
                try:
                    from FIDC_ESTOQUE_V02 import run_fidc_estoque
                    creds = credentials["fidc"]
                    paths = credentials["paths"]
                    
                    # Determine funds
                    fundos = []
                    if args.fidc_fundos:
                        fundos = json.loads(args.fidc_fundos)
                    elif not creds.get("usar_todos", True):
                        fundos = creds.get("fundos_selecionados", [])

                    run_fidc_estoque(
                        creds["username"],
                        creds["password"],
                        paths.get("fidc", ""),
                        creds["url"],
                        args.data_inicial,
                        args.data_final,
                        fundos
                    )
                    log("SUCCESS", "FIDC ESTOQUE", "Execução concluída com sucesso")
                    sucesso += 1
                except Exception as e:
                    log("ERROR", "FIDC ESTOQUE", f"Erro: {str(e)}")
                    erros += 1
            elif sistema == 'jcot':
                log("INFO", "JCOT", "Iniciando execução")
                try:
                    from Jcot_V02 import run_jcot
                    creds = credentials["jcot"]
                    paths = credentials["paths"]
                    run_jcot(
                        creds["username"],
                        creds["password"],
                        paths.get("jcot", ""),
                        creds["url"],
                        args.data_inicial,
                        args.data_final
                    )
                    log("SUCCESS", "JCOT", "Execução concluída com sucesso")
                    sucesso += 1
                except Exception as e:
                    log("ERROR", "JCOT", f"Erro: {str(e)}")
                    erros += 1
            elif sistema == 'britech':
                log("INFO", "BRITECH", "Iniciando execução")
                try:
                    from query_britech_V02 import run_britech
                    creds = credentials["britech"]
                    paths = credentials["paths"]
                    run_britech(
                        paths.get("britech", ""),
                        creds["url"],
                        creds["username"],
                        creds["password"],
                        True  # base_total
                    )
                    log("SUCCESS", "BRITECH", "Execução concluída com sucesso")
                    sucesso += 1
                except Exception as e:
                    log("ERROR", "BRITECH", f"Erro: {str(e)}")
                    erros += 1
            elif sistema == 'qore':
                log("INFO", "QORE", "Iniciando execução")
                try:
                    from automacao_qore_v5 import run_qore
                    creds = credentials["qore"]
                    paths = credentials["paths"]
                    
                    # Determine funds
                    fundos = []
                    if args.qore_fundos:
                        fundos = json.loads(args.qore_fundos)
                    elif not creds.get("usar_todos", True):
                        fundos = creds.get("fundos_selecionados", [])

                    # QORE tem muitos parâmetros - usando valores padrão
                    run_qore(
                        paths.get("bd_xlsx", ""),  # bd_path
                        paths.get("pdf", ""),         # pdf_path
                        paths.get("qore_excel", ""),  # excel_path
                        "",                            # planilha_aux
                        creds["url"],
                        creds["password"],
                        creds["username"],
                        None,                          # df
                        True,                          # QORE_enabled
                        True,                          # PDF_enabled
                        False,                         # modo_lote_pdf
                        True,                          # Excel_enabled
                        False,                         # modo_lote_excel
                        None,                          # data_inicial
                        None,                          # data_final
                        paths.get("selenium_temp", ""), # SELENIUM_DOWNLOAD_TEMP_PATH
                        fundos                         # fundos_selecionados
                    )
                    log("SUCCESS", "QORE", "Execução concluída com sucesso")
                    sucesso += 1
                except Exception as e:
                    log("ERROR", "QORE", f"Erro: {str(e)}")
                    erros += 1
            elif sistema == 'trustee':
                log("INFO", "TRUSTEE", "Iniciando execução")
                try:
                    import subprocess
                    bat_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\0. Python\TRUSTEE\Rodar_automacao_trustee.bat"
                    if os.path.exists(bat_path):
                        subprocess.run([bat_path], check=True, timeout=300, shell=True)
                        log("SUCCESS", "TRUSTEE", "Execução concluída com sucesso")
                        sucesso += 1
                    else:
                        log("ERROR", "TRUSTEE", f"Arquivo .bat não encontrado: {bat_path}")
                        erros += 1
                except Exception as e:
                    log("ERROR", "TRUSTEE", f"Erro: {str(e)}")
                    erros += 1
            else:
                log("WARN", sistema.upper(), "Sistema desconhecido")
                erros += 1
        except Exception as e:
            log("ERROR", sistema.upper(), f"Erro: {str(e)}")
            erros += 1
    
    log("SUCCESS", "SISTEMA", f"Pipeline finalizado: {sucesso} executados, {erros} erros")
    return 0 if erros == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
