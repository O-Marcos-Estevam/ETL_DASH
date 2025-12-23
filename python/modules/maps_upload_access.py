import pyodbc
import pandas as pd
import os
import re # Para extrair informações do nome do arquivo
from datetime import datetime, date
import sys

# --- Função para conectar ao banco de dados Access ---
def connect_to_access(db_path):
    """Tenta conectar ao banco de dados Access."""
    try:
        # String de conexão para arquivos .accdb usando o driver Microsoft Access Driver
        # Pode precisar ajustar o nome do DRIVER dependendo da sua instalação do Office/Access Database Engine
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            r'DBQ=' + db_path + ';'
        )
        conn = pyodbc.connect(conn_str)
        print(f"Conexão com Access estabelecida: {db_path}")
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Erro ao conectar ao Access. SQLSTATE: {sqlstate}")
        if sqlstate == 'IM002':
            print("Verifique se o driver ODBC 'Microsoft Access Driver (*.mdb, *.accdb)' está instalado e se a arquitetura (32/64 bits) corresponde à do Python.")
        else:
             print(f"Detalhes do erro: {ex.args[1]}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao conectar ao Access: {e}")
        return None

# --- Função para extrair informações (Data e Nome do Fundo) do nome do arquivo ---
def extract_info_from_filename(file_path, depara_path=None):
    """Extrai data, nome do fundo e tabela do depara (usando correspondência exata na coluna D)."""
    try:
        filename = os.path.basename(file_path)
        
        # Extrai informações do nome do arquivo
        match = re.search(
            r'([^_]+)_(.+?)_(\d{2}-\d{2}-\d{4})_([^\.]+)\.xlsx$',
            filename, re.IGNORECASE
        )
        if not match:
            print("Aviso: Formato do nome do arquivo inválido.")
            return None

        raw_fund_name = match.group(2)
        date_str = match.group(3)
        tablename = match.group(4)  # Ex: "Valores_a_receber"
        print(f"Tablename extraído: {tablename}")

        # Formata nome do fundo (remove "MULTIESTRATÉGIA" e underscores)
        fund_name = raw_fund_name.replace("MULTIESTRATÉGIA", "").replace("_", " ").replace("  ", " ").strip()
        
        # Formata data
        try:
            process_date = datetime.strptime(date_str, '%d-%m-%Y').date()
        except ValueError:
            print(f"Erro: Data inválida '{date_str}'")
            return None

        # Busca no depara (correspondência EXATA na coluna D)
        table_name = None
        if depara_path and os.path.exists(depara_path):
            try:
                df = pd.read_excel(depara_path, sheet_name='MAPS')
                # Procura o tablename EXTRAÍDO (ex: "Valores_a_receber") na coluna D (case-insensitive)
                match = df[df.iloc[:, 3].str.strip().str.lower() == tablename.lower()]
                if not match.empty:
                    table_name = match.iloc[0, 1]  # Pega o valor da coluna B
            except Exception as e:
                print(f"Erro ao ler depara: {str(e)[:100]}")

        print(f"Resultado: Data={process_date}, Fundo='{fund_name}', Tabela='{table_name}'")
        return [process_date, fund_name, table_name]
        
    except Exception as e:
        print(f"Erro crítico: {e}")
        return None

def get_primary_keys(cursor, table_name, depara_path):
    """Obtém as chaves primárias, tratando '0.1' como [0, 1]."""
    try:
        # 1. Carrega o mapeamento
        df = pd.read_excel(depara_path, sheet_name="MAPS")
        table_row = df[df.iloc[:, 1].str.strip().str.lower() == table_name.lower()]
        
        if table_row.empty:
            print(f"[AVISO] Tabela '{table_name}' não encontrada")
            return []

        # 2. Extrai e processa as posições (tratando "0.1" como [0, 1])
        pk_value = str(table_row.iloc[0, 2]).strip()
        print(f"Valor bruto da coluna PK: '{pk_value}'")

        if '.' in pk_value and not any(c.isalpha() for c in pk_value):
            # Caso especial: "0.1" -> [0, 1]
            col_positions = [int(pos) for pos in pk_value.split('.') if pos.isdigit()]
        elif ',' in pk_value:
            # Formato tradicional: "0,1" -> [0, 1]
            col_positions = [int(pos) for pos in pk_value.split(',') if pos.strip().isdigit()]
        elif pk_value.isdigit():
            # Única posição: "1" -> [1]
            col_positions = [int(pk_value)]
        else:
            print(f"[AVISO] Formato inválido: '{pk_value}'")
            return []

        print(f"Posições processadas: {col_positions}")

        # 3. Obtém os nomes das colunas
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        all_columns = [column[0] for column in cursor.description]

        # 4. Valida e retorna as PKs (base 0)
        primary_keys = [all_columns[pos] for pos in col_positions if 0 <= pos < len(all_columns)]
        return primary_keys if primary_keys else []

    except Exception as e:
        print(f"[AVISO] Erro ao obter PKs: {str(e)[:200]}")
        return []

