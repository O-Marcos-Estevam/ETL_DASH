import os
import pandas as pd



def identificar_excels(caminho_da_pasta):

    print(f"Buscando arquivos Excel com 'COMPOSIÇÃO' ou 'POSIÇÃO' na pasta: {caminho_da_pasta}\n")
    arquivos_identificados_composicao = []
    arquivos_identificados_posicao = []

    if not os.path.isdir(caminho_da_pasta):
        print(f"Erro: O caminho '{caminho_da_pasta}' não é um diretório válido ou não existe.")
        return arquivos_identificados_composicao, arquivos_identificados_posicao # Retorna lista vazia em caso de erro

    try:
        arquivos_na_pasta = os.listdir(caminho_da_pasta)
    except OSError as e:
        print(f"Erro ao listar arquivos na pasta '{caminho_da_pasta}': {e}")
        return arquivos_identificados_composicao # Retorna lista vazia em caso de erro

    for nome_arquivo in arquivos_na_pasta:
        caminho_completo_arquivo = os.path.join(caminho_da_pasta, nome_arquivo)
        # Verifica se é um arquivo, se termina com .xlsx ou .xls e se 'composição' está no nome
        if os.path.isfile(caminho_completo_arquivo) and nome_arquivo.lower().endswith(('.xlsx', '.xls')) and "composicao" in nome_arquivo.lower():
            arquivos_identificados_composicao.append(caminho_completo_arquivo)
        elif os.path.isfile(caminho_completo_arquivo) and nome_arquivo.lower().endswith(('.xlsx', '.xls')) and "posicao" in nome_arquivo.lower():
            arquivos_identificados_posicao.append(caminho_completo_arquivo)

    if arquivos_identificados_composicao:
        print(f"Arquivos COMPOSIÇÃO identificados ({len(arquivos_identificados_composicao)}):")
        for arq in arquivos_identificados_composicao:
            print(f"- {os.path.basename(arq)}") # Imprime apenas o nome do arquivo
        print("-" * 30)
    else:
        print(f"Nenhum arquivo Excel com 'COMPOSIÇÃO'  encontrado na pasta '{caminho_da_pasta}'.")


    if arquivos_identificados_posicao:
        print(f"Arquivos POSIÇÃO identificados ({len(arquivos_identificados_posicao)}):")
        for arq in arquivos_identificados_posicao:
            print(f"- {os.path.basename(arq)}") # Imprime apenas o nome do arquivo
        print("-" * 30)
    else:
        print(f"Nenhum arquivo Excel com  'POSIÇÃO' encontrado na pasta '{caminho_da_pasta}'.")

    return arquivos_identificados_composicao, arquivos_identificados_posicao


def ler_e_imprimir_conteudo_excels(lista_caminhos_excel):

    if not lista_caminhos_excel:
        print("Nenhum arquivo Excel para ler e imprimir.")
        return

    print("Iniciando a leitura e impressão dos arquivos Excel identificados:\n")

    for caminho_completo_arquivo in lista_caminhos_excel:
        nome_arquivo = os.path.basename(caminho_completo_arquivo)
        print(f"--- Conteúdo do arquivo: {nome_arquivo} ---")

        try:
            # Lê o arquivo Excel (por padrão, a primeira planilha)
            df = pd.read_excel(caminho_completo_arquivo)
            # Imprime o conteúdo do DataFrame
            #print(df)
            salvar_subset_excel_ativo(df, nome_arquivo)

        except FileNotFoundError:
             # Esta exceção não deve ocorrer se a função anterior funcionou,
            print(f"Erro: Arquivo não encontrado durante a leitura - {nome_arquivo}")
        except pd.errors.ParserError as e:
            print(f"Erro de análise ao ler o arquivo {nome_arquivo}: {e}")
        except Exception as e:
            # Captura outros possíveis erros (ex: arquivo corrompido)
            print(f"Ocorreu um erro ao ler o arquivo {nome_arquivo}: {e}")

        print("\n" + "=" * (len(nome_arquivo) + 23) + "\n") # Separador maior entre arquivos

