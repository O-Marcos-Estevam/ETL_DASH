import os
import time
import traceback
import logging
import tkinter as tk
from tkinter import simpledialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import shutil
from datetime import datetime, timedelta
from selenium.webdriver.common.keys import Keys

TEMP_EXTENSIONS = [".crdownload", ".part", ".tmp"]

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


def gera_datas_uteis(data_inicio, data_fim):
    datas = []
    dt = datetime.strptime(data_inicio, "%d/%m/%Y")
    dt_fim = datetime.strptime(data_fim, "%d/%m/%Y")

    if dt == dt_fim:
        datas.append(dt.strftime("%d/%m/%Y"))

    else:
        while dt <= dt_fim:
            if dt.weekday() < 5:  # segunda a sexta (0=seg, ..., 4=sex)
                datas.append(dt.strftime("%d/%m/%Y"))
            dt += timedelta(days=1)

    return datas

def setup_driver(download_path, url):
    os.makedirs(download_path, exist_ok=True)
    chrome_options = Options()
    prefs = {
        "download.default_directory": os.path.abspath(download_path),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True, # Para PDFs abrirem direto sem preview no Chrome
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1 # Para múltiplos downloads
    }
    chrome_options.add_experimental_option("prefs", prefs)
    # chrome_options.add_argument("--headless") # Descomente para rodar sem abrir a janela do Chrome (modo invisível)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    logging.info(f"Navegador aberto com pasta de download: {download_path}")
    return driver

def login(driver, username, password):
    try:
        wait = WebDriverWait(driver, 10)
        botao = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "#card-maps-pegasus")]')))
        botao.click()
        time.sleep(1) # Pequena pausa após o clique
        
        botao_gestores = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/pegasusgestores"]')))
        botao_gestores.click()

        # Espera pela página de login
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "login-pf-page")))
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "kc-form-buttons").click()
        
        # Espera pela página de autenticação de 2 fatores ou pela página pós-login
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "kc-content")), # Se for direto para a página principal
                EC.presence_of_element_located((By.ID, "kc-login")) # Se for para a página de OTP
            )
        )

        # Autenticação em dois fatores (janela popup)
        try:
            # Verifica se o campo OTP está presente
            otp_field = driver.find_element(By.ID, "otp")
            root = tk.Tk()
            root.withdraw() # Esconde a janela principal do Tkinter
            codigo = simpledialog.askstring("Entrada de Código", "Digite o código do Authenticator:")
            otp_field.send_keys(codigo)
            driver.find_element(By.ID, "kc-login").click()
            logging.info("Código OTP inserido e enviado.")
        except:
            logging.info("Campo OTP não encontrado, assumindo que não é necessário 2FA ou já foi passado.")
        
        logging.info("Login realizado com sucesso.")
        time.sleep(2) # Pequena pausa para a página carregar após o login final
        return True
    except Exception:
        logging.error("Falha no login:")
        traceback.print_exc() # Imprime o erro completo para depuração
        return False

def wait_for_downloads(download_path, timeout=120):
    download_wait_time = 5
    waited = 0
    logging.info("Verificando downloads pendentes...")
    def still_downloading():
        for filename in os.listdir(download_path):
            # Verifica se há arquivos temporários de download
            if any(filename.endswith(ext) for ext in TEMP_EXTENSIONS):
                return True
        return False
    
    # Loop enquanto houver arquivos temporários
    while still_downloading():
        if waited >= timeout:
            logging.warning("Tempo máximo de espera para download atingido.")
            break
        logging.info(f"Aguardando finalização do download... {download_wait_time}s restantes para timeout ({timeout - waited}s).")
        time.sleep(download_wait_time)
        waited += download_wait_time

    logging.info("Todos os downloads concluídos.")


