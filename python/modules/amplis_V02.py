from amplis_functions import (
    setup_driver,
    login,
    click_button,
    get_previous_working_day_sp,
    set_date,
    select_all_funds,
    click_ok_button,
    clear_folder,
    wait_for_downloads,
    set_output_type_to_csv,
    rename_file
)
from selenium.webdriver.common.by import By
import os
import time
from tkinter import messagebox
import glob
from tkinter import Tk
import shutil
from save_pdfs import save_pdfs
import holidays
from datetime import datetime
from datetime import timedelta



def run_reag_process_csv(custom_inical_date=None, custom_final_date=None, USERNAME_REAG=None,PASSWORD_REAG=None, url_reag=None ,csv_path =None):
    """Runs the download process for REAG CSV."""
    driver = setup_driver(csv_path, url_reag)
    try:
        if login(driver, USERNAME_REAG, PASSWORD_REAG):
            d_minus_inical = custom_inical_date if custom_inical_date else get_previous_working_day_sp()
            d_minus_final = custom_final_date if custom_inical_date else get_previous_working_day_sp()

            # BAIXA CARTEIRA DIARIA CSV
            time.sleep(0.7)
         
            click_button(driver, "mainForm:listaDeFavoritosRelatorios:0:j_id_9m")      
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateBegin:campoInputDate", d_minus_inical) # data inical
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateEnd:campoInputDate", d_minus_final)  #data final
            time.sleep(3)
            select_all_funds(driver)
            time.sleep(5)
            # Set output type to CSV and download
            set_output_type_to_csv(driver, "mainForm:saida:campo")
            time.sleep(0.5)
            click_ok_button(driver)
            
            time.sleep(1)
           
            wait_for_downloads(csv_path) # Aguardar o download 

            # BAIXA COTAS E PATRIMONIO CSV
            click_button(driver, "mainForm:listaDeFavoritosRelatorios:2:j_id_9m")
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateBegin:campoInputDate", d_minus_inical) # data inical
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateEnd:campoInputDate", d_minus_final)  #data final
            time.sleep(0.7)
            select_all_funds(driver)
            time.sleep(0.5)
            set_output_type_to_csv(driver, "mainForm:reportExtension:campo")
            time.sleep(0.5)
            click_ok_button(driver)
            time.sleep(1)
           
            wait_for_downloads(csv_path) # Aguardar o download 
            rename_file(csv_path, ".csv", "cp1.csv")  # Renomeia o arquivo para "cp1.csv"
            time.sleep(0.5)
               
         
            # BAIXA APLICACAO E RESGATE (CSV)
            click_button(driver, "mainForm:listaDeFavoritosRelatorios:1:j_id_9m")
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateBegin:campoInputDate", d_minus_inical) # data inical
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateEnd:campoInputDate", d_minus_final)  #data final
            time.sleep(0.7)
            select_all_funds(driver)
            time.sleep(0.5)
            set_output_type_to_csv(driver, "mainForm:reportExtension:campo")
            time.sleep(0.5)
            click_ok_button(driver)
            time.sleep(1)
           
            wait_for_downloads(csv_path) # Aguardar o download 
           
            # PODE NAO HAVER ARQUIVO PARA BAIXAR
            try:
                driver.find_element(By.ID, "detailMessageListBoxId")
                print("No data available for AR report generation.")
            except:
                rename_file(csv_path, ".csv", "ar.csv") 

      
    finally:
        driver.quit()

def run_master_process_csv(custom_inical_date=None, custom_final_date=None, USERNAME_MASTER=None,PASSWORD_MASTER=None, url_master=None ,csv_path=None):
    """Runs the download process for REAG CSV."""
    driver = setup_driver(csv_path, url_master)
    try:
        if login(driver, USERNAME_MASTER, PASSWORD_MASTER):
            d_minus_inical = custom_inical_date if custom_inical_date else get_previous_working_day_sp()
            d_minus_final = custom_final_date if custom_inical_date else get_previous_working_day_sp()

            # BAIXA CARTEIRA DIARIA CSV

            click_button(driver, "mainForm:listaDeFavoritosRelatorios:0:j_id_9m")        
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateBegin:campoInputDate", d_minus_inical) # data inical
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateEnd:campoInputDate", d_minus_final)  #data final
            time.sleep(3)
            select_all_funds(driver)
            time.sleep(5)
            # Set output type to CSV and download
            set_output_type_to_csv(driver, "mainForm:saida:campo")
            time.sleep(0.5)
            click_ok_button(driver)
            
            time.sleep(1)
           
            wait_for_downloads(csv_path) # Aguardar o download 

            # BAIXA COTAS E PATRIMONIO CSV
            click_button(driver, "mainForm:listaDeFavoritosRelatorios:1:j_id_9m")
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateBegin:campoInputDate", d_minus_inical) # data inical
            time.sleep(0.7)
            set_date(driver, "mainForm:calendarDateEnd:campoInputDate", d_minus_final)  #data final
            time.sleep(0.7)
            select_all_funds(driver)
            time.sleep(0.5)
            set_output_type_to_csv(driver, "mainForm:reportExtension:campo")
            time.sleep(0.5)
            click_ok_button(driver)
            time.sleep(1)
           
            wait_for_downloads(csv_path) # Aguardar o download 
            rename_file(csv_path, ".csv", "cp2.csv")  # Renomeia o arquivo para "cp1.csv"
            time.sleep(0.5)
               
    finally:
        driver.quit()