def salvar_subset_excel_ativo(df, nome_arquivo_original):

    # Define o caminho da pasta de destino fixa
    caminho_pasta_destino = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\06. AUXILIAR_MAPS'

    print(f"Preparando para salvar subset do arquivo: {nome_arquivo_original}")
    print(f"Pasta de destino: {caminho_pasta_destino}")

    cotas_e_patrimonio(df, nome_arquivo_original,caminho_pasta_destino)

    start_index_rv, end_index_rv = None, None
    start_index_rf, end_index_rf = None, None
    start_index_caixa, end_index_caixa = None, None
    start_index_areceber, end_index_areceber = None, None
    start_index_apagar, end_index_apagar = None, None
    start_index_rentab, end_index_rentab = None, None # Para Rentabilidade (%)
    start_index_fundo, end_index_fundo = None, None
    start_index_cotista, end_index_cotista = None, None
    start_index_outrosativos, end_index_outrosativos = None, None

 

    for num_linha, primeira_coluna_valor in enumerate(df.iloc[:, 0]):

        # Adicionar a verificação para garantir que o valor é uma string
        if isinstance(primeira_coluna_valor, str):
            # Converter para minúsculas APENAS se for uma string
            primeira_coluna_valor_lower = primeira_coluna_valor.lower()

            # --- Lógica para encontrar Início e Fim de CADA Seção ---

            # RENDA VARIAVEL
            # Procura o início da seção RV apenas se ainda não encontrou
            if start_index_rv is None and "renda variável | ações" in primeira_coluna_valor_lower:   
                start_index_rv = num_linha # Índice do DataFrame
                print(f"Início da seção 'Renda Variável' encontrado no índice do DataFrame: {start_index_rv} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' para RV apenas se encontrou o início mas não o fim
            # Adicionado check para garantir que o 'total' vem DEPOIS do início
            if start_index_rv is not None and end_index_rv is None and "total".lower() in primeira_coluna_valor.lower() and "subtotal".lower() not in primeira_coluna_valor.lower():
                 if start_index_rv < num_linha:
                    end_index_rv = num_linha # Índice do DataFrame
                    print(f"Fim da seção 'Renda Variável' (Total) encontrado no índice do DataFrame: {end_index_rv} (Linha Excel: {num_linha + 2})")


            # RENDA FIXA
            # Procura o início da seção RV apenas se ainda não encontrou
            if start_index_rf is None and "renda fixa" in primeira_coluna_valor_lower:   
                start_index_rf = num_linha # Índice do DataFrame
                print(f"Início da seção 'Renda Fixa' encontrado no índice do DataFrame: {start_index_rf} (Linha Excel: {num_linha + 2})")
            # Adicionado check para garantir que o 'total' vem DEPOIS do início
            if start_index_rf is not None and end_index_rf is None and "total".lower() in primeira_coluna_valor.lower() and "subtotal".lower() not in primeira_coluna_valor.lower():
                 if start_index_rf < num_linha:
                    end_index_rf = num_linha # Índice do DataFrame
                    print(f"Fim da seção 'Renda Fixa' (Total) encontrado no índice do DataFrame: {end_index_rf} (Linha Excel: {num_linha + 2})")
            
            # Cotas de Fundos
            if start_index_fundo is None and "cotas de fundos" in primeira_coluna_valor_lower:
                start_index_fundo = num_linha
                print(f"Início da seção 'Cotas de Fundos' encontrado no índice do DataFrame: {start_index_fundo} (Linha Excel: {num_linha + 2})")
            # Adicionado check para garantir que o 'total' vem DEPOIS do início
            if start_index_fundo is not None and end_index_fundo is None and "total" in primeira_coluna_valor_lower:
                 if start_index_fundo < num_linha:
                    end_index_fundo = num_linha
                    print(f"Fim da seção 'Fundo' (Total) encontrado no índice do DataFrame: {end_index_fundo} (Linha Excel: {num_linha + 2})")

            # Outros ativos
            if start_index_outrosativos is None and "outros |" in primeira_coluna_valor_lower:
                start_index_outrosativos = num_linha
                print(f"Início da seção 'Outros Ativos' encontrado no índice do DataFrame: {start_index_outrosativos} (Linha Excel: {num_linha + 2})")
            # Adicionado check para garantir que o 'total' vem DEPOIS do início
            if start_index_outrosativos is not None and end_index_outrosativos is None and "total" in primeira_coluna_valor_lower:
                 if start_index_outrosativos < num_linha:
                    end_index_outrosativos = num_linha
                    print(f"Fim da seção 'Outros Ativos' (Total) encontrado no índice do DataFrame: {end_index_outrosativos} (Linha Excel: {num_linha + 2})")


            # CAIXA
            # Procura o início da seção Caixa apenas se ainda não encontrou
            if start_index_caixa is None and "caixa" in primeira_coluna_valor_lower:
                start_index_caixa = num_linha
                print(f"Início da seção 'Caixa' encontrado no índice do DataFrame: {start_index_caixa} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' para Caixa apenas se encontrou o início mas não o fim
            # Adicionado check para garantir que o 'total' vem DEPOIS do início
            if start_index_caixa is not None and end_index_caixa is None and "total" in primeira_coluna_valor_lower:
                 if start_index_caixa < num_linha:
                    end_index_caixa = num_linha
                    print(f"Fim da seção 'Caixa' (Total) encontrado no índice do DataFrame: {end_index_caixa} (Linha Excel: {num_linha + 2})")

            # VALORES A RECEBER
            # Procura o início apenas se ainda não encontrou
            if start_index_areceber is None and "valores a receber" in primeira_coluna_valor_lower:
                start_index_areceber = num_linha
                print(f"Início da seção 'Valores a Receber' encontrado no índice do DataFrame: {start_index_areceber} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' apenas se encontrou o início mas não o fim
            if start_index_areceber is not None and end_index_areceber is None  and "total".lower() in primeira_coluna_valor.lower() and "subtotal".lower() not in primeira_coluna_valor.lower():
                 if start_index_areceber < num_linha:
                    end_index_areceber = num_linha
                    print(f"Fim da seção 'Valores a Receber' (Total) encontrado no índice do DataFrame: {end_index_areceber} (Linha Excel: {num_linha + 2})")

            # VALORES A PAGAR
            # Procura o início apenas se ainda não encontrou
            if start_index_apagar is None and "valores a pagar" in primeira_coluna_valor_lower:
                start_index_apagar = num_linha
                print(f"Início da seção 'Valores a Pagar' encontrado no índice do DataFrame: {start_index_apagar} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' apenas se encontrou o início mas não o fim
            if start_index_apagar is not None and end_index_apagar is None  and "total".lower() in primeira_coluna_valor.lower() and "subtotal".lower() not in primeira_coluna_valor.lower():
                 if start_index_apagar < num_linha:
                    end_index_apagar = num_linha
                    print(f"Fim da seção 'Valores a Pagar' (Total) encontrado no índice do DataFrame: {end_index_apagar} (Linha Excel: {num_linha + 2})")

            # RENTABILIDADE (%)
            # Atenção: A seção Rentabilidade (%) PODE NÃO ter uma linha "Total" associada
            # Se o arquivo sempre tiver "Total" depois, essa lógica funcionará.
            # Se for apenas uma única linha, o end_index_rentab nunca será definido por "total".
            if start_index_rentab is None and "rentabilidade (%)" in primeira_coluna_valor_lower:
                start_index_rentab = num_linha
                print(f"Início da seção 'Rentabilidade (%)' encontrado no índice do DataFrame: {start_index_rentab} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' apenas se encontrou o início mas não o fim
            if start_index_rentab is not None and end_index_rentab is None and "variação" in primeira_coluna_valor_lower:
                 if start_index_rentab < num_linha:
                    end_index_rentab = num_linha
                    print(f"Fim da seção 'Rentabilidade (%)' (Variação) encontrado no índice do DataFrame: {end_index_rentab} (Linha Excel: {num_linha + 2})")
            
            
            # investidor
            # Procura o início apenas se ainda não encontrou
            if start_index_cotista is None and "investidor" in primeira_coluna_valor_lower:
                start_index_cotista = num_linha
                print(f"Início da seção 'Investidor' encontrado no índice do DataFrame: {start_index_cotista} (Linha Excel: {num_linha + 2})")
            # Procura o 'total' apenas se encontrou o início mas não o fim
            if start_index_cotista is not None and end_index_cotista is None  and "total".lower() in primeira_coluna_valor.lower() and "subtotal".lower() not in primeira_coluna_valor.lower():
                 if start_index_cotista < num_linha:
                    end_index_cotista = num_linha
                    print(f"Fim da seção 'Investidor' (Total) encontrado no índice do DataFrame: {end_index_cotista} (Linha Excel: {num_linha + 2})")

        # Se o valor na primeira coluna NÃO for uma string, ignora esta linha
        else:
             # Opcional: printar algo para depuração se quiser ver quais linhas são ignoradas
             # print(f"Ignorando linha {num_linha + 2} para busca de texto (valor: {primeira_coluna_valor}, tipo: {type(primeira_coluna_valor)})")
             pass # Não faz nada, apenas continua para a próxima linha

    print("Busca por seções concluída.")

    # --- Chamar a função carteira_ativos para CADA seção que teve Início e Fim encontrados ---

    # Renda Variável
    if start_index_rv is not None and end_index_rv is not None:
        print(f"Processando seção 'Renda Variável' de {start_index_rv} a {end_index_rv}")
        # Assumindo que 'carteira_ativos' sabe como lidar com cada 'parte'
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_rv, end_index_rv, "renda variável | ações")
    else:
        print("Início ou fim da seção 'renda variável | ações' não encontrados.") # Feedback importante para depuração

        # Renda Fixa
    if start_index_rf is not None and end_index_rf is not None:
        print(f"Processando seção 'Renda Fixa' de {start_index_rf} a {end_index_rf}")
        # Assumindo que 'carteira_ativos' sabe como lidar com cada 'parte'
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_rf, end_index_rf, "renda fixa")
    else:
        print("Início ou fim da seção 'renda variável | ações' não encontrados.") # Feedback importante para depuração

    # Cotas Fundos
    if start_index_fundo is not None and end_index_fundo is not None:
        print(f"Processando seção 'Cotas Fundos' de {start_index_fundo} a {end_index_fundo}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_fundo, end_index_fundo, "Cotas Fundos")
    else:
        print("Início ou fim da seção 'Cotas Fundos' não encontrados.") # Feedback importante para depuração

    # Outros Ativos
    if start_index_outrosativos is not None and end_index_outrosativos is not None:
        print(f"Processando seção 'Outros Ativos' de {start_index_outrosativos} a {end_index_outrosativos}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_outrosativos, end_index_outrosativos, "Outros Ativos")
    else:
        print("Início ou fim da seção 'Outros Ativos' não encontrados.") # Feedback importante para depuração

    # Caixa
    if start_index_caixa is not None and end_index_caixa is not None:
        print(f"Processando seção 'Caixa' de {start_index_caixa} a {end_index_caixa}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_caixa, end_index_caixa, "caixa")
    else:
        print("Início ou fim da seção 'caixa' não encontrados.") # Feedback importante para depuração

    # Valores a Receber
    if start_index_areceber is not None and end_index_areceber is not None:
        print(f"Processando seção 'Valores a Receber' de {start_index_areceber} a {end_index_areceber}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_areceber, end_index_areceber, "Valores a receber")
    else:
        print("Início ou fim da seção 'Valores a receber' não encontrados.") # Feedback importante para depuração

    # Valores a Pagar
    if start_index_apagar is not None and end_index_apagar is not None:
        print(f"Processando seção 'Valores a Pagar' de {start_index_apagar} a {end_index_apagar}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_apagar, end_index_apagar, "Valores a pagar")
    else:
        print("Início ou fim da seção 'Valores a pagar' não encontrados.") # Feedback importante para depuração

    # Rentabilidade (%)
    # Como Rentabilidade (%) pode não ter um 'Total' no arquivo, este bloco
    # só será executado se um 'Total' for encontrado após "Rentabilidade (%)".
    # Se for apenas uma linha, você precisaria de uma lógica diferente para processá-la,
    # talvez apenas usando o start_index_rentab se ele for encontrado.
    if start_index_rentab is not None and end_index_rentab is not None:
        print(f"Processando seção 'Rentabilidade (%)' de {start_index_rentab} a {end_index_rentab}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_rentab, end_index_rentab, "Rentabilidade (%)")
    else:
         # Adicione um print específico, pois a falta do 'Total' é comum aqui
        if start_index_rentab is not None and end_index_rentab is None:
             print(f"Início da seção 'Rentabilidade (%)' encontrado em {start_index_rentab}, mas a linha 'Total' não foi encontrada para delimitar o fim.")
             # Se Rentabilidade é só uma linha, talvez você queira processá-la aqui
             # Ex: processar_rentabilidade(df, nome_arquivo_original, caminho_pasta_destino, start_index_rentab)
        else:
            print("Início ou fim da seção 'Rentabilidade (%)' não encontrados.")

        # Investidor
    if start_index_cotista is not None and end_index_cotista is not None:
        print(f"Processando seção 'Investidor' de {start_index_cotista} a {end_index_cotista}")
        carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_index_cotista, end_index_cotista, "passivo")
    else:
        print("Início ou fim da seção 'Investidor' não encontrados.") # Feedback importante para depuração

def cotas_e_patrimonio(df, nome_arquivo_original,caminho_pasta_destino):   
    try:
        os.makedirs(caminho_pasta_destino, exist_ok=True)
        print("Pasta de destino verificada/criada com sucesso.")
    except OSError as e:
        print(f"Erro ao criar ou acessar a pasta de destino '{caminho_pasta_destino}': {e}")
        return False # Retorna False se não conseguir garantir a pasta

    #COTAS E PATRIMONIO
    # Seleciona as primeiras 22 linhas (índice 0 a 21)
    # Se o DataFrame tiver menos de 22 linhas, iloc[:22] pegará todas as linhas disponíveis.
    df_subset = df.iloc[:22].copy() 

    # Verifica se é realmente um arquivo de Cotas/Patrimônio procurando por palavras-chave
    # Converte o subset para string (tudo minúsculo) para facilitar a busca
    conteudo_subset = df_subset.to_string().lower()
    palavras_chave = ['patrimônio', 'pl posição', 'pl posicão', 'pl posicao', 'pl contábil']
    
    # Se NENHUMA das palavras-chave for encontrada, não salva
    encontradas = [k for k in palavras_chave if k in conteudo_subset]
    if not encontradas:
        print(f"⚠️ AVISO: Arquivo '{nome_arquivo_original}' IGNORADO para Cotas&Patrimonio.")
        return False
    else:
        print(f"   [DEBUG] Arquivo aceito! Palavras encontradas: {encontradas}")

    # Cria o nome do novo arquivo com o sufixo "_Cotas&Patrimonio"
    nome_base, extensao = os.path.splitext(nome_arquivo_original)
    # Adiciona o sufixo antes da extensão
    nome_arquivo_novo = f"{nome_base}_Cotas&Patrimonio{extensao}"
    caminho_completo_novo = os.path.join(caminho_pasta_destino, nome_arquivo_novo)

    try:
        df_subset.to_excel(caminho_completo_novo, index=False)

        print(f"✓ Arquivo Cotas e Patrimonio salvo com sucesso: '{nome_arquivo_novo}'")
        return True
    except Exception as e:
        print(f"Erro ao salvar o arquivo '{nome_arquivo_novo}': {e}")
        return False # Retorna False em caso de erro ao salvar
    
def carteira_ativos(df, nome_arquivo_original, caminho_pasta_destino, start_df_index, end_df_index,parte):

    try:
        # Garante que a pasta de destino existe. Cria se não existir.
        os.makedirs(caminho_pasta_destino, exist_ok=True)
        # print("Pasta de destino verificada/criada com sucesso.") # Removido

        # iloc[start_df_index : end_df_index + 1] inclui a linha start e a linha end
        df_subset = df.iloc[start_df_index : end_df_index + 1].copy()
        parte_ajustado =  (parte[:parte.find('|')].strip() if parte and '|' in parte else parte.strip()).replace(' ', '_')
        # Cria o nome do novo arquivo com o sufixo "_Valora"
        nome_base, extensao = os.path.splitext(nome_arquivo_original)
        nome_arquivo_novo = f"{nome_base}_{parte_ajustado}{extensao}"
        caminho_completo_novo = os.path.join(caminho_pasta_destino, nome_arquivo_novo)

        df_subset.to_excel(caminho_completo_novo, index=False)

        print(f"✓ Arquivo '{parte}' salvo com sucesso: '{nome_arquivo_novo}'")
        return True
    except OSError as e:
         print(f"Erro ao criar ou acessar a pasta de destino '{caminho_pasta_destino}': {e}")
         return False
    except Exception as e:
        print(f"Erro ao salvar o arquivo '{nome_arquivo_novo}': {e}")
        return False
    
# --- Parte Principal ---
if __name__ == "__main__":
    # Define o caminho da sua pasta
    # Usando r'' para garantir que as barras invertidas sejam tratadas corretamente
    caminho_da_sua_pasta = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\04. EXCEL_MAPS'

    # 1. Chama a primeira função para identificar os arquivos
    arquivos_composicao = identificar_excels(caminho_da_sua_pasta)[0]
    arquivos_posicao = identificar_excels(caminho_da_sua_pasta)[1]

    # 2. Chama a segunda função para ler e imprimir o conteúdo dos arquivos encontrados
    if arquivos_composicao: # Verifica se a lista não está vazia antes de chamar a segunda função
        ler_e_imprimir_conteudo_excels(arquivos_composicao)
    else:
        print("Nenhum arquivo 'Composição' para ler e imprimir com base na identificação.")
        
    if arquivos_posicao:
         ler_e_imprimir_conteudo_excels(arquivos_posicao)
    else:
        print("Nenhum arquivo 'Posição' para ler e imprimir com base na identificação.")