def upload_data_to_access(db_path: str, file_path: str,  depara_path ):


    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {file_path}")

    # Conectar ao banco de dados Access
    conn = pyodbc.connect(
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    )
    cursor = conn.cursor()
    info_filename = extract_info_from_filename(file_path, depara_path)
    table_name= info_filename[2]
    if table_name.lower() == "cotas_patrimonio_maps":
        cursor.close()
        conn.close()
        upload_cp_to_access(db_path, file_path, depara_path)
        return
    
    if table_name.lower() == "passivo_maps":
        cursor.close()
        conn.close()
        upload_passivo_to_access(db_path, file_path, depara_path)
        return

    try:
   
        # 1. Obter nomes reais das colunas e tentar identificar UNIQUE constraints
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        real_column_names = [column[0] for column in cursor.description]
        
        # 2. Estratégia alternativa para identificar colunas únicas
        primary_keys = get_primary_keys(cursor, table_name, depara_path )
        print(f"[PK] Chaves primárias identificadas: {primary_keys or 'Nenhuma (usando fallback)'}")

        if not primary_keys:
            # Fallback adicional: pedir ao usuário
            print("[AVISO] ATENÇÃO: Não foi possível determinar as chaves primárias automaticamente.")
            cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
            columns = [column[0] for column in cursor.description]
            print(f"Colunas disponíveis: {columns}")
            
            # Pode substituir por uma lógica automática mais segura se preferir
            primary_keys = [columns[0]]  # Usa a primeira coluna como fallback

        # Etapa 2: Processamento do arquivo
        extensao = os.path.splitext(file_path)[1].lower()

        # 3. Ler o arquivo de dados
        extensao = os.path.splitext(file_path)[1].lower()
        if extensao == '.csv':
            df = pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1', skiprows=3, header=None)
        elif extensao in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, header=None, skiprows=3)
        else:
            raise ValueError(f"Formato não suportado: {extensao}")

        # Variáveis de controle
        success_count = 0
        failure_count = 0
        total_count = 0
        blank_count = 0
        insert_count = 0
        update_count = 0

        #deleta os dados que ja exitem do fundo & data que sera inputado
        delete_input(db_path, table_name, info_filename[1],info_filename[0])

        # Valores fixos para as primeiras colunas
        fixed_values= [info_filename[0],info_filename[1]]
        for index, row in df.iterrows():
      

            primeira_coluna_valor = str(row[0]) if not pd.isnull(row[0]) else ""

            if any(termo in primeira_coluna_valor.lower() for termo in ["total", "—", "variação"]):
                total_count += 1
                continue
            elif primeira_coluna_valor.strip() == "":
                blank_count += 1
                continue

            try:
                #df_row_values_processed = [val for val in row.values if not pd.isna(val)]
                df_row_values_processed = [str(val).replace("—", "0").replace(".", ",") if not pd.isna(val) else "" for val in row.values]
                df_row_values_processed = [val for val in df_row_values_processed if val.strip()]

                values_to_insert_this_row = fixed_values + df_row_values_processed
                print(f"Inserindo lina: {values_to_insert_this_row}")
                # Verificar se temos valores suficientes
                if len(values_to_insert_this_row) < len(real_column_names):
                    print(f"[AVISO] Aviso: Linha {index+1} tem menos valores que colunas")
                    failure_count += 1
                    continue

                # NOVA ESTRATÉGIA DE UPSERT - COMEÇA AQUI
                # 1. Preparar partes da query dinamicamente
                where_conditions = " AND ".join([f"[{pk}] = ?" for pk in primary_keys])
                set_columns = [col for col in real_column_names if col not in primary_keys]
                
                # 2. Query de UPDATE - só atualiza colunas não-PK
                update_query = f"""
                UPDATE {table_name} 
                SET {', '.join([f'[{col}] = ?' for col in set_columns])}
                WHERE {where_conditions}
                """
                
                # 3. Separar valores: PKs para WHERE, outros para SET
                where_values = [values_to_insert_this_row[real_column_names.index(pk)] for pk in primary_keys]
                set_values = [values_to_insert_this_row[real_column_names.index(col)] for col in set_columns]
                
                # 4. Executar UPDATE
                cursor.execute(update_query, set_values + where_values)
                
                # 5. Se não atualizou nada, fazer INSERT
                if cursor.rowcount == 0:
                    insert_query = f"""
                    INSERT INTO {table_name} ({', '.join([f'[{col}]' for col in real_column_names])})
                    VALUES ({', '.join(['?']*len(real_column_names))})
                    """
                    cursor.execute(insert_query, values_to_insert_this_row)
                    insert_count += 1
                else:
                    update_count += 1
                    
                success_count += 1
                # FIM DA NOVA ESTRATÉGIA

            except pyodbc.Error as e:
                failure_count += 1
                print(f"[AVISO] Erro na linha {index + 1}: {str(e)}")
                print(f"Valores tentados: {values_to_insert_this_row}")
                print(f"Valores de PK: {[values_to_insert_this_row[real_column_names.index(pk)] for pk in primary_keys]}")
            except Exception as e:
                failure_count += 1
                print(f"[AVISO] Erro genérico na linha {index + 1}: {str(e)}")
                print(f"Valores tentados: {values_to_insert_this_row}")

        conn.commit()
        print("Transação confirmada.")

    except Exception as e:
        conn.rollback()
        print(f"Erro durante o processamento: {e}")
        raise

    finally:
        cursor.close()
        conn.close()
        print("Conexão fechada.")

    # Resumo
    print(f"\n--- Resumo do Upload ---")
    print(f"Linhas processadas: {success_count + failure_count}")
    print(f"Inserts: {insert_count} | Updates: {update_count}")
    print(f"Falhas: {failure_count}")
    print(f"Linhas puladas (total/blank): {total_count}/{blank_count}")

