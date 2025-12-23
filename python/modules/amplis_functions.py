
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

# Function to set up the driver with Chrome options
def setup_driver(download_path, url):
    chrome_options = Options()
    prefs = {
        "download.default_directory": os.path.abspath(download_path),  # Set default download directory
        "download.prompt_for_download": False,  # Disable download prompts
        "plugins.always_open_pdf_externally": True,  # Open PDFs directly without Chrome PDF Viewer
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1  # Allow all downloads
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    return driver

# Function to log in
def login(driver, username, password):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginForm:userLoginInput:campo")))
        driver.find_element(By.ID, "loginForm:userLoginInput:campo").send_keys(username)
        driver.find_element(By.ID, "loginForm:userPasswordInput").send_keys(password)
        driver.find_element(By.ID, "loginForm:botaoOk").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mainForm_menu1_label")))
        print("Login successful.")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def safe_click(driver, element_locator):
    for attempt in range(3):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element_locator))
            element.click()
            print(f"Successfully clicked on element with locator: {element_locator}")
            return True
        except StaleElementReferenceException:
            print(f"Stale element reference when clicking - retrying ({attempt + 1}/3)")
    return False

# Function to click on a specific link by ID
def click_button(driver, element_id):
    try:
        link = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("arguments[0].click();", link)
        print(f"Successfully clicked on element with ID: {element_id}")
    except Exception as e:
        print(f"Failed to click on element with ID {element_id}: {e}")

# Function to set the date in the calendar input
def set_date(driver, element_id, date_value):
    try:
        date_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("arguments[0].value = arguments[1];", date_input, date_value)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", date_input)
        print(f"Date set to: {date_value}")
    except Exception as e:
        print(f"Failed to set date: {e}")

# Function to select all funds
def select_all_funds(driver):
    select_all_locator = (By.ID, "mainForm:portfolioPickList:includeAll")
    if not safe_click(driver, select_all_locator):
        print("Failed to click 'Select All Funds' button after multiple attempts.")
    else:
        for attempt in range(3):
            try:
                selected_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mainForm:portfolioPickList:secondSelect"))
                )
                options_in_selected_box = selected_box.find_elements(By.TAG_NAME, "option")
                if len(options_in_selected_box) > 0:
                    print("Funds successfully selected.")
                    break
                else:
                    print(f"No funds selected, retrying selection... ({attempt + 1}/3)")
                    safe_click(driver, select_all_locator)
            except StaleElementReferenceException:
                print(f"Stale element reference when verifying funds - retrying ({attempt + 1}/3)")

# Function to click the "Ok" button
def click_ok_button(driver):
    try:
        ok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "mainForm:confirmButton"))
        )
        driver.execute_script("arguments[0].click();", ok_button)
        print("Successfully clicked 'Ok' button.")
    except Exception as e:
        print(f"Failed to click 'Ok' button: {e}")

# Function to get D-2 (closest working day, skipping weekends and holidays)
def get_previous_working_day_sp(days_before=2):
    # Set up holidays for São Paulo
    br_holidays = holidays.Brazil(state='SP')
    
    current_date = date.today()
    delta_days = days_before

    while delta_days > 0:
        current_date -= timedelta(days=1)
        # Skip weekends (Saturday=5, Sunday=6) and holidays
        if current_date.weekday() < 5 and current_date not in br_holidays:
            delta_days -= 1

    return current_date.strftime("%d/%m/%Y")  # Return date in format "DD/MM/YYYY"

# Function to clear folder
def clear_folder(folder_path):
    try:
        folder = Path(folder_path)
        parent_folder = folder.resolve().parent.name
        folder_name = folder.name

        if folder.exists():
            num_files = len(os.listdir(folder_path))
            if num_files > 0:
                # Create a simple UI with yes/no prompt
                root = Tk()
                root.withdraw()  # Hide the main window
                confirm = messagebox.askyesno("Clear folder", f"There are {num_files} files in {parent_folder}/{folder_name}. Do you want to delete them?")
                if confirm:
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    print(f"Cleared folder: {parent_folder}/{folder_name}")
                else:
                    print("Folder not cleared. Exiting script.")
                    exit()
            else: 
                print(f"Folder is empty: {parent_folder}/{folder_name}")
    except Exception as e:
        print(f"Failed to clear folder {parent_folder}/{folder_name}: {e}")

# Function to wait for all downloads to complete
def wait_for_downloads(download_path):
    download_wait_time = 3  # Initial wait time
    while any([filename.endswith(".crdownload") for filename in os.listdir(download_path)]):
        print(f"Waiting for downloads to complete... {download_wait_time}s")
        time.sleep(download_wait_time)
    print("Download completed.")

# Function to change the output type to CSV
def set_output_type_to_csv(driver, element_id):
    try:
        # Locate the select element by its ID
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        # Create a Select instance and choose the CSV option by value
        select = Select(select_element)
        select.select_by_value("3")
        print("Output type set to CSV.")
    except Exception as e:
        print(f"Failed to set output type to CSV: {e}")

import glob

def rename_file(download_path, file_extension, new_name):
    try:
        # Assuming the CSV file extension is '.csv', find all CSV files in the download folder
        files = glob.glob(os.path.join(download_path, f"*{file_extension}"))
        if files:
            # Assuming the most recent CSV file is the one we just downloaded
            file = max(files, key=os.path.getctime)
            new_file_path = os.path.join(download_path, new_name)
            os.rename(file, new_file_path)
            print(f"File renamed to: {new_name}")
        else:
            print("No files found to rename.")
    except Exception as e:
        print(f"Failed to rename file: {e}")

# Nova função para fechar abas about:blank
def close_blank_tabs(driver):
    try:
        main_window = driver.current_window_handle
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if driver.current_url == "about:blank":
                driver.close()
        driver.switch_to.window(main_window)
        print("Abas 'about:blank' fechadas com sucesso.")
    except Exception as e:
        print(f"Erro ao fechar abas 'about:blank': {e}")

def insert_text_enter(driver, element_id, text):
    driver.find_element(By.ID, element_id).send_keys(text)
    driver.find_element(By.ID, element_id).send_keys(Keys.RETURN)