def exportar_ativos(driver, lista_datas, lista_fundos, baixar_pdf, baixar_xlsx, download_path, pdf_path, maps_path):
    wait = WebDriverWait(driver, 15) # Aumentei o tempo de espera geral para elementos

    for data in lista_datas:
        try:
            logging.info(f"Iniciando processamento para data: {data}")

            # --- Navegação/Reset para cada nova data ---
            # O objetivo é garantir que a página esteja no estado correto para cada iteração
            try:
                # Tenta clicar no botão toggle (se estiver visível, pode ser um menu lateral)
                toggle_button = driver.find_element(By.CSS_SELECTOR, ".toggle.pull-right.hidden-xl.visible-lg")
                if toggle_button.is_displayed():
                    toggle_button.click()
                    logging.info("Botão toggle clicado (para reset da interface).")
            except Exception:
                logging.info("Botão toggle não encontrado ou não visível (ignorando).")
            
            # Tenta clicar no botão "stop-redirect" (assumindo que leva para a tela principal de módulos/relatórios)
            try:
                botoes_stop_redirect = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "stop-redirect")))
                if botoes_stop_redirect:
                    botoes_stop_redirect[0].click()
                    logging.info("Botão 'stop-redirect' clicado.")
                    time.sleep(3) # Pausa para a página carregar após o clique
                else:
                    logging.warning("Botão 'stop-redirect' não encontrado. Pode indicar problema na navegação inicial.")
            except Exception as e:
                logging.error(f"Erro ao clicar em 'stop-redirect': {e}")
                traceback.print_exc()

            # Clica no primeiro item do submenu (assumindo que é o relatório/funcionalidade desejada)
            try:
                primeiro_li = wait.until(EC.element_to_be_clickable((By.XPATH, "(//div[@class='sub-menu']//div[@class='sub-menu-container']//ul[@class='unstyled']/li)[1]")))
                primeiro_li.click()
                logging.info("Primeiro item do submenu clicado.")
                time.sleep(2) # **PAUSA MAIOR AQUI:** Crucial para a página carregar todos os elementos após a navegação
            except Exception as e:
                logging.error(f"Erro ao clicar no primeiro item do submenu: {e}")
                traceback.print_exc()
                raise 


            # --- Fim da Navegação/Reset ---

            for fundo in lista_fundos:
                logging.info(f"Processando: {fundo} - {data}")
                try:
                    # Tenta clicar no seletor de fundos
                    select2_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "select2-choice")))
                    select2_button.click()
                    time.sleep(1) # Pequena pausa para o campo de busca abrir
                    
                    # Envia o nome do fundo e seleciona
                    select2_button.send_keys(fundo)
                    select2_button.send_keys(Keys.TAB) 
                    time.sleep(2) # Pausa para os resultados da busca aparecerem
                    
                    # Clica no item correspondente ao fundo
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "select2-match"))).click()
                    time.sleep(2)

                    # --- INTERAÇÃO COM O CAMPO DE DATA ---                
                    input_field = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "date")))
                    
                    # Limpeza robusta
                    input_field.send_keys(Keys.CONTROL + "a")
                    input_field.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Preenchimento com verificação
                    for char in data:
                        input_field.send_keys(char)
                        time.sleep(0.1)
                    
                    # Validação
                    atual = input_field.get_attribute("value")
                    if atual != data:
                        logging.warning(f"Valor inconsistente. Corrigindo...")
                        driver.execute_script(f"arguments[0].value = '{data}';", input_field)
                    
                    # Dispara eventos JS
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", input_field)
                    input_field.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    
                    logging.info(f"Campo de data preenchido com sucesso: {data}")
                

                    # Clica no botão Pesquisar
                    driver.find_element(By.XPATH, "//input[@value='Pesquisar']").click()
                    logging.info("Botão 'Pesquisar' clicado.")
                    time.sleep(3) # Pausa para a pesquisa carregar os resultados

                    # Clica no botão Exportar
                    botao_exportar = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Exportar')]")))
                    botao_exportar.click()
                    logging.info("Botão 'Exportar' clicado.")
                    time.sleep(0.5)

                    # PDF
                    if baixar_pdf:
                        botao_pdf = driver.find_element(By.XPATH, '//img[@title="PDF"]/parent::a')
                        botao_pdf.click()
                        logging.info(f"Solicitado download PDF: {fundo} - {data}")
                        time.sleep(1.5)
                    
                    # XLSX
                    if baixar_xlsx:
                        try:
                            # Espera e clica no botão XLSX
                            botao_xlsx = wait.until(EC.element_to_be_clickable((By.XPATH, '//img[@title="XLSX"]/parent::a')))
                            botao_xlsx.click()
                            logging.info(f"Solicitado download XLSX: {fundo} - {data}")
                            time.sleep(1.5)
                        except Exception:
                            logging.warning("Clique normal no botão XLSX falhou, tentando clique por JavaScript.")
                            try:
                                # Tenta clicar via JavaScript como fallback
                                botao_xlsx_js = driver.find_element(By.XPATH, '//img[@title="XLSX"]/parent::a')
                                driver.execute_script("arguments[0].click();", botao_xlsx_js)
                                logging.info(f"Solicitado download XLSX via JS: {fundo} - {data}")
                                time.sleep(1.5)
                            except Exception as e:
                                logging.error(f"Não foi possível clicar no botão XLSX para {fundo}: {e}")
                                traceback.print_exc()
                                # Não usa 'continue' aqui para não pular o fundo inteiro, mas falha o download XLSX

                except Exception as e:
                    logging.warning(f"Erro ao processar fundo {fundo} na data {data}: {e}")
                    traceback.print_exc() # Imprime o erro completo para depuração
                    continue  # Pula para o próximo fundo, mas continua na mesma data

        except Exception as e:
            logging.warning(f"Erro CRÍTICO ao processar a data {data}. Pulando para a próxima data. Erro: {e}")
            traceback.print_exc() # Imprime o erro completo para depuração
            continue # Pula para a próxima data se ocorrer um erro crítico nesta

        # Ao terminar todos os fundos de uma data: aguarda e redistribui arquivos
        if download_path and pdf_path and maps_path:
            wait_for_downloads(download_path)
            redistribuir_arquivos(download_path, pdf_path, maps_path)