def process_all_files_in_folder(db_path: str, folder_path: str, depara_path: str):
    """Processa todos os arquivos Excel na pasta especificada"""
    
    # Lista todos os arquivos na pasta
    try:
        files = [f for f in os.listdir(folder_path) 
                if f.lower().endswith(('.xlsx', '.xls')) 
                and not f.startswith('~$')]  # Ignora arquivos temporários
        
        if not files:
            print(f"Nenhum arquivo Excel encontrado na pasta: {folder_path}")
            return

        print(f"\n[INFO] Encontrados {len(files)} arquivos para processar:")
        for f in files:
            print(f" - {f}")

        # Processa cada arquivo
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            print(f"\n[PROC] Processando arquivo: {filename}")
            
            try:
                upload_data_to_access(db_path, file_path, depara_path)
                print(f"[OK] Arquivo {filename} processado com sucesso!")
            except Exception as e:
                print(f"[ERRO] Erro ao processar {filename}: {str(e)}")
                continue

    except Exception as e:
        print(f"Erro ao acessar a pasta: {str(e)}")

def upload_cp_to_access(db_path: str, file_path: str, depara_path: str):
    """
    Versão simplificada com conversão de tipos robusta para o Access
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {file_path}")

    # Conectar ao banco de dados Access
    conn = pyodbc.connect(
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    )
    cursor = conn.cursor()
    
    try:
        info_filename = extract_info_from_filename(file_path, depara_path)
        table_name = info_filename[2]  # Nome da tabela no Access

        # 1. Obter estrutura da tabela
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        real_column_names = [column[0] for column in cursor.description]
        
        # 2. Ler o arquivo Excel
        extensao = os.path.splitext(file_path)[1].lower()
        
        if extensao == '.csv':
            df = pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1', skiprows=0, header=None, keep_default_na=False)
        elif extensao in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, header=None, skiprows=0, keep_default_na=False)
        else:
            raise ValueError(f"Formato não suportado: {extensao}")

        # 3. Processar os dados
        valores_segunda_coluna = []
        total_count = 0
        blank_count = 0

        for index, row in df.iterrows():
            primeira_coluna_valor = str(row[0]).strip()
            
            if any(termo in primeira_coluna_valor.lower() for termo in [ "—", "variação"]):
                total_count += 1
                continue
            elif not primeira_coluna_valor:
                blank_count += 1
                continue
            
            segunda_coluna_valor = str(row[1]).strip() if row[1] != "" else None
            valores_segunda_coluna.append(segunda_coluna_valor)

        # 4. Preparar valores para inserção
        valores_insercao = [
            info_filename[0],  # Data
            info_filename[1]   # Nome do fundo
        ]
        
        # Adicionar valores da segunda coluna
        valores_insercao.extend(valores_segunda_coluna)

        # 5. Converter tipos para o Access
        def convert_for_access(value):
            if value is None:
                return None
            try:
                # Se já é datetime.date, converte para string no formato do Access
                if hasattr(value, 'strftime'):  # Para datetime.date ou datetime.datetime
                    return value.strftime('%Y-%m-%d')
                # Se é string de data no formato dd/mm/yyyy
                elif isinstance(value, str) and re.match(r'\d{2}/\d{2}/\d{4}', value):
                    return datetime.datetime.strptime(value, '%d/%m/%Y').strftime('%Y-%m-%d')
                # Se é número com vírgula decimal
                elif isinstance(value, str) and ',' in value and value.replace(',', '').replace('.', '').isdigit():
                    return float(value.replace(',', '.'))
                # Se é número inteiro como string
                elif isinstance(value, str) and value.isdigit():
                    return int(value)
                else:
                    return str(value)
            except Exception as e:
                print(f"Aviso: Não foi possível converter {value} ({type(value)}), mantendo como string")
                return str(value)

        valores_convertidos = [convert_for_access(val) for val in valores_insercao]

        # 6. Ajustar tamanho
        if len(valores_convertidos) > len(real_column_names):
            valores_convertidos = valores_convertidos[:len(real_column_names)]
        elif len(valores_convertidos) < len(real_column_names):
            valores_convertidos += [None] * (len(real_column_names) - len(valores_convertidos))

        # 7. Executar UPSERT
        try:
            # Primeiro tentar UPDATE
            where_conditions = f"[{real_column_names[0]}] = ? AND [{real_column_names[1]}] = ?"
            update_cols = [f"[{col}] = ?" for col in real_column_names[2:]]
            
            update_query = f"""
            UPDATE {table_name} 
            SET {', '.join(update_cols)}
            WHERE {where_conditions}
            """
            
            cursor.execute(update_query, valores_convertidos[2:] + valores_convertidos[:2])
            
            if cursor.rowcount == 0:
                insert_query = f"""
                INSERT INTO {table_name} ({', '.join([f'[{col}]' for col in real_column_names])})
                VALUES ({', '.join(['?']*len(real_column_names))})
                """
                cursor.execute(insert_query, valores_convertidos)
                print("[OK] Nova linha inserida com sucesso")
            else:
                print("[OK] Linha existente atualizada com sucesso")
                
            conn.commit()

        
        except pyodbc.Error as e:
            conn.rollback()
            print(f"[AVISO] Erro durante o UPSERT: {str(e)}")
            print("Valores tentados:")
            for col, val in zip(real_column_names, valores_convertidos):
                print(f"  {col}: {val}")
            raise

    except Exception as e:
        conn.rollback()
        print(f"Erro durante o processamento: {e}")
        raise

    finally:
        cursor.close()
        conn.close()
        print("Conexão fechada.")

    # Resumo
    print(f"\n--- Resumo do Upload ---")
    print(f"Total de linhas processadas: {len(valores_segunda_coluna)}")
    print(f"Linhas puladas (total/blank): {total_count}/{blank_count}")

def delete_input(db_path: str, table_name: str, fundo: str, data: date):
    """Deleta todas as linhas de uma tabela que tenham a mesma DATA_INPUT e FUNDO"""
    
    # Conectar ao banco de dados Access
    conn = pyodbc.connect(
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    )
    cursor = conn.cursor()
    
    try:
        # Formatar a data para o formato do Access (AAAA-MM-DD)
        data_str = data.strftime('%Y-%m-%d')
        
        # Query para deletar registros
        delete_query = f"""
        DELETE FROM {table_name}
        WHERE [DATA_INPUT] = ? AND [FUNDO] = ?
        """
        
        # Executar a query
        cursor.execute(delete_query, data_str, fundo)
        deleted_rows = cursor.rowcount
        
        # Confirmar a transação
        conn.commit()
        
        print(f"[OK] {deleted_rows} linhas deletadas da tabela {table_name} para o fundo '{fundo}' na data {data_str}")
        
        return deleted_rows
        
    except pyodbc.Error as e:
        conn.rollback()
        print(f"[AVISO] Erro ao deletar registros: {str(e)}")
        raise
        
    finally:
        cursor.close()
        conn.close()

def upload_passivo_to_access(db_path: str, file_path: str,  depara_path ):


    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {file_path}")

    # Conectar ao banco de dados Access
    conn = pyodbc.connect(
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    )
    cursor = conn.cursor()
    info_filename = extract_info_from_filename(file_path, depara_path)
    table_name= info_filename[2]
    if table_name.lower() == "cotas_patrimonio_maps":
        cursor.close()
        conn.close()
        upload_cp_to_access(db_path, file_path, depara_path)
        return

   
    try:
   
        # 1. Obter nomes reais das colunas e tentar identificar UNIQUE constraints
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        real_column_names = [column[0] for column in cursor.description]
        
        # 2. Estratégia alternativa para identificar colunas únicas
        primary_keys = get_primary_keys(cursor, table_name, depara_path )
        print(f"[PK] Chaves primárias identificadas: {primary_keys or 'Nenhuma (usando fallback)'}")

        if not primary_keys:
            # Fallback adicional: pedir ao usuário
            print("[AVISO] ATENÇÃO: Não foi possível determinar as chaves primárias automaticamente.")
            cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
            columns = [column[0] for column in cursor.description]
            print(f"Colunas disponíveis: {columns}")
            
            # Pode substituir por uma lógica automática mais segura se preferir
            primary_keys = [columns[0]]  # Usa a primeira coluna como fallback

        # Etapa 2: Processamento do arquivo
        extensao = os.path.splitext(file_path)[1].lower()

        # 3. Ler o arquivo de dados
        extensao = os.path.splitext(file_path)[1].lower()
        if extensao == '.csv':
            df = pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1', skiprows=3, header=None)
        elif extensao in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path, header=None, skiprows=3)
        else:
            raise ValueError(f"Formato não suportado: {extensao}")

        # Variáveis de controle
        success_count = 0
        failure_count = 0
        total_count = 0
        blank_count = 0
        insert_count = 0
        update_count = 0

        #deleta os dados que ja exitem do fundo & data que sera inputado
        delete_input(db_path, table_name, info_filename[1],info_filename[0])

        # Valores fixos para as primeiras colunas
        fixed_values = [info_filename[0],info_filename[1]]
        nome_investidor, documento = extract_investor_data(file_path)
        
        # Define valores padrão se não encontrar
        dados_cotistas = [nome_investidor if nome_investidor else 'NOME_NÃO_ENCONTRADO',documento if documento else 'DOC_NÃO_ENCONTRADO']


        
        for index, row in df.iterrows():
      

            primeira_coluna_valor = str(row[0]) if not pd.isnull(row[0]) else ""

            if any(termo in primeira_coluna_valor.lower() for termo in ["total", "—", "variação"]):
                total_count += 1
                continue
            elif primeira_coluna_valor.strip() == "":
                blank_count += 1
                continue

            try:
                #df_row_values_processed = [val for val in row.values if not pd.isna(val)]
                df_row_values_processed = [str(val).replace("—", "0") if not pd.isna(val) else "" for val in row.values]
                df_row_values_processed = [val for val in df_row_values_processed if val.strip()]

                values_to_insert_this_row = fixed_values + dados_cotistas + df_row_values_processed
                print(f"Inserindo lina: {values_to_insert_this_row}")
                # Verificar se temos valores suficientes
                if len(values_to_insert_this_row) < len(real_column_names):
                    print(f"[AVISO] Aviso: Linha {index+1} tem menos valores que colunas")
                    failure_count += 1
                    continue

                # NOVA ESTRATÉGIA DE UPSERT - COMEÇA AQUI
                # 1. Preparar partes da query dinamicamente
                where_conditions = " AND ".join([f"[{pk}] = ?" for pk in primary_keys])
                set_columns = [col for col in real_column_names if col not in primary_keys]
                
                # 2. Query de UPDATE - só atualiza colunas não-PK
                update_query = f"""
                UPDATE {table_name} 
                SET {', '.join([f'[{col}] = ?' for col in set_columns])}
                WHERE {where_conditions}
                """
                
                # 3. Separar valores: PKs para WHERE, outros para SET
                where_values = [values_to_insert_this_row[real_column_names.index(pk)] for pk in primary_keys]
                set_values = [values_to_insert_this_row[real_column_names.index(col)] for col in set_columns]
                
                # 4. Executar UPDATE
                cursor.execute(update_query, set_values + where_values)
                
                # 5. Se não atualizou nada, fazer INSERT
                if cursor.rowcount == 0:
                    insert_query = f"""
                    INSERT INTO {table_name} ({', '.join([f'[{col}]' for col in real_column_names])})
                    VALUES ({', '.join(['?']*len(real_column_names))})
                    """
                    cursor.execute(insert_query, values_to_insert_this_row)
                    insert_count += 1
                else:
                    update_count += 1
                    
                success_count += 1
                # FIM DA NOVA ESTRATÉGIA

            except pyodbc.Error as e:
                failure_count += 1
                print(f"[AVISO] Erro na linha {index + 1}: {str(e)}")
                print(f"Valores tentados: {values_to_insert_this_row}")
                print(f"Valores de PK: {[values_to_insert_this_row[real_column_names.index(pk)] for pk in primary_keys]}")
            except Exception as e:
                failure_count += 1
                print(f"[AVISO] Erro genérico na linha {index + 1}: {str(e)}")
                print(f"Valores tentados: {values_to_insert_this_row}")

        conn.commit()
        print("Transação confirmada.")

    except Exception as e:
        conn.rollback()
        print(f"Erro durante o processamento: {e}")
        raise

    finally:
        cursor.close()
        conn.close()
        print("Conexão fechada.")

    # Resumo
    print(f"\n--- Resumo do Upload ---")
    print(f"Linhas processadas: {success_count + failure_count}")
    print(f"Inserts: {insert_count} | Updates: {update_count}")
    print(f"Falhas: {failure_count}")
    print(f"Linhas puladas (total/blank): {total_count}/{blank_count}")

def extract_investor_data(file_path):
    """Extrai nome do investidor e CNPJ da segunda linha do arquivo."""
    extensao = os.path.splitext(file_path)[1].lower()
    
    try:
        if extensao == '.csv':
            with open(file_path, 'r', encoding='ISO-8859-1') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    segunda_linha = lines[1].strip()  # Segunda linha (índice 1)
        elif extensao in ['.xls', '.xlsx']:
            df_temp = pd.read_excel(file_path, header=None, nrows=2)
            segunda_linha = str(df_temp.iloc[1, 0]) if len(df_temp) >= 2 else ""
        else:
            return None, None
        
        # Extrair nome e CNPJ usando expressão regular
        import re
        padrao = r"Investidor:\s*(.+?)\s*\(\s*([0-9./-]+)\s*\)"
        match = re.search(padrao, segunda_linha)
        
        if match:
            nome_investidor = match.group(1).strip()
            cnpj = match.group(2).strip()
            return nome_investidor, cnpj
        return None, None
        
    except Exception as e:
        print(f"Erro ao extrair dados do investidor: {e}")
        return None, None



if __name__ == "__main__":
   

    
    if len(sys.argv) == 4:
            # Recebe os argumentos do VBA
            db_path = sys.argv[1]  # Caminho DEPARA
            folder_path = sys.argv[2] # Pasta PDFs
            depara_path = sys.argv[3] # Caminho fundos
            
            print(f"Argumentos recebidos:")
            print(f"1. Base: {db_path}")
            print(f"2. Pasta Aux_maps: {folder_path}")
            print(f"3. Depara: {depara_path}")
    else:
            # Modo interativo (se executado diretamente)
           #db_path = input("Digite o caminho da Base Access: ")
           #folder_path = input("Digite o caminho da pasta de AUX: ")
           #depara_path = input("Digite o caminho do arquivo Depara: ")
            # Configurações (substitua com seus caminhos reais)
            db_path = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\09. Base_de_Dados\Base Fundos_V2.accdb'
            folder_path = r'C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\06. AUXILIAR_MAPS'
            depara_path = r"C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\07. DEPARA\DE PARA.xlsx"
          


    # Processa todos os arquivos da pasta
    process_all_files_in_folder(db_path, folder_path, depara_path)

    

