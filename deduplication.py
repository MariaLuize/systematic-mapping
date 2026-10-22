import os
import re

def remover_duplicatas_ris(caminho_entrada, caminho_saida, caminho_log="duplicatas_removidas.log"):
    if not os.path.exists(caminho_entrada):
        print(f"Erro: O arquivo '{caminho_entrada}' não foi encontrado.")
        return

    print(f"Lendo '{caminho_entrada}' para remover duplicatas...")

    with open(caminho_entrada, 'r', encoding='utf-8', errors='ignore') as f:
        conteudo = f.read()
    registros = conteudo.split('ER  -')
    
    registros_unicos = []
    dois_vistos = set()
    titulos_vistos = set()
    
    linhas_log = []
    linhas_log.append("RELATÓRIO DE REGISTROS DUPLICADOS REMOVIDOS")
    linhas_log.append("=" * 60 + "\n")
    
    total_originais = 0
    duplicatas_removidas = 0

    for idx, registro in enumerate(registros, 1):
        registro_limpo = registro.strip()
        if not registro_limpo:
            continue
            
        total_originais += 1
        
        # Seach doi
        doi_match = re.search(r'^DO\s+-\s+(.*)$', registro_limpo, re.MULTILINE)
        doi = doi_match.group(1).strip().lower() if doi_match else None
        
        # search title
        titulo_match = re.search(r'^(?:TI|T1)\s+-\s+(.*)$', registro_limpo, re.MULTILINE)
        titulo = titulo_match.group(1).strip() if titulo_match else None
        
        is_duplicata = False
        motivo_remocao = ""
        
        if doi:
            if doi in dois_vistos:
                is_duplicata = True
                motivo_remocao = f"DOI já existente ({doi})"
            else:
                dois_vistos.add(doi)
                
        if titulo and not is_duplicata:
            titulo_normalizado = re.sub(r'[^a-z0-9]', '', titulo.lower())
            
            if titulo_normalizado in titulos_vistos:
                is_duplicata = True
                motivo_remocao = "Título já existente (após normalização)"
            else:
                titulos_vistos.add(titulo_normalizado)
                

        if is_duplicata:
            duplicatas_removidas += 1
            texto_titulo = titulo if titulo else "Sem Título"
            texto_doi = doi if doi else "Sem DOI"
            linhas_log.append(f"Removido Registro #{total_originais}")
            linhas_log.append(f"Motivo: {motivo_remocao}")
            linhas_log.append(f"Título: {texto_titulo}")
            linhas_log.append(f"DOI: {texto_doi}")
            linhas_log.append("-" * 60)
        else:
            registros_unicos.append(registro_limpo + '\nER  -')

    with open(caminho_saida, 'w', encoding='utf-8') as f_out:
        f_out.write('\n\n'.join(registros_unicos) + '\n')
    with open(caminho_log, 'w', encoding='utf-8') as f_log:
        f_log.write('\n'.join(linhas_log) + '\n')
    
    print("\n" + "=" * 40)
    print("RESUMO DA LIMPEZA")
    print("=" * 40)
    print(f"Total de registros lidos: {total_originais}")
    print(f"Duplicatas removidas:     {duplicatas_removidas}")
    print(f"Registros finais únicos:  {len(registros_unicos)}")
    print(f"Arquivo RIS salvo como:   {caminho_saida}")
    print(f"Arquivo LOG salvo como:   {caminho_log}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    INPUT_FILE  = "./original_ris_files/combined_raw_sag_sistematic_mapping.ris"
    OUTPUT_FILE = "./original_ris_files/combined_deduplicated.ris"
    OUTPUT_LOG  = "./original_ris_files/removed_duplicates.log"
    
    remover_duplicatas_ris(INPUT_FILE, OUTPUT_FILE,OUTPUT_LOG)