def run_reag_process_pdf(custom_inical_date=None, custom_final_date=None, USERNAME_REAG=None,PASSWORD_REAG=None, url_reag=None ,pdf_path=None):
    """Runs the download process for REAG PDF."""
    driver = setup_driver(pdf_path, url_reag)
    try:
        if login(driver, USERNAME_REAG, PASSWORD_REAG):
                        
            d_minus_inical = custom_inical_date if custom_inical_date else get_previous_working_day_sp()
            d_minus_final = custom_final_date if custom_final_date else get_previous_working_day_sp()
            print(f"Datas a serem processadas: De {d_minus_inical} até {d_minus_final}")
            
            br_holidays = holidays.Brazil()
            start_date_format = datetime.strptime(d_minus_inical, '%d/%m/%Y').date()
            end_date_format = datetime.strptime(d_minus_final, '%d/%m/%Y').date()

            current_date = start_date_format
            while current_date <= end_date_format:
                if current_date.weekday() < 5 and current_date not in br_holidays:
                    print(f"Processando dia: {current_date}")
                    try:
                        click_button(driver, "mainForm:listaDeFavoritosRelatorios:0:j_id_9m")  
                        time.sleep(0.7)
                        set_date(driver, "mainForm:calendarDateBegin:campoInputDate", current_date.strftime('%d/%m/%Y'))
                        print(f"Data definida no campo: {current_date.strftime('%d/%m/%Y')}")
                        time.sleep(3)
                        select_all_funds(driver)
                        time.sleep(3)
                        click_ok_button(driver)
                        time.sleep(4)
                        wait_for_downloads(pdf_path)
                        print(f"Download concluído para {current_date}")

                        # Fechar abas extras
                        main_window = driver.window_handles[0]
                        for handle in driver.window_handles[1:]:
                            driver.switch_to.window(handle)
                            driver.close()
                        driver.switch_to.window(main_window)

                    except Exception as e:
                        print(f"Erro ao processar {current_date}: {e}")
                else:
                    print(f"Dia {current_date} não é dia útil ou é feriado.")

                current_date += timedelta(days=1)

            print("Processamento completo. Todos os dias foram processados com sucesso!")
    finally:
        driver.quit()
def run_master_process_pdf(custom_inical_date=None, custom_final_date=None, USERNAME_MASTER=None,PASSWORD_MASTER=None, url_master=None ,pdf_path=None):
    """Runs the download process for REAG PDF."""
    driver = setup_driver(pdf_path, url_master)
    try:
        if login(driver, USERNAME_MASTER, PASSWORD_MASTER):
                        
            d_minus_inical = custom_inical_date if custom_inical_date else get_previous_working_day_sp()
            d_minus_final = custom_final_date if custom_final_date else get_previous_working_day_sp()
            print(f"Datas a serem processadas: De {d_minus_inical} até {d_minus_final}")
            
            br_holidays = holidays.Brazil()
            start_date_format = datetime.strptime(d_minus_inical, '%d/%m/%Y').date()
            end_date_format = datetime.strptime(d_minus_final, '%d/%m/%Y').date()

            current_date = start_date_format
            while current_date <= end_date_format:
                if current_date.weekday() < 5 and current_date not in br_holidays:
                    print(f"Processando dia: {current_date}")
                    try:
                        click_button(driver, "mainForm:listaDeFavoritosRelatorios:0:j_id_9m")  
                        time.sleep(0.7)
                        set_date(driver, "mainForm:calendarDateBegin:campoInputDate", current_date.strftime('%d/%m/%Y'))
                        print(f"Data definida no campo: {current_date.strftime('%d/%m/%Y')}")
                        time.sleep(3)
                        select_all_funds(driver)
                        time.sleep(5)
                        click_ok_button(driver)
                        time.sleep(4)
                        wait_for_downloads(pdf_path)
                        print(f"Download concluído para {current_date}")

                        # Fechar abas extras
                        main_window = driver.window_handles[0]
                        for handle in driver.window_handles[1:]:
                            driver.switch_to.window(handle)
                            driver.close()
                        driver.switch_to.window(main_window)

                    except Exception as e:
                        print(f"Erro ao processar {current_date}: {e}")
                else:
                    print(f"Dia {current_date} não é dia útil ou é feriado.")

                current_date += timedelta(days=1)

            print("Processamento completo. Todos os dias foram processados com sucesso!")
    finally:
        driver.quit()




def run_amplis(USERNAME_REAG,PASSWORD_REAG, url_reag , USERNAME_MASTER, PASSWORD_MASTER, url_master, csv_path, pdf_path, initial_date,final_date,pdf, csv):

    

    if not final_date:
        final_date = initial_date


    if csv :
        #clear_folder(csv_path)
        run_reag_process_csv(custom_inical_date=initial_date, custom_final_date=final_date,USERNAME_REAG= USERNAME_REAG,PASSWORD_REAG=PASSWORD_REAG, url_reag=url_reag ,csv_path=csv_path)
        run_master_process_csv(custom_inical_date=initial_date, custom_final_date=final_date, USERNAME_MASTER=USERNAME_MASTER,PASSWORD_MASTER=PASSWORD_MASTER, url_master=url_master ,csv_path=csv_path)
    
    if pdf :
       # clear_folder(pdf_path)
        run_reag_process_pdf(custom_inical_date=initial_date, custom_final_date=final_date, USERNAME_REAG= USERNAME_REAG,PASSWORD_REAG=PASSWORD_REAG, url_reag=url_reag ,pdf_path=pdf_path)
        run_master_process_pdf(custom_inical_date=initial_date, custom_final_date=final_date,  USERNAME_MASTER=USERNAME_MASTER,PASSWORD_MASTER=PASSWORD_MASTER, url_master=url_master ,pdf_path=pdf_path)