def exportar_passivos(driver, lista_datas, lista_fundos, baixar_pdf, baixar_xlsx, download_path, pdf_path, maps_path):
    wait = WebDriverWait(driver, 15) 

    for data in lista_datas:
        try:
            logging.info(f"Iniciando processamento para data: {data}")

            # --- Navegação/Reset para cada nova data ---
            # O objetivo é garantir que a página esteja no estado correto para cada iteração
            try:
                # Tenta clicar no botão toggle (se estiver visível, pode ser um menu lateral)
                toggle_button = driver.find_element(By.CSS_SELECTOR, ".toggle.pull-right.hidden-xl.visible-lg")
                if toggle_button.is_displayed():
                    toggle_button.click()
                    logging.info("Botão toggle clicado (para reset da interface).")
            except Exception:
                logging.info("Botão toggle não encontrado ou não visível (ignorando).")
            
            # Tenta clicar no botão "stop-redirect" (assumindo que leva para a tela principal de módulos/relatórios)
            try:
                botoes_stop_redirect = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "stop-redirect")))
                if botoes_stop_redirect:
                    botoes_stop_redirect[1].click()
                    logging.info("Botão 'stop-redirect' clicado.")
                    time.sleep(3) # Pausa para a página carregar após o clique
                else:
                    logging.warning("Botão 'stop-redirect' não encontrado. Pode indicar problema na navegação inicial.")
            except Exception as e:
                logging.error(f"Erro ao clicar em 'stop-redirect': {e}")
                traceback.print_exc()

            # Clica no primeiro item do submenu (assumindo que é o relatório/funcionalidade desejada)
            try:
                botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Posição por Fundo']")))
                botao.click()
                time.sleep(2) # **PAUSA MAIOR AQUI:** Crucial para a página carregar todos os elementos após a navegação
            except Exception as e:
                logging.error(f"Erro ao clicar no terceiro item do submenu: {e}")
                traceback.print_exc()
                raise 


            # --- Fim da Navegação/Reset ---

            for fundo in lista_fundos:
                logging.info(f"Processando: {fundo} - {data}")
                try:
                    # Tenta clicar no seletor de fundos
                    select2_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "select2-choice")))
                    select2_button.click()
                    time.sleep(1) # Pequena pausa para o campo de busca abrir
                    
                    # Envia o nome do fundo e seleciona
                    select2_button.send_keys(fundo)
                    select2_button.send_keys(Keys.TAB) 
                    time.sleep(2) # Pausa para os resultados da busca aparecerem
                    
                    # Clica no item correspondente ao fundo
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "select2-match"))).click()
                    time.sleep(0.5)

                    # --- INTERAÇÃO COM O CAMPO DE DATA ---                
                           
                    input_field = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "date")))
                    
                    # Limpeza robusta
                    input_field.send_keys(Keys.CONTROL + "a")
                    input_field.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Preenchimento com verificação
                    for char in data:
                        input_field.send_keys(char)
                        time.sleep(0.1)
                    
                    # Validação
                    atual = input_field.get_attribute("value")
                    if atual != data:
                        logging.warning(f"Valor inconsistente. Corrigindo...")
                        driver.execute_script(f"arguments[0].value = '{data}';", input_field)
                    
                    # Dispara eventos JS
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", input_field)
                    input_field.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    
                    logging.info(f"Campo de data preenchido com sucesso: {data}")

                    # Clica no botão Pesquisar
                    driver.find_element(By.XPATH, "//input[@value='Pesquisar']").click()
                    logging.info("Botão 'Pesquisar' clicado.")
                    time.sleep(3) # Pausa para a pesquisa carregar os resultados

                    # Clica no botão Exportar
                    botao_exportar = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Exportar')]")))
                    botao_exportar.click()
                    logging.info("Botão 'Exportar' clicado.")
                    time.sleep(0.5)

                    # PDF
                    if baixar_pdf:
                        botao_pdf = driver.find_element(By.XPATH, '//img[@title="PDF"]/parent::a')
                        botao_pdf.click()
                        logging.info(f"Solicitado download PDF: {fundo} - {data}")
                        time.sleep(1.5)
                    
                    # XLSX
                    if baixar_xlsx:
                        try:
                            # Espera e clica no botão XLSX
                            botao_xlsx = wait.until(EC.element_to_be_clickable((By.XPATH, '//img[@title="XLSX"]/parent::a')))
                            botao_xlsx.click()
                            logging.info(f"Solicitado download XLSX: {fundo} - {data}")
                            time.sleep(1.5)
                        except Exception:
                            logging.warning("Clique normal no botão XLSX falhou, tentando clique por JavaScript.")
                            try:
                                # Tenta clicar via JavaScript como fallback
                                botao_xlsx_js = driver.find_element(By.XPATH, '//img[@title="XLSX"]/parent::a')
                                driver.execute_script("arguments[0].click();", botao_xlsx_js)
                                logging.info(f"Solicitado download XLSX via JS: {fundo} - {data}")
                                time.sleep(1.5)
                            except Exception as e:
                                logging.error(f"Não foi possível clicar no botão XLSX para {fundo}: {e}")
                                traceback.print_exc()
                                # Não usa 'continue' aqui para não pular o fundo inteiro, mas falha o download XLSX

                except Exception as e:
                    logging.warning(f"Erro ao processar fundo {fundo} na data {data}: {e}")
                    traceback.print_exc() # Imprime o erro completo para depuração
                    continue  # Pula para o próximo fundo, mas continua na mesma data

        except Exception as e:
            logging.warning(f"Erro CRÍTICO ao processar a data {data}. Pulando para a próxima data. Erro: {e}")
            traceback.print_exc() # Imprime o erro completo para depuração
            continue # Pula para a próxima data se ocorrer um erro crítico nesta

        # Ao terminar todos os fundos de uma data: aguarda e redistribui arquivos
        if download_path and pdf_path and maps_path:
            wait_for_downloads(download_path)
            redistribuir_arquivos(download_path, pdf_path, maps_path)

