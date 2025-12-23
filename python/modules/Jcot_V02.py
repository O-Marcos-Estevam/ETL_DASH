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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginForm")))
        driver.find_element(By.ID, "userItem").send_keys(username)
        driver.find_element(By.ID, "passItem").send_keys(password)
        driver.find_element(By.ID, "btlogin").click()

        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "ui-dialog-buttonset")))
        button.click()

        print("Login realizado com sucesso.")
        return True
    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def relatorio_cotista_posicao(driver):
    time.sleep(1)
   # Encontre todos os elementos que correspondem ao XPath
    elementos = driver.find_elements(By.XPATH, "//*[@id='menutree']//div[contains(@class, 'hitarea closed-hitarea expandable-hitarea')]")
    
    print(f"Total de elementos: {len(elementos)}")
    for i, el in enumerate(elementos):
        print(f"[{i}] HTML: {el.get_attribute('outerHTML')[:200]}...")
    time.sleep(0.4)
     #clica em relatorio
    elementos[9].click()
    time.sleep(0.4)
     #clica em cotista
    elementos[10].click()
    time.sleep(0.4)
    #clica em posição
    elementos[12].click()
    time.sleep(1)

def clicar_opcao_por_data(driver):
    try:
            # Localize e clique na opção "Por Data" dentro do submenu "Posição"
        print("Procurando e clicando na opção 'Por Data'...")
        opcao_por_data = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()='Por Data']"))
        )
        opcao_por_data.click()
        time.sleep(2)
        print("Opção 'Por Data' clicada com sucesso!")
    except Exception as e:
        print(f"Erro ao clicar na opção 'Por Data': {e}")

def clicar_opcao_por_periodo(driver, data_inicio, data_fim):

     # Localize e clique na opção "Por Período" dentro do submenu "Posição"
    print("Procurando e clicando na opção 'Por Período'...")
    opcao_por_data = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Por Período']")))
    opcao_por_data.click()
    time.sleep(2)
    print("Opção 'Por Período' clicada com sucesso!")

    # Localiza o campo de data pelo atributo 'name'
    campo_data_inicio = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "dt_posicao_inicio")))
    campo_data_fim = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "dt_posicao_fim")))

    # Garante que o campo está visível e editável
   # driver.execute_script("arguments[0].focus();", campo_data_inicio)

    # Limpa o campo de data
    campo_data_inicio.clear()
    campo_data_fim.clear()
    time.sleep(1)  # Pequeno delay para evitar problemas
    # Insere a nova data
    campo_data_inicio.send_keys(data_inicio)
    campo_data_fim.send_keys(data_fim)

    time.sleep(0.5)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tb-confirm"))).click() #confirma em cima da pagina
    time.sleep(1)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[span[text()='Sim']]"))).click() #clica ok para periodos longos
        time.sleep(1)
    except:    
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ccf_dwb_buscar"))).click() #setinhado para o lado
        time.sleep(1)
        elemento = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[id^="slickgrid_"][id$="_col28"]')))
        elemento.click() #selecoinada tds os fundos
        time.sleep(0.5)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tb-confirm"))).click() #confirma em cima da pagina
        time.sleep(0.5)
        #troca para XLSX
        campo = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "main_cd_tipo_fich_ac")))
        campo.click()
        actions = ActionChains(driver)
        actions.double_click(campo).perform()
        campo.clear()
        campo.send_keys(Keys.BACKSPACE * 10)
        campo.send_keys("Arquivo XLSX")
        time.sleep(0.5)

# CLICA NO OK
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "xpl6"))).click()
    time.sleep(10)
    print("Arquivo JCOT salvo com sucesso.")




def run_jcot (USERNAME_JCOT,PASSWORD_JCOT,jcot_path,url_jcot,data_inicio,data_fim):

    #Confiurar data inicio se for None pega 10 dias antes da data fim
    if not data_fim:  
        data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y")  # Converter para objeto datetime
        data_fim = data_inicio_dt.strftime("%d/%m/%Y") # Converter para objeto datetime
        data_inicio_dt = data_inicio_dt - timedelta(days=10) # Subtrair 10 dias
        data_inicio = data_inicio_dt.strftime("%d/%m/%Y") # Converter de volta para string

    clear_folder (jcot_path)

    # Configurar e inicializar o driver
    driver = setup_driver(jcot_path, url_jcot)

    if driver:
        try:
            # Realizar login
            if login(driver, USERNAME_JCOT, PASSWORD_JCOT):
                print("Pronto para realizar ações pós-login.")
            else:
                print("Falha ao realizar login. Verifique suas credenciais.")
          
            relatorio_cotista_posicao(driver)
            clicar_opcao_por_periodo(driver,data_inicio, data_fim)
            wait_for_downloads (jcot_path)
        finally:
            # Encerrar o driver
            driver.quit()
            print("Driver encerrado com sucesso.")
    else:
        print("Falha ao inicializar o driver. Verifique a configuração.")
