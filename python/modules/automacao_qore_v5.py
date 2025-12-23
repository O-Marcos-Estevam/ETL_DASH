import time
import re
import pandas as pd
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import os
import shutil
import zipfile
from pathlib import Path
import sys

def validar_boolean_qore(valor) -> bool:
    """
    Valida valores boolean para compatibilidade com o sistema principal
    """
    if valor is None:
        return False
    
    valor_str = str(valor).strip().upper()
    valores_true = {'TRUE', 'VERDADEIRO'}
    valores_false = {'FALSE', 'FALSO'}
    
    if valor_str in valores_true:
        return True
    elif valor_str in valores_false:
        return False
    else:
        print(f"[AVISO] Valor QORE não reconhecido: '{valor}'. Assumindo como False.")
        return False

def ler_parametros_planilha(df, QORE_enabled, PDF_enabled, modo_lote_pdf, Excel_enabled, modo_lote_excel, data_inicial_raw, data_final_raw, CAMINHO_PLANILHA_AUX_BD, CAMINHO_PLANILHA_AUX_DOWNLOAD):
    """
    Lê os parâmetros de controle da planilha DOWNLOADS_AUX.xlsx
    """
    try:
        if not isinstance(data_inicial_raw, datetime):
            raise ValueError("Data inicial inválida na célula C4")

        if not isinstance(data_final_raw, datetime):
            if modo_lote_pdf or modo_lote_excel:
                raise ValueError("Data final inválida na célula C5, e pelo menos um modo lote está ativo.")
            else:
                data_final_raw = data_inicial_raw

        print(f"[INFO] Parâmetros da planilha 'Downloads' lidos:")
        print(f"       QORE Habilitado: {QORE_enabled}")
        print(f"       PDF Habilitado: {PDF_enabled}")
        print(f"       PDF em Lote: {modo_lote_pdf}")
        print(f"       Excel Habilitado: {Excel_enabled}")
        print(f"       Excel em Lote: {modo_lote_excel}")
        print(f"       Data Inicial: {data_inicial_raw.strftime('%d/%m/%Y')}")
        if modo_lote_pdf or modo_lote_excel:
            print(f"       Data Final: {data_final_raw.strftime('%d/%m/%Y')}")

        return QORE_enabled, PDF_enabled, modo_lote_pdf, Excel_enabled, modo_lote_excel, data_inicial_raw, data_final_raw
    except Exception as e:
        print(f"[ERRO] Erro ao ler parâmetros da planilha DOWNLOADS_AUX: {str(e)}")
        sys.exit(1)

def ler_lista_fundos(caminho_planilha_bd_aux):
    """
    Lê a planilha BD.xlsx, aba BD, filtra fundos com 'QORE' exato na coluna J
    e retorna dicionário {apelido: caminho_descricao} com tratamento especial para BLOKO
    """
    try:
        df_bd = pd.read_excel(caminho_planilha_bd_aux, sheet_name="BD", engine='openpyxl')
        mask_qore_bd = df_bd.iloc[:, 9].astype(str).str.strip().str.upper() == "QORE"
        fundos_qore_filtered = df_bd[mask_qore_bd]
        fundos_dict_local = {}
        
        for _, row in fundos_qore_filtered.iterrows():
            apelido = row.iloc[1]
            caminho_descricao = row.iloc[2]
            
            if pd.notna(apelido) and pd.notna(caminho_descricao):
                apelido_clean = str(apelido).strip()
                caminho_clean = str(caminho_descricao).strip()
                
                if apelido_clean and caminho_clean:
                    # Lógica de tratamento do apelido (incluindo BLOKO)
                    apelido_partes = apelido_clean.split()
                    apelido_final = apelido_clean  # valor padrão
                    
                    if len(apelido_partes) > 1:
                        if apelido_partes[1] == "BLOKO":
                            if apelido_partes[0] == "FIP":
                                apelido_final = "BLOKO URBANISMO"
                            else: 
                                apelido_final = "BLOKO FIM"
                    
                    fundos_dict_local[apelido_final] = caminho_clean

        print(f"[INFO] Encontrados {len(fundos_dict_local)} fundos QORE:")
        for apelido, caminho in fundos_dict_local.items():
            print(f"  - {apelido}: {caminho}")
            
        return fundos_dict_local
        
    except Exception as e:
        print(f"[ERRO] Erro ao ler lista de fundos do BD.xlsx: {str(e)}")
        return {}


def ler_credenciais_e_link(df, email, senha, link, CAMINHO_PLANILHA_AUX_DOWNLOAD):
    """
    Lê as credenciais e o link do QORE da planilha DOWNLOADS_AUX.xlsx
    """
    try:
        return email, senha, link
    except Exception as e:
        print(f"[ERRO] Erro ao ler credenciais: {str(e)}")
        return "", "", ""

def extrair_siglas_e_fundos_map(fundos_dict_from_excel_param):
    """
    Extrai as siglas dos apelidos dos fundos e retorna um dicionário {apelido: sigla}.
    Para fundos BLOKO, mantém o nome completo para busca.
    """
    siglas = {}
    
    for apelido, caminho_descricao in fundos_dict_from_excel_param.items():
        apelido_partes = apelido.split()
        
        # Para fundos BLOKO, usamos o nome completo para busca
        if "BLOKO" in apelido.upper():
            sigla_para_busca = apelido  # Usa o nome completo (BLOKO URBANISMO ou BLOKO FIM)
            print(f"[INFO] Fundo BLOKO encontrado: {apelido}. Usando nome completo para busca.")
        else:
            # Para outros fundos, usa a segunda palavra como sigla
            sigla_para_busca = apelido_partes[1] if len(apelido_partes) > 1 else apelido
        
        siglas[apelido] = sigla_para_busca
    
    print(f"[INFO] Siglas extraídas dos apelidos para busca:")
    for apelido, sigla in siglas.items():
        print(f"  - {apelido}: {sigla}")
    
    return siglas


