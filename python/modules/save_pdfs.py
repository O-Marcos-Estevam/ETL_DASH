
import os
import fitz
import logging
import pandas as pd 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mapping of month numbers to their Portuguese names
MONTHS_PT = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",\
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro"
}


def load_de_para_mapping(excel_path):
    """Load the DE-PARA mapping from the Excel file."""
    try:
        # Read the Excel sheet starting from row 3
        df = pd.read_excel(excel_path, sheet_name='De Para', header=None, skiprows=2)
        
        # Extract columns B and C, which are index 1 and 2
        de_para_mapping = dict(zip(df[1], df[2]))
        
        logging.info(f"Loaded DE-PARA mapping from {excel_path}")
        return de_para_mapping
    except Exception as e:
        logging.error(f"Error reading DE-PARA mapping: {e}")
        return {}


def extract_date_from_pdf(pdf_path, is_aplicacao_resgate=False):
    """Extract the date from the PDF file."""
    
    try:
        document = fitz.open(pdf_path)
        logging.info(f"Opened PDF: {pdf_path}")
        
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text = page.get_text()
            
            logging.debug(f"Text of page {page_num + 1}:\n{text}\n{'-'*40}")
            
            if is_aplicacao_resgate:
                start_index = text.find("Período")
                if start_index != -1:
                    subsequent_text = text[start_index + len("Período"):].strip()
                    date_part = subsequent_text.split('a')[0].strip()
                    logging.info(f"Found date for Aplicação e Resgate: {date_part}")
                    return date_part
            else:
                start_index = text.find("Data:")
                if start_index != -1:
                    subsequent_text = text[start_index + len("Data:"):].strip()
                    date_line = subsequent_text.split('\n')[0].strip()
                    date_str = date_line.split()[0].strip()
                    logging.info(f"Found date: {date_str}")
                    return date_str
            
        document.close()
        
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
    return None


def extract_carteira_from_pdf(pdf_path, is_aplicacao_resgate=False):
    """Extract the 'Carteira' name from the PDF file."""
    
    try:
        document = fitz.open(pdf_path)
        logging.info(f"Opened PDF: {pdf_path}")
        
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text = page.get_text()
            
            logging.debug(f"Text of page {page_num + 1}:\n{text}\n{'-'*40}")
            
            if is_aplicacao_resgate:
                start_index = text.find("Carteira")
                if start_index != -1:
                    subsequent_text = text[start_index + len("Carteira"):].strip()
                    carteira_name = subsequent_text.split('\n')[0].strip()
                    logging.info(f"Found Carteira for Aplicação e Resgate: {carteira_name}")
                    return carteira_name
            else:
                start_index = text.find("Carteira:")
                if start_index != -1:
                    subsequent_text = text[start_index + len("Carteira:"):].strip()
                    carteira_name = subsequent_text.split('\n')[0].strip()
                    carteira_name = carteira_name.split('-')[0].strip()
                    logging.info(f"Found Carteira: {carteira_name}")
                    return carteira_name
            
        document.close()
        
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
    return None


def is_aplicacao_resgate_pdf(pdf_path):
    """Check if the PDF is a 'Aplicação e Resgate' type based on its content."""
    try:
        document = fitz.open(pdf_path)
        logging.info(f"Opened PDF: {pdf_path}")
        
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text = page.get_text()
            
            if "Relatório de Aplicação e Resgate Analítico" in text:
                logging.info("Detected Aplicação e Resgate report.")
                return True
        
        document.close()
        
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
    
    return False


def get_unique_filename(filepath):
    """Generate a unique filename by adding a numerical suffix if the file already exists."""
    base, extension = os.path.splitext(filepath)
    counter = 1
    
    # Loop until a unique filename is found
    while os.path.exists(filepath):
        filepath = f"{base} ({counter}){extension}"
        counter += 1
    
    return filepath

def rename_pdf_files(folder_path, de_para_mapping):
    """Rename PDF files in the specified folder based on extracted dates and Carteira names and move them to specific folders."""
    
    logging.info(f"Scanning folder: {folder_path}")
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            logging.info(f"Processing file: {pdf_path}")
            
            is_aplicacao_resgate = is_aplicacao_resgate_pdf(pdf_path)
            date_str = extract_date_from_pdf(pdf_path, is_aplicacao_resgate)
            carteira_name = extract_carteira_from_pdf(pdf_path, is_aplicacao_resgate)
            
            if date_str and carteira_name:
                try:
                    day, month, year = date_str.split('/')
                    
                    if is_aplicacao_resgate:
                        new_filename = f"{day}.{month} - Aplicação e Resgate - {carteira_name}.pdf"
                    else:
                        new_filename = f"{day}.{month} - Carteira Diária - {carteira_name}.pdf"
                    
                    base_folder_name = de_para_mapping.get(carteira_name, None)
                    
                    if base_folder_name:
                        base_path = os.path.join(r"C:\bloko\Fundos - Documentos", base_folder_name, "06. Carteiras", year)
                        month_folder_name = f"{month} - {MONTHS_PT[month]}"
                        month_folder = os.path.join(base_path, month_folder_name)
                        
                        os.makedirs(month_folder, exist_ok=True)
                        new_pdf_path = os.path.join(month_folder, new_filename)
                        
                        # Check if the file already exists, and get a unique filename if needed
                        if os.path.exists(new_pdf_path):
                            logging.info(f"A file with the name '{new_filename}' already exists. Generating a unique filename.")
                            new_pdf_path = get_unique_filename(new_pdf_path)
                        
                        # Rename and move the file
                        os.rename(pdf_path, new_pdf_path)
                        logging.info(f"Renamed and moved '{filename}' to '{new_pdf_path}'")
                    else:
                        logging.warning(f"No mapping found for Carteira '{carteira_name}'")
                    
                except Exception as e:
                    logging.error(f"Error renaming {pdf_path}: {e}")
            else:
                logging.warning(f"No date or Carteira found in {pdf_path}")

def save_pdfs():
    excel_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\07. DEPARA\DE PARA.xlsx"
    de_para_mapping = load_de_para_mapping(excel_path)
    folder_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\05. PDF"
    rename_pdf_files(folder_path, de_para_mapping)

if __name__ == "__main__":
    save_pdfs()