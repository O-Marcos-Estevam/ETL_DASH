import os
import json
import shutil
import time
from pathlib import Path
from tkinter import messagebox, Tk
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import holidays
from amplis_functions import wait_for_downloads, rename_file, setup_driver, login, insert_text_enter, click_button, clear_folder

def login(driver, username, password):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Login1_UserName")))
        time.sleep(0.5)
        driver.find_element(By.ID, "Login1_UserName").send_keys(username)
        driver.find_element(By.ID, "Login1_Password").send_keys(password)
        driver.find_element(By.ID, "Login1_LoginButton").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "gridQuery")))
        print("Login successful.")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def donwload_3meses(driver,download_path):

    time.sleep(5)
    insert_text_enter(driver, "gridQuery_DXFREditorcol2_I", "1")
    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn4")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "sc.xlsx")
    
    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn5")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "hc.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn6")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "pc.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn7")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "lh.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn8")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "pf.xlsx")

    print("Download da base dos ultimos 3 meses realizado.")


def donwload_total(driver,download_path):
    time.sleep(5)
    insert_text_enter(driver, "gridQuery_DXFREditorcol2_I", "1")
    time.sleep(0.5)

    click_button(driver, "gridQuery_DXCBtn0")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "sc.xlsx")
    
    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn1")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "hc.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn2")
    time.sleep(0.5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "pc.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn9")
    time.sleep(5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "pf.xlsx")

    time.sleep(0.5)
    click_button(driver, "gridQuery_DXCBtn3") 
    time.sleep(5)
    click_button(driver, "btnExportExcel")
    time.sleep(1)
    wait_for_downloads(download_path)
    rename_file(download_path, ".xlsx", "lh.xlsx")

    print("Download da base completa realizado.")



def run_britech(download_path,url_britech,username_britech,password_britech,base_total):
   
    clear_folder(download_path)
    driver = setup_driver(download_path, url_britech)
    login(driver, username_britech, password_britech)
    if base_total:
        donwload_total(driver,download_path)
        
    else:
        donwload_3meses(driver,download_path)