def get_final_path(data_dt, report_type, fundo_nome_atual, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH):
    """
    Determina o caminho final baseado na data, tipo de relatório e, para PDFs, no caminho_descricao do fundo.
    """
    ano = data_dt.strftime("%Y")
    mes_numero = data_dt.strftime("%m") 
    
    meses_por_extenso = {
        "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
        "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
        "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
    }
    
    final_path = ""
    caminho_descricao_fundo = fundos_dict_param.get(fundo_nome_atual)
    
    if report_type.upper() == "PDF" and caminho_descricao_fundo:
        mes_formatado = f"{mes_numero} - {meses_por_extenso.get(mes_numero, '')}"
        caminho_base_fundos = r"C:\bloko\Fundos - Documentos"
        final_path = os.path.join(caminho_base_fundos, caminho_descricao_fundo, "06. Carteiras", ano, mes_formatado)
    elif report_type.upper() == "EXCEL":
        final_path = QORE_EXCEL_PATH
    else:
        base_dir = QORE_PDF_PATH 
        if not base_dir:
            raise ValueError(f"Caminho base não definido para {report_type}")
        final_path = os.path.join(base_dir, ano, mes_numero)
           
    os.makedirs(final_path, exist_ok=True)
    return final_path

def get_versioned_filepath(directory, base_filename_without_ext, extension):
    """
    Gera um caminho de arquivo, adicionando um sufixo de versão (X) se o arquivo já existir.
    Retorna o caminho completo e a versão utilizada (0 se for o original, 1 para (1), 2 para (2), etc.).
    """
    target_path = os.path.join(directory, f"{base_filename_without_ext}{extension}")
    
    if not os.path.exists(target_path):
        return target_path, 0
    
    version_suffix_num = 1
    while True:
        versioned_filename = f"{base_filename_without_ext} ({version_suffix_num}){extension}"
        target_path_with_suffix = os.path.join(directory, versioned_filename)
        
        if not os.path.exists(target_path_with_suffix):
            return target_path_with_suffix, version_suffix_num
        
        version_suffix_num += 1

def get_versioned_filepath(directory, base_filename_without_ext, extension):
    """
    Gera um caminho de arquivo, adicionando um sufixo de versão (X) se o arquivo já existir.
    Retorna o caminho completo e a versão utilizada (0 se for o original, 1 para (1), 2 para (2), etc.).
    """
    target_path = os.path.join(directory, f"{base_filename_without_ext}{extension}")
    
    if not os.path.exists(target_path):
        return target_path, 0
    
    version_suffix_num = 1
    while True:
        versioned_filename = f"{base_filename_without_ext} ({version_suffix_num}){extension}"
        target_path_with_suffix = os.path.join(directory, versioned_filename)
        
        if not os.path.exists(target_path_with_suffix):
            return target_path_with_suffix, version_suffix_num
        
        version_suffix_num += 1

