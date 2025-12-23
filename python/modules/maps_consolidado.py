
from maps_downloads import setup_driver, login, exportar_ativos, exportar_passivos, gera_datas_uteis
from maps_save_excel_folders import identificar_excels, ler_e_imprimir_conteudo_excels, salvar_subset_excel_ativo, cotas_e_patrimonio, carteira_ativos
from maps_upload_access import process_all_files_in_folder

url_maps = "https://reag-gestores.cloud.maps.com.br/"
download_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina"
pdf_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\05. PDF"
maps_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\04. EXCEL_MAPS"
db_path = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\teste.accdb'
folder_path = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\06. AUXILIAR_MAPS'
depara_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\07. DEPARA\DE PARA.xlsx" 

username_maps = "camila.renda@nscapital.com.br"
password_maps = "2025@Maps"

data_inicio = "17/06/2025" # Exemplo: comece na segunda-feira
data_fim = "17/06/2025"   # Exemplo: termine na sexta-feira ou sábado para pegar sexta útil
    
baixar_xlsx=True
baixar_pdf=True
ativo = False
passivo = True

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

    # Configurações (substitua com seus caminhos reais)
    
    

def run_maps_completo (url_maps, download_path, pdf_path, maps_path, username_maps, password_maps, data_inicio, data_fim, baixar_xlsx, baixar_pdf, ativo, passivo, lista_fundos, db_path, folder_path, depara_path):

    lista_datas = gera_datas_uteis(data_inicio, data_fim)

    driver = setup_driver(download_path, url_maps)
    if login(driver, username_maps, password_maps):
        if ativo:
            exportar_ativos(driver, lista_datas, lista_fundos, baixar_pdf, baixar_xlsx, download_path=download_path, pdf_path=pdf_path, maps_path=maps_path)
        if passivo:    
            exportar_passivos(driver, lista_datas, lista_fundos, baixar_pdf, baixar_xlsx, download_path=download_path, pdf_path=pdf_path, maps_path=maps_path)
    driver.quit()
    print ("Download MAPS concluído para todos os dias do período.")
    
    print('Organizando arquivos baixados nas suas respctivas pastas')    

    # 1. Chama a primeira função para identificar os arquivos
    arquivos_composicao = identificar_excels(maps_path)[0]
    arquivos_posicao = identificar_excels(maps_path)[1]

    # 2. Chama a segunda função para ler e imprimir o conteúdo dos arquivos encontrados
    if arquivos_composicao: # Verifica se a lista não está vazia antes de chamar a segunda função
        ler_e_imprimir_conteudo_excels(arquivos_composicao)
    else:
        print("Nenhum arquivo 'Composição' para ler e imprimir com base na identificação.")
        
    if arquivos_posicao:
         ler_e_imprimir_conteudo_excels(arquivos_posicao)
    else:
        print("Nenhum arquivo 'Posição' para ler e imprimir com base na identificação.")

    print('Arquivos realocados nas suas respctivas pastas')  

    print('Iniciando Upload dos arquivos no access')  

    # Processa todos os arquivos da pasta
    process_all_files_in_folder(db_path, folder_path, depara_path)    
    print('Upload Completo')  

if __name__ == "__main__":
    run_maps_completo (url_maps, download_path, pdf_path, maps_path, username_maps, password_maps, data_inicio, data_fim, baixar_xlsx, baixar_pdf, ativo, passivo, lista_fundos, db_path, folder_path, depara_path)