import os
import time
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from amplis_functions import clear_folder, wait_for_downloads 
import holidays


def setup_driver(download_path, url):
    """Configura o driver do Selenium com opções do Chrome."""
    try:
        chrome_options = Options()
        prefs = {
            "download.default_directory": os.path.abspath(download_path),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Inicializa o driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        print(f"Acessando {url}")
        return driver
    except Exception as e:
        print(f"Erro ao configurar o driver: {e}")
        return None

def login(driver, username, password):
    """Realiza login no sistema utilizando o Selenium."""
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "j_username")))
        driver.find_element(By.ID, "j_username").send_keys(username)
        driver.find_element(By.ID, "j_password").send_keys(password)
        botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]")))
        botao.click()

        print("Login realizado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def baixar_estoque(driver,initial_date,final_date,lista_fundos):
    #entrar na aba estoque
    botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/reports/estoque']")))
    botao.click()

    #selecionar data
    br_holidays = holidays.Brazil(state='SP')
    initial_date= datetime.strptime(initial_date, '%d/%m/%Y').date()
    final_date = datetime.strptime(final_date, '%d/%m/%Y').date()
    current_date= initial_date
    num_documentos = 0
    
    print(current_date, final_date)
    while current_date <= final_date:
        if current_date.weekday() < 5 and current_date.strftime('%Y-%m-%d') not in br_holidays:
            print(f"📅 Processando dia: {current_date.strftime('%d/%m/%Y')}")
            current_date_ajustado = current_date.strftime('%d/%m/%Y')

            
            
            # Loop para processar cada fundo na lista
            for fundo_nome in lista_fundos:
                print(f"➡️ Processando fundo: {fundo_nome}")

                # Preencher a data
                driver.find_element(By.ID, "data").clear()
                driver.find_element(By.ID, "data").send_keys(current_date_ajustado)
                time.sleep(1)

                # Selecionar fundo
                fundo = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fundoSelecionado_chzn")))
                fundo.click()
                time.sleep(1)

                fundo_search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chzn-search')]//input")))
                fundo_search.clear()
                fundo_search.send_keys(fundo_nome)
                time.sleep(5)

                elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(@id, 'fundoSelecionado_chzn_o_')]")))

                for element in elements:
                    if element.is_displayed():  # Verifica se o elemento está visível
                        element.click()
                        break  # Para após encontrar o primeiro disponível

                time.sleep(1)

                # Gerar documento
                gerar_documento = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "csv")))
                gerar_documento.click()
                time.sleep(1)

                num_documentos += 1
                print(f"✔️ Documento gerado para {fundo_nome} ({num_documentos} no total)")

        # Avança para o próximo dia útil
        current_date += timedelta(days=1)
   

def atualizar_relatorios(driver):
    while True:
        try:
            # Aguarda a tabela estar visível
            tabela = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "table-striped")))  # Lê o conteúdo da tabela
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            encontrou_palavra = False

            for linha in linhas:
                if "AGUARDANDO" in linha.text:
                    encontrou_palavra = True
                    break  # Se encontrar, não precisa continuar lendo a tabela

            # Se encontrou "AGUARDANDO", clica no botão refresh
            if encontrou_palavra:
                print("Encontrado 'AGUARDANDO', clicando no botão de refresh...")
                time.sleep(5)
                botao_refresh = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "refresh")))
                botao_refresh.click()

                # Aguarda a tabela atualizar
                WebDriverWait(driver, 10).until(EC.staleness_of(tabela))  # Espera a tabela antiga sumir
                print("Tabela atualizada, verificando novamente...")

            else:
                print("Nenhum 'AGUARDANDO' encontrado, encerrando.")
                break  # Sai do loop se não encontrar "AGUARDANDO"

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            break  # Encerra caso haja erro

def baixar_relatorios(driver):
    #entrar na aba meu estoque
    botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/reports/meusRelatorios']")))
    botao.click()
    time.sleep(1)

    atualizar_relatorios(driver)

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.NAME, "arquivo")))

    # Lista para armazenar os botões já clicados
    botoes_clicados = set()

    while True:
        # Captura todos os botões com name="arquivo"
        botoes = driver.find_elements(By.NAME, "arquivo")

        # Filtra apenas os botões que ainda não foram clicados
        botoes_nao_clicados = [botao for botao in botoes if botao not in botoes_clicados]

        if not botoes_nao_clicados:  # Se não houver botões novos, encerra o loop
            print("Todos os arquivos foram baixados! Encerrando...")
            break

        for botao in botoes_nao_clicados:
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(botao))
                botao.click()
                print("Arquivo baixado!")

                # Adiciona o botão à lista de botões já clicados
                botoes_clicados.add(botao)

                # Aguarda um pouco para garantir que o download iniciou
                time.sleep(1)

            except Exception as e:
                print(f"Erro ao clicar no botão: {e}")

                




def run_fidc_estoque (USERNAME_FIDC,PASSWORD_FIDC,FIDC_path,url_FIDC,initial_date,final_date,lista_fundos):
    if not final_date:
        final_date = initial_date
        
         # Configurar e inicializar o driver
    driver = setup_driver(FIDC_path, url_FIDC)

    if driver:
        try:
                # Realizar login
            if login(driver, USERNAME_FIDC, PASSWORD_FIDC):
                print("Pronto para realizar ações pós-login.")
            else:
                print("Falha ao realizar login. Verifique suas credenciais.")
            
            baixar_estoque(driver,initial_date, final_date, lista_fundos)
            baixar_relatorios(driver)
            wait_for_downloads (FIDC_path)
            time.sleep(4)
                
        finally:
            # Encerrar o driver
            driver.quit()
            print("Driver encerrado com sucesso.")
    else:
        print("Falha ao inicializar o driver. Verifique a configuração.")    
    