def handle_downloaded_file(fundo_nome, data_referencia, em_lote, report_type, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH):
    """
    Move e renomeia os arquivos baixados do diretório temporário para a pasta de destino final.
    """
    if "BLOKO" in fundo_nome:
        handle_downloaded_file_bloko(fundo_nome, data_referencia, em_lote, report_type, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH)
    else:
        if fundo_nome not in all_siglas_param:
            print(f"[ERRO] Fundo não reconhecido para mover/renomear: {fundo_nome}.")
            return False

        sigla = all_siglas_param[fundo_nome]
        
        data_dt = data_referencia
        dia = data_dt.strftime("%d")
        mes = data_dt.strftime("%m")
        
        config_details = {
            "PDF": {
                "extension": ".pdf",
            # "pattern": f"carteira-{sigla.lower()}-fip-multiestrategia".replace('-', '_'),
                "type_name": "Carteira Diária",
                "name_base": f"{dia}.{mes} - Carteira Diária - {fundo_nome}"  # MUDANÇA AQUI
            },
            "Excel": {
                "extension": ".xlsx",
            # "pattern": f"carteira-{sigla.lower()}-fip-multiestrategia".replace('-', '_'),
                "type_name": "Carteira Excel",
                "name_base": f"{dia}.{mes} - Carteira Excel - {fundo_nome}"  # MUDANÇA AQUI
            }
        }

        if report_type not in config_details:
            print(f"[ERRO] Tipo de relatório '{report_type}' desconhecido para processar download.")
            return False
        
        cfg = config_details[report_type]
        
        try:
            if em_lote:
                zip_files = list(Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob("*.zip"))
                if not zip_files:
                    print(f"[!] Nenhum arquivo ZIP encontrado para o fundo '{fundo_nome}' ({report_type}).")
                    return False 
                
                zip_file = max(zip_files, key=os.path.getctime)
                print(f"[INFO] Extraindo arquivos do ZIP: {zip_file.name} para {SELENIUM_DOWNLOAD_TEMP_PATH}")
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(SELENIUM_DOWNLOAD_TEMP_PATH)
                os.remove(zip_file) 

                arquivos_processados_count = 0 
                

                for arquivo in Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob(f"*{cfg['extension']}"):
                    # Verifica se o arquivo contém a sigla do fundo (mais flexível)
                    arquivo_nome_lower = arquivo.name.lower()
                    sigla_lower = sigla.lower()
                    
                    # Verifica se a sigla está presente no nome do arquivo
                    if sigla_lower not in arquivo_nome_lower:
                        print(f"[DEBUG] Arquivo '{arquivo.name}' não contém a sigla '{sigla}', pulando...")
                        continue
                    
                    # Tenta extrair a data do nome do arquivo
                    batch_file_date_dt = data_referencia 
                    try:
                        # Procura por padrão de data no formato YYYYMMDD no nome do arquivo
                        import re
                        date_match = re.search(r'(\d{8})', arquivo.stem)
                        if date_match:
                            date_str = date_match.group(1)
                            batch_file_date_dt = datetime.strptime(date_str, "%Y%m%d")
                            print(f"[DEBUG] Data extraída do arquivo '{arquivo.name}': {batch_file_date_dt.strftime('%d/%m/%Y')}")
                        else:
                            print(f"[DEBUG] Não foi possível extrair data do arquivo '{arquivo.name}', usando data de referência")
                    except (ValueError, IndexError) as e:
                        print(f"[DEBUG] Erro ao extrair data do arquivo '{arquivo.name}': {e}")
                        pass

                    current_base_filename_without_ext = f"{batch_file_date_dt.strftime('%d.%m')} - {cfg['type_name']} - {fundo_nome}"  # MUDANÇA AQUI (linha ~185)

                    destino_dir = get_final_path(batch_file_date_dt, report_type, fundo_nome, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH)
                    
                    final_destino, version_num = get_versioned_filepath(destino_dir, current_base_filename_without_ext, cfg['extension'])
                    
                    print(f"[DEBUG] Movendo arquivo '{arquivo.name}' para '{final_destino}'")
                    shutil.move(str(arquivo), final_destino)
                    if version_num > 0:
                        print(f"[✔️] {report_type} movido (versão {version_num}) para: {final_destino}")
                    else:
                        print(f"[✔️] {report_type} movido para: {final_destino}")
                    arquivos_processados_count += 1
                
                if arquivos_processados_count == 0:
                    print(f"[ERRO] Nenhum arquivo com sigla '{sigla}' encontrado nos arquivos extraídos para {report_type}")
                    # Lista todos os arquivos para debug
                    all_files = list(Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob(f"*{cfg['extension']}"))
                    print(f"[DEBUG] Arquivos {cfg['extension']} encontrados na pasta temporária:")
                    for f in all_files:
                        print(f"  - {f.name}")
                    return False
                    
                return arquivos_processados_count > 0 

            else:
                print(f"[INFO] Aguardando download do {report_type} na pasta de downloads temporários...")
                timeout = time.time() + 30 
                found_file = None
                
                while time.time() < timeout:
                    files_of_type = list(Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob(f"*{cfg['extension']}"))
                    files_of_type.sort(key=os.path.getmtime, reverse=True)
                    
                    if files_of_type:
                        found_file = files_of_type[0]
                        if sigla.lower() in found_file.name.lower(): 
                            break
                        else: 
                            print(f"[AVISO] Arquivo '{found_file.name}' não corresponde à sigla '{sigla}'. Aguardando mais...")
                    time.sleep(1)

                if not found_file:
                    print(f"[!] Timeout: Não foi possível encontrar nenhum arquivo '{cfg['extension']}' para '{sigla}' após 30 segundos em '{SELENIUM_DOWNLOAD_TEMP_PATH}'.")
                    return False 
                
                destino_dir = get_final_path(data_dt, report_type, fundo_nome, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH)
                
                final_destino, version_num = get_versioned_filepath(destino_dir, cfg['name_base'], cfg['extension'])

                shutil.move(str(found_file), final_destino)
                if version_num > 0:
                    print(f"[✔️] {report_type} movido (versão {version_num}) para: {final_destino}")
                else:
                    print(f"[✔️] {report_type} movido para: {final_destino}")
                return True 
                
        except Exception as e:
            print(f"[ERRO] Falha ao mover ou renomear {report_type} para o fundo '{fundo_nome}': {str(e)}")
            return False
    