def redistribuir_arquivos(download_path, pdf_path, maps_path):
    arquivos = os.listdir(download_path)
    count_pdf, count_xlsx = 0, 0
    for arquivo in arquivos:
        arquivo_lower = arquivo.lower()
        origem = os.path.join(download_path, arquivo)
        if arquivo_lower.endswith(".pdf"):
            destino = os.path.join(pdf_path, arquivo)
            try:
                shutil.move(origem, destino)
                count_pdf += 1
            except shutil.Error as e:
                logging.error(f"Erro ao mover PDF '{arquivo}': {e}. Pode ser que o arquivo já exista ou esteja em uso.")
        elif arquivo_lower.endswith(".xlsx"):
            destino = os.path.join(maps_path, arquivo)
            try:
                shutil.move(origem, destino)
                count_xlsx += 1
            except shutil.Error as e:
                logging.error(f"Erro ao mover XLSX '{arquivo}': {e}. Pode ser que o arquivo já exista ou esteja em uso.")
    logging.info(f"Arquivos redistribuídos! PDFs: {count_pdf} | XLSX: {count_xlsx}")

if __name__ == "__main__":
    url_maps = "https://reag-gestores.cloud.maps.com.br/"
    download_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina"
    pdf_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\05. PDF"
    maps_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\04. EXCEL_MAPS"
    
    # Garante que as pastas de destino existam
    os.makedirs(pdf_path, exist_ok=True)
    os.makedirs(maps_path, exist_ok=True)
    
    username_maps = "camila.renda@nscapital.com.br"
    password_maps = "2025@Maps"

    data_inicio = "02/06/2025" # Exemplo: comece na segunda-feira
    data_fim = "17/06/2025"   # Exemplo: termine na sexta-feira ou sábado para pegar sexta útil
    
    baixar_xlsx=True
    baixar_pdf=True
    ativo = False
    passivo = True

    lista_datas = gera_datas_uteis(data_inicio, data_fim)
    
    lista_fundos = [ "FIP MULTIESTRATÉGIA TURANO", 
                     "FIP MULTIESTRATÉGIA BENELLI",
                     "FIP MULTIESTRATÉGIA GEKKO",
                     "FIP MULTIESTRATÉGIA RAM", 
                     "FIP MULTIESTRATÉGIA HURACAN", 
                     "FIP MULTIESTRATÉGIA MURCIELAGO", 
                     "FIP MULTIESTRATÉGIA AMG", 
                     "FIP MULTIESTRATÉGIA OSLO", 
                     "FIP MULTIESTRATÉGIA ESTOCOLMO", 
                     "FIP MULTIESTRATÉGIA URUS"]
    

    driver = setup_driver(download_path, url_maps)
    if login(driver, username_maps, password_maps):
        if ativo:
            exportar_ativos(
                driver, 
                lista_datas, 
                lista_fundos, 
                baixar_pdf, 
                baixar_xlsx, 
                download_path=download_path, 
                pdf_path=pdf_path, 
                maps_path=maps_path
            )
        if passivo:    
            exportar_passivos(
                    driver, 
                    lista_datas, 
                    lista_fundos, 
                    baixar_pdf, 
                    baixar_xlsx, 
                    download_path=download_path, 
                    pdf_path=pdf_path, 
                    maps_path=maps_path
                )
    driver.quit()
    logging.info("Processo concluído para todos os dias do período.")