def handle_downloaded_file_bloko(fundo_nome, data_referencia, em_lote, report_type, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH):
    """
    Versão corrigida que:
    1. Primeiro extrai o ZIP completamente
    2. Depois processa e move os arquivos para a pasta final
    3. Faz limpeza dos arquivos temporários
    """
    if fundo_nome not in all_siglas_param:
        print(f"[ERRO] Fundo não reconhecido: '{fundo_nome}'")
        return False

    # Configurações
    cfg = {
        "extension": ".xlsx",
        "type_name": "Carteira Excel",
        "name_base": f"{data_referencia.strftime('%d.%m')} - Carteira Excel - {fundo_nome}",
        "timeout": 120
    }

    try:
        if em_lote:
            print("[INFO] Processando arquivos em lote (ZIP)...")
            
            # 1. Encontra o arquivo ZIP mais recente
            zip_files = list(Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob("*.zip"))
            if not zip_files:
                print("[ERRO] Nenhum arquivo ZIP encontrado na pasta temporária!")
                return False
                
            zip_file = max(zip_files, key=os.path.getmtime)
            print(f"[INFO] Arquivo ZIP encontrado: {zip_file.name}")

            # 2. Cria uma pasta temporária para extração
            temp_extract_dir = Path(SELENIUM_DOWNLOAD_TEMP_PATH) / "temp_extract"
            temp_extract_dir.mkdir(exist_ok=True)
            
            # 3. Extrai o ZIP para a pasta temporária
            print(f"[INFO] Extraindo arquivos para: {temp_extract_dir}")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # 4. Remove o arquivo ZIP original
            zip_file.unlink()
            print("[INFO] ZIP extraído e removido com sucesso")

            # 5. Processa cada arquivo extraído
            arquivos_processados = 0
            padroes_busca = {
                "BLOKO URBANISMO": "urbanismo",
                "BLOKO FIM": "fundo-de-investimento"
            }
            
            padrao_busca = padroes_busca.get(fundo_nome, "").lower()
            if not padrao_busca:
                print(f"[ERRO] Padrão de busca não definido para: {fundo_nome}")
                return False

            for arquivo in temp_extract_dir.glob(f"*{cfg['extension']}"):
                arquivo_nome = arquivo.name.lower()
                
                # Verifica se o arquivo pertence ao fundo
                if padrao_busca in arquivo_nome:
                    print(f"[DEBUG] Processando arquivo: {arquivo.name}")
                    
                    # Extrai a data do nome do arquivo (formato: YYYYMMDD)
                    try:
                        date_match = re.search(r'(\d{4})(\d{2})(\d{2})', arquivo.name)
                        if date_match:
                            data_arquivo = datetime.strptime(
                                f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}", 
                                "%Y-%m-%d"
                            )
                        else:
                            data_arquivo = data_referencia
                    except Exception as e:
                        print(f"[AVISO] Não foi possível extrair data do arquivo: {e}")
                        data_arquivo = data_referencia
                    
                    # Prepara o nome do arquivo final
                    nome_base = f"{data_arquivo.strftime('%d.%m')} - {cfg['type_name']} - {fundo_nome}"
                    
                    # Obtém o caminho de destino final
                    destino_dir = get_final_path(
                        data_arquivo, 
                        report_type, 
                        fundo_nome, 
                        fundos_dict_param, 
                        QORE_PDF_PATH, 
                        QORE_EXCEL_PATH
                    )
                    os.makedirs(destino_dir, exist_ok=True)
                    
                    # Gera o caminho final com tratamento de versões
                    final_destino, version_num = get_versioned_filepath(
                        destino_dir, 
                        nome_base, 
                        cfg['extension']
                    )
                    
                    # Move o arquivo para o destino final
                    try:
                        shutil.move(str(arquivo), str(final_destino))
                        print(f"[✔️] Arquivo movido para: {final_destino}")
                        arquivos_processados += 1
                    except Exception as move_error:
                        print(f"[ERRO] Falha ao mover arquivo: {move_error}")
                        # Tenta copiar como fallback
                        try:
                            shutil.copy(str(arquivo), str(final_destino))
                            arquivo.unlink()  # Remove o arquivo original
                            print(f"[AVISO] Arquivo copiado para: {final_destino}")
                            arquivos_processados += 1
                        except Exception as copy_error:
                            print(f"[ERRO CRÍTICO] Falha ao copiar arquivo: {copy_error}")
            
            # 6. Limpa a pasta temporária de extração
            try:
                shutil.rmtree(temp_extract_dir)
                print("[INFO] Pasta temporária de extração removida")
            except Exception as clean_error:
                print(f"[AVISO] Erro ao limpar pasta temporária: {clean_error}")
            
            if arquivos_processados == 0:
                print("[ERRO] Nenhum arquivo correspondente foi processado!")
                return False
                
            return True

        else:
            # Processamento para modo individual (não em lote)
            print("[INFO] Processando arquivo individual...")
            
            timeout = time.time() + cfg['timeout']
            found_file = None
            padrao_busca = "urbanismo" if "URBANISMO" in fundo_nome.upper() else "investimento"
            
            while time.time() < timeout:
                # Lista arquivos ordenados por modificação (mais recente primeiro)
                arquivos = sorted(
                    Path(SELENIUM_DOWNLOAD_TEMP_PATH).glob(f"*{cfg['extension']}"),
                    key=os.path.getmtime,
                    reverse=True
                )
                
                for arquivo in arquivos:
                    if padrao_busca.lower() in arquivo.name.lower():
                        # Verifica se o download foi completado
                        size1 = arquivo.stat().st_size
                        time.sleep(1)
                        size2 = arquivo.stat().st_size
                        
                        if size1 == size2:  # Download completo
                            found_file = arquivo
                            break
                
                if found_file:
                    break
                    
                time.sleep(5)
            
            if not found_file:
                print("[ERRO] Timeout - Nenhum arquivo válido encontrado")
                return False
            
            # Prepara o destino final
            destino_dir = get_final_path(
                data_referencia,
                report_type,
                fundo_nome,
                fundos_dict_param,
                QORE_PDF_PATH,
                QORE_EXCEL_PATH
            )
            os.makedirs(destino_dir, exist_ok=True)
            
            # Gera o nome final
            final_destino, version_num = get_versioned_filepath(
                destino_dir,
                cfg['name_base'],
                cfg['extension']
            )
            
            # Move o arquivo
            try:
                shutil.move(str(found_file), str(final_destino))
                print(f"[✔️] Arquivo movido para: {final_destino}")
                return True
            except Exception as move_error:
                print(f"[ERRO] Falha ao mover arquivo: {move_error}")
                # Tenta copiar como fallback
                try:
                    shutil.copy(str(found_file), str(final_destino))
                    found_file.unlink()
                    print(f"[AVISO] Arquivo copiado para: {final_destino}")
                    return True
                except Exception as copy_error:
                    print(f"[ERRO CRÍTICO] Falha ao copiar arquivo: {copy_error}")
                    return False
    
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha inesperada: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def preencher_data_robusto(campo, data_dt, driver):
    """
    Preenche um campo de data no navegador de forma robusta usando JavaScript.
    """
    try:
        data_iso = data_dt.strftime("%Y-%m-%d")
        driver.execute_script(f'''
            var campo = arguments[0];
            campo.value = '{data_iso}';
            var eventNames = ['focus', 'input', 'change', 'blur'];
            eventNames.forEach(function(eventName) {{
                var event = new Event(eventName, {{bubbles: true}});
                campo.dispatchEvent(event);
            }});
            if (typeof campo.onchange === 'function') {{
                campo.onchange();
            }}
        ''', campo)
        time.sleep(1)
    except Exception as e:
        print(f"[ERRO] Erro ao preencher data: {str(e)}")

def process_document_type(fundo_nome_chave, data_exibicao, data_obj, is_batch_mode, data_inicial_dt, data_final_dt, report_type, download_button_text, driver, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH):
    """
    Função genérica para processar o download de PDF ou Excel para um fundo.
    Assume que o driver já está na página de detalhes do fundo.
    """
    sigla_para_busca = all_siglas_param.get(fundo_nome_chave)
    if not sigla_para_busca:
        print(f"[AVISO] Sigla não encontrada para o fundo: '{fundo_nome_chave}'. Pulando {report_type} download.")
        return False

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//button[contains(., "{download_button_text}")]'))
        ).click()
        time.sleep(3)
    except TimeoutException:
        print(f"[ERRO] Botão '{download_button_text}' não encontrado para o fundo '{fundo_nome_chave}'. Pulando {report_type} download.")
        return False
    
    if not is_batch_mode:
        document_found_on_site = False 
        linhas = driver.find_elements(By.XPATH, '//table/tbody/tr') 
        for linha in linhas:
            colunas = linha.find_elements(By.TAG_NAME, 'td')
            if len(colunas) >= 3 and colunas[1].text.strip() == data_exibicao:
                botao = colunas[3].find_element(By.TAG_NAME, 'button')
                botao.click()
                print(f"[⬇️] Baixando {report_type} do fundo {fundo_nome_chave}")
                time.sleep(2)
                return handle_downloaded_file(fundo_nome_chave, data_obj, False, report_type, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH)
        
        if not document_found_on_site:
            print(f"[AVISO] Nenhum {report_type} encontrado para a data '{data_exibicao}' no fundo '{fundo_nome_chave}' no site. Pulando download.")
            return False

    else:
        menu_botoes = driver.find_elements(By.XPATH, '//div[@data-kt-menu-trigger="click"]')
        found_ellipsis_button = False
        for b in menu_botoes:
            try:
                if "ellipsis-h" in b.find_element(By.TAG_NAME, 'i').get_attribute("class"):
                    b.click()
                    found_ellipsis_button = True
                    break
            except NoSuchElementException:
                continue
            except Exception as e_inner:
                print(f"[AVISO] Erro ao inspecionar botão de menu para {fundo_nome_chave} ({report_type}): {e_inner}")
                continue
        
        if not found_ellipsis_button:
            print(f"[ERRO] Não foi encontrado o botão de menu '...' para o fundo {fundo_nome_chave} ({report_type}). Pulando download em lote.")
            return False

        time.sleep(1)
        download_lote_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(., "Download em Lote")]'))
        )
        download_lote_button.click()
        time.sleep(2)
        
        preencher_data_robusto(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dataInicial"))), data_inicial_dt, driver)
        preencher_data_robusto(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dataFinal"))), data_final_dt, driver)
        driver.execute_script("[document.getElementById('dataInicial'), document.getElementById('dataFinal')].forEach(c => c.dispatchEvent(new Event('change')));")
        time.sleep(2)
        
        botao_download = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Download")]')))
        botao_download.click()
        print(f"[⬇️] Baixando lote do {report_type} do fundo {fundo_nome_chave}") 
        time.sleep(4)
        return handle_downloaded_file(fundo_nome_chave, data_final_dt, True, report_type, all_siglas_param, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict_param, QORE_PDF_PATH, QORE_EXCEL_PATH) 

    return False

def run_qore(CAMINHO_PLANILHA_AUX_BD, QORE_PDF_PATH_DEFAULT, QORE_EXCEL_PATH_DEFAULT, CAMINHO_PLANILHA_AUX_DOWNLOAD, link_dashboard, senha, email, df, QORE_enabled, PDF_enabled, modo_lote_pdf, Excel_enabled, modo_lote_excel, data_inicial_dt, data_final_dt, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_selecionados=None):
    """
    Execução principal do script QORE
    """
    print("=" * 50)
    print("INICIANDO AUTOMAÇÃO QORE")
    if fundos_selecionados:
        print(f"Fundos selecionados: {len(fundos_selecionados)}")
    print("=" * 50)

    # Define os caminhos
    QORE_PDF_PATH = QORE_PDF_PATH_DEFAULT
    QORE_EXCEL_PATH = QORE_EXCEL_PATH_DEFAULT

    # Limpa a pasta temporária de downloads do Selenium antes de iniciar
    try:
        if os.path.exists(SELENIUM_DOWNLOAD_TEMP_PATH):
            for item in os.listdir(SELENIUM_DOWNLOAD_TEMP_PATH):
                item_path = os.path.join(SELENIUM_DOWNLOAD_TEMP_PATH, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            print(f"[INFO] Pasta temporária limpa: {SELENIUM_DOWNLOAD_TEMP_PATH}")
    except Exception as e:
        print(f"[AVISO] Erro ao limpar pasta temporária: {e}")

    # Lê os parâmetros da planilha de download
    ler_parametros_planilha(df, QORE_enabled, PDF_enabled, modo_lote_pdf, Excel_enabled, modo_lote_excel, data_inicial_dt, data_final_dt, CAMINHO_PLANILHA_AUX_BD, CAMINHO_PLANILHA_AUX_DOWNLOAD)

    # Verifica se a automação QORE está habilitada
    if not QORE_enabled:
        print("[INFO] Automação QORE desabilitada na planilha 'Downloads'. Encerrando o script.")
        sys.exit(0)

    # Verifica se pelo menos um tipo de download (PDF ou Excel) está habilitado
    if not PDF_enabled and not Excel_enabled:
        print("[INFO] Nem PDF nem Excel estão habilitados para QORE. Encerrando.")
        sys.exit(0)

    # Carrega a lista de fundos
    fundos_dict = ler_lista_fundos(CAMINHO_PLANILHA_AUX_BD)
    if not fundos_dict:
        print("[ERRO] Nenhum fundo QORE encontrado no BD. Encerrando.")
        sys.exit(1)

    # Filtrar fundos se especificado
    if fundos_selecionados and len(fundos_selecionados) > 0:
        print(f"[INFO] Filtrando fundos. Selecionados: {len(fundos_selecionados)}")
        fundos_dict_filtrado = {k: v for k, v in fundos_dict.items() if k in fundos_selecionados}
        if not fundos_dict_filtrado:
            print("[AVISO] Nenhum fundo selecionado foi encontrado na lista do BD. Verifique os nomes.")
        fundos_dict = fundos_dict_filtrado
        print(f"[INFO] Fundos após filtro: {len(fundos_dict)}")

    all_siglas = extrair_siglas_e_fundos_map(fundos_dict) 

    # Lê as credenciais e o link do dashboard
    if not all([email, senha, link_dashboard]):
        print("[ERRO] Credenciais ou link do dashboard não encontrados na planilha. Encerrando.")
        sys.exit(1)

    # Configura e inicia o Chrome driver
    chrome_options = Options()
    prefs = {
        "download.default_directory": SELENIUM_DOWNLOAD_TEMP_PATH,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar Chrome driver: {e}")
        sys.exit(1)

    # Realiza o login no sistema QORE
    print(f"[INFO] Acessando dashboard: {link_dashboard}")
    try:
        driver.get(link_dashboard)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'email'))).send_keys(email)
        driver.find_element(By.NAME, 'password').send_keys(senha + Keys.RETURN)
        WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))
        print("[INFO] Login realizado com sucesso!")
    except TimeoutException:
        print("[ERRO] Timeout durante o login - verifique credenciais ou conectividade. Encerrando.")
        driver.quit()
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Falha no login: {e}. Encerrando.")
        driver.quit()
        sys.exit(1)

    # Determina a data de exibição para logs e a data objeto para downloads únicos
    data_exibicao = data_final_dt.strftime("%d/%m/%Y") if (modo_lote_pdf or modo_lote_excel) else data_inicial_dt.strftime("%d/%m/%Y")
    data_obj = data_inicial_dt 

    print(f"\n[INFO] Processando {len(fundos_dict)} fundos para {data_exibicao}")
    print(f"[INFO] Tipos habilitados: PDF={PDF_enabled}, Excel={Excel_enabled}")

    sucessos_total = 0
    total_fundos = len(fundos_dict)

    # Loop pelos fundos
    for nome_fundo_chave in fundos_dict: 
        try:
            sigla_para_busca = all_siglas.get(nome_fundo_chave)
            if not sigla_para_busca:
                print(f"[AVISO] Sigla não encontrada para o fundo: '{nome_fundo_chave}'. Pulando este fundo.")
                continue

            print(f"\n➡️ Processando fundo: {nome_fundo_chave} (Busca por: '{sigla_para_busca}')")
            
            # Navega para o dashboard, depois para a página do fundo
            driver.get(link_dashboard) 
            time.sleep(3)
            
            fund_link_element = None
            try:
                # Busca pelo texto completo (para BLOKO) ou pela sigla (para outros)
                fund_link_element = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, sigla_para_busca))
                )
                
            except TimeoutException:
                print(f"[ERRO] Fundo '{nome_fundo_chave}' não encontrado ou não clicável no site com a sigla '{sigla_para_busca}'. Pulando este fundo.")
                continue 

            fund_link_element.click() 
            time.sleep(4)

            current_fund_success = False

            # Processa PDF (se habilitado)
            if PDF_enabled:
                print(f"[INFO] Iniciando processamento de PDF para o fundo {nome_fundo_chave}")
                if process_document_type(nome_fundo_chave, data_exibicao, data_obj, modo_lote_pdf, data_inicial_dt, data_final_dt, "PDF", "Carteira PDF", driver, all_siglas, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict, QORE_PDF_PATH, QORE_EXCEL_PATH):
                    print(f"[INFO] PDF processado com sucesso para {nome_fundo_chave}")
                    current_fund_success = True
                else:
                    print(f"[AVISO] Falha no processamento PDF para {nome_fundo_chave}")

            # Processa Excel (se habilitado)
            if Excel_enabled:
                # Clicar "Voltar" e re-navegar para a página do fundo antes de processar Excel
                try:
                    print(f"[INFO] Clicando no botão 'Voltar' para o fundo {nome_fundo_chave} antes de processar Excel.")
                    back_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Voltar")]')))
                    back_button.click()
                    time.sleep(3)

                    print(f"[INFO] Navegando novamente para a página do fundo {nome_fundo_chave} para processar Excel.")
                    WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))
                    
                    fund_link_element_for_excel = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, sigla_para_busca))
                    )
                    fund_link_element_for_excel.click()
                    time.sleep(4)
                except TimeoutException:
                    print(f"[AVISO] Timeout ao tentar clicar no botão 'Voltar' ou re-navegar para o fundo {nome_fundo_chave}. Tentando processar Excel mesmo assim.")
                    # Fallback: tenta voltar ao dashboard e re-clicar no link
                    driver.get(link_dashboard) 
                    time.sleep(3)
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, sigla_para_busca))
                        ).click()
                        time.sleep(4)
                    except:
                        print("[AVISO] Falha em nova tentativa de re-navegar para o fundo. Processando Excel sem re-navegação garantida.")
                except Exception as e:
                    print(f"[ERRO] Erro inesperado ao tentar clicar em 'Voltar' ou navegar novamente para {nome_fundo_chave}: {e}. Processando Excel sem re-navegação garantida.")
                    # Tenta ir para o dashboard e depois para a página do fundo novamente.
                    driver.get(link_dashboard) 
                    time.sleep(3)
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, sigla_para_busca))
                        ).click()
                        time.sleep(4)
                    except:
                        print("[AVISO] Falha em nova tentativa de re-navegar para o fundo. Processando Excel sem re-navegação garantida.")

                print(f"[INFO] Iniciando processamento de Excel para o fundo {nome_fundo_chave}")
                if process_document_type(nome_fundo_chave, data_exibicao, data_obj, modo_lote_excel, data_inicial_dt, data_final_dt, "Excel", "Carteira Excel", driver, all_siglas, SELENIUM_DOWNLOAD_TEMP_PATH, fundos_dict, QORE_PDF_PATH, QORE_EXCEL_PATH):
                    print(f"[INFO] Excel processado com sucesso para {nome_fundo_chave}")
                    current_fund_success = True 
                else:
                    print(f"[AVISO] Falha no processamento Excel para {nome_fundo_chave}")
            else:
                print(f"[INFO] Download de Excel desabilitado para o fundo {nome_fundo_chave}.")
            
            if current_fund_success:
                sucessos_total += 1
            
        except Exception as e:
            print(f"[ERRO] Falha inesperada ao processar fundo {nome_fundo_chave}: {str(e)}")
            continue

    print(f"\n[INFO] Processamento QORE concluído: {sucessos_total}/{total_fundos} fundos processados com sucesso")

    # Finalização
    print("Processo concluído.")
    time.sleep(2) 
    if driver:
        try:
            driver.quit()
            print("[INFO] Driver Chrome encerrado.")
        except Exception as e:
            print(f"[AVISO] Erro ao encerrar o driver Chrome: {e}")

    # Sai do script com o código de status apropriado (0 para sucesso, 1 para falha)
    sys.exit(0 if sucessos_total > 0 else 1)


if __name__ == "__main__":
    # ==================== DECLARAÇÃO DE VARIÁVEIS ====================
    
    # Configurações padrão (modo desenvolvimento/teste)
    CAMINHO_PLANILHA_AUX_DOWNLOAD = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\07. DEPARA\DOWNLOADS_AUX.xlsx"

    # ==================== INTERAÇÃO PARA CONFIRMAR CAMINHO ====================
    print("=" * 80)
    print("AUTOMAÇÃO QORE - CONFIGURAÇÃO INICIAL")
    print("=" * 80)
    print(f"\nCaminho padrão da planilha Downloads:")
    print(f"{CAMINHO_PLANILHA_AUX_DOWNLOAD}")
    print("\nEste é o caminho correto da planilha Downloads? (S/N)")
    
    resposta = input("Digite S para SIM ou N para NÃO: ").strip().upper()
    
    if resposta == 'N' or resposta == 'NAO' or resposta == 'NÃO':
        print("\nDigite o caminho correto da planilha Downloads:")
        novo_caminho = input("Caminho: ").strip()
        
        # Remove aspas se o usuário colou um caminho com aspas
        if novo_caminho.startswith('"') and novo_caminho.endswith('"'):
            novo_caminho = novo_caminho[1:-1]
        elif novo_caminho.startswith("'") and novo_caminho.endswith("'"):
            novo_caminho = novo_caminho[1:-1]
        
        CAMINHO_PLANILHA_AUX_DOWNLOAD = novo_caminho
        print(f"\nCaminho atualizado para: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
    
    elif resposta == 'S' or resposta == 'SIM':
        print("\nUsando o caminho padrão...")
    
    else:
        print("\nResposta não reconhecida. Usando o caminho padrão...")
    
    # Verifica se o arquivo existe
    if not os.path.exists(CAMINHO_PLANILHA_AUX_DOWNLOAD):
        print(f"\n[ERRO] Arquivo não encontrado: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
        print("Verifique se o caminho está correto e tente novamente.")
        input("\nPressione Enter para sair...")
        sys.exit(1)
    
    print(f"\n[INFO] Arquivo encontrado com sucesso!")
    print("=" * 80)

    # Lê da planilha os outros caminhos (modo padrão)
    try:
        df = pd.read_excel(CAMINHO_PLANILHA_AUX_DOWNLOAD, sheet_name="Downloads", engine='openpyxl', header=None)
        CAMINHO_PLANILHA_AUX_BD = str(df.iloc[18, 8]).strip()
        QORE_PDF_PATH_DEFAULT = str(df.iloc[8, 8]).strip()
        QORE_EXCEL_PATH_DEFAULT = str(df.iloc[12, 8]).strip()   
        SELENIUM_DOWNLOAD_TEMP_PATH = str(df.iloc[19, 8]).strip()
    except Exception as e:
        print(f"\n[ERRO] Erro ao ler a planilha: {e}")
        print("Verifique se a planilha está no formato correto.")
        input("\nPressione Enter para sair...")
        sys.exit(1)
       
    # ==================== LEITURA DAS OUTRAS VARIÁVEIS DA PLANILHA ====================
    # Todas as variáveis estão centralizadas aqui - fácil de encontrar e alterar
    email = str(df.iloc[9, 13]).strip()                           # Login do QORE
    senha = str(df.iloc[9, 14]).strip()                           # Senha do QORE
    link = str(df.iloc[9, 12]).strip()                            # URL do dashboard QORE
    QORE_enabled = validar_boolean_qore(df.iloc[23, 2])           # Se automação está ativa
    PDF_enabled = validar_boolean_qore(df.iloc[24, 2])            # Se deve baixar PDFs
    modo_lote_pdf = validar_boolean_qore(df.iloc[25, 2])          # Se PDF é em lote
    Excel_enabled = validar_boolean_qore(df.iloc[26, 2])          # Se deve baixar Excel
    modo_lote_excel = validar_boolean_qore(df.iloc[27, 2])        # Se Excel é em lote
    data_inicial_raw = df.iloc[3, 2]                              # Data de início
    data_final_raw = df.iloc[4, 2]                                # Data de fim
    
    # Outras variáveis de configuração (podem ser alteradas aqui)
    timeout_login = 15                                            # Tempo limite para login
    timeout_elementos = 10                                        # Tempo limite para elementos
    timeout_download = 30                                         # Tempo limite para downloads
    pausa_navegacao = 3                                           # Pausa entre navegações
    pausa_clique = 2                                              # Pausa após cliques
    pausa_final = 2                                               # Pausa antes de fechar
    
    # Configurações do Chrome (podem ser alteradas aqui)
    window_size = "1920,1080"                                     # Tamanho da janela
    chrome_args = [                                               # Argumentos do Chrome
        "--no-sandbox",
        "--disable-dev-shm-usage", 
        "--disable-gpu",
        f"--window-size={window_size}"
    ]
    
    # Configurações de pastas (podem ser alteradas aqui)
    caminho_base_fundos = r"C:\bloko\Fundos - Documentos"         # Base dos fundos
    subfolder_carteiras = "06. Carteiras"                        # Subpasta de carteiras
    
    # Configurações de arquivos (podem ser alteradas aqui)
    extensoes_pdf = ".pdf"                                        # Extensão PDF
    extensoes_excel = ".xlsx"                                     # Extensão Excel
    prefixo_carteira_diaria = "Carteira Diária"                  # Nome padrão PDF
    prefixo_carteira_excel = "Carteira Excel"                    # Nome padrão Excel

    os.makedirs(SELENIUM_DOWNLOAD_TEMP_PATH, exist_ok=True)

    # Verifica argumentos da linha de comando
    if len(sys.argv) == 5:
        # Recebe os argumentos do VBA/chamada externa
        CAMINHO_PLANILHA_AUX_DOWNLOAD = sys.argv[1]  # Planilha Downloads
        CAMINHO_PLANILHA_AUX_BD = sys.argv[2]        # Planilha BD
        QORE_PDF_PATH_PARAM = sys.argv[3]            # Caminho PDF
        QORE_EXCEL_PATH_PARAM = sys.argv[4]          # Caminho Excel
        
        print(f"Argumentos recebidos:")
        print(f"1. Planilha Downloads: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
        print(f"2. Planilha BD: {CAMINHO_PLANILHA_AUX_BD}")
        print(f"3. Caminho PDF: {QORE_PDF_PATH_PARAM}")
        print(f"4. Caminho Excel: {QORE_EXCEL_PATH_PARAM}")
        
        # Usa os parâmetros da linha de comando
        QORE_PDF_PATH_DEFAULT = QORE_PDF_PATH_PARAM
        QORE_EXCEL_PATH_DEFAULT = QORE_EXCEL_PATH_PARAM
        
    elif len(sys.argv) == 2:
        # Apenas o caminho da planilha principal foi fornecido
        CAMINHO_PLANILHA_AUX_DOWNLOAD = sys.argv[1]
        print(f"Argumento recebido:")
        print(f"1. Planilha Downloads: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
        
        print(f"[INFO] Caminhos lidos da planilha:")
        print(f"       BD: {CAMINHO_PLANILHA_AUX_BD}")
        print(f"       PDF: {QORE_PDF_PATH_DEFAULT}")
        print(f"       Excel: {QORE_EXCEL_PATH_DEFAULT}")
        
    else:
        # Modo interativo (se executado diretamente) - já foi executado acima
        print(f"[INFO] Usando caminhos padrão:")
        print(f"       Downloads: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
    
    # Leitura da planilha principal (se ainda não foi lida)
    if 'df' not in locals():
        df = pd.read_excel(CAMINHO_PLANILHA_AUX_DOWNLOAD, sheet_name="Downloads", engine='openpyxl', header=None)

    # Se os caminhos ainda não foram definidos, lê da planilha
    if 'CAMINHO_PLANILHA_AUX_BD' not in locals():
        CAMINHO_PLANILHA_AUX_BD = str(df.iloc[18, 8]).strip()
    if 'QORE_PDF_PATH_DEFAULT' not in locals():
        QORE_PDF_PATH_DEFAULT = str(df.iloc[8, 8]).strip()
    if 'QORE_EXCEL_PATH_DEFAULT' not in locals():
        QORE_EXCEL_PATH_DEFAULT = str(df.iloc[12, 8]).strip()

    print(f"\n[INFO] Configurações finais:")
    print(f"       Planilha Downloads: {CAMINHO_PLANILHA_AUX_DOWNLOAD}")
    print(f"       Planilha BD: {CAMINHO_PLANILHA_AUX_BD}")
    print(f"       Caminho PDF: {QORE_PDF_PATH_DEFAULT}")
    print(f"       Caminho Excel: {QORE_EXCEL_PATH_DEFAULT}")
    print(f"       QORE Habilitado: {QORE_enabled}")

    # CHAMA A FUNÇÃO PRINCIPAL COM TODOS OS PARÂMETROS NECESSÁRIOS
    run_qore(
        CAMINHO_PLANILHA_AUX_BD, 
        QORE_PDF_PATH_DEFAULT, 
        QORE_EXCEL_PATH_DEFAULT, 
        CAMINHO_PLANILHA_AUX_DOWNLOAD, 
        link, 
        senha, 
        email, 
        df, 
        QORE_enabled, 
        PDF_enabled, 
        modo_lote_pdf, 
        Excel_enabled, 
        modo_lote_excel, 
        data_inicial_raw, 
        data_final_raw,
        SELENIUM_DOWNLOAD_TEMP_PATH
    )