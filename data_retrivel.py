import os
import sys
import re
import time
import requests
from dotenv import load_dotenv
load_dotenv(override=True)


def fetch_abstract_by_doi(doi, api_key):
    """
    Busca o resumo (abstract) de um artigo na API da Elsevier usando o DOI.
    """
    if not doi:
        return None
    
    doi_clean = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi).strip()
    url = f"https://api.elsevier.com/content/article/doi/{doi_clean}"
    
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json"
    }
    scopus_url = f"https://api.elsevier.com/content/abstract/doi/{doi_clean}"
    response = requests.get(scopus_url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        abstract = data.get('abstracts-retrieval-response', {}).get('coredata', {}).get('dc:description')
        if abstract:
            return abstract.strip()
    
    # try:
    #     response = requests.get(url, headers=headers, timeout=10)
    #     if response.status_code == 200:
    #         data = response.json()
    #         full_text = data.get('full-text-retrieval-response', {})
    #         coredata = full_text.get('coredata', {})
            
    #         abstract = coredata.get('dc:description')
    #         if abstract:
    #             return abstract.strip()
                
    #         abs_struct = full_text.get('originalText', {}).get('abstract', {})
    #         if isinstance(abs_struct, dict):
    #             return abs_struct.get('ce:para', '')
    #         elif isinstance(abs_struct, str):
    #             return abs_struct
    #     else:
    #         # Tenta fallback usando a Scopus Abstract Retrieval API caso o anterior falhe
    #         scopus_url = f"https://api.elsevier.com/content/abstract/doi/{doi_clean}"
    #         response = requests.get(scopus_url, headers=headers, timeout=10)
    #         if response.status_code == 200:
    #             data = response.json()
    #             abstract = data.get('abstracts-retrieval-response', {}).get('coredata', {}).get('dc:description')
    #             if abstract:
    #                 return abstract.strip()
    # except Exception as e:
    #     pass
    return None

def add_abstracts_to_ris_old(input_path, output_path, api_key):
    if not os.path.exists(input_path):
        print(f"Arquivo de entrada não encontrado: {input_path}")
        return

    print("Lendo referências e buscando abstracts...")
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    records = content.split('ER  -')
    updated_records = []
    total = len(records) - 1  

    for idx, record in enumerate(records):
        if not record.strip():
            continue
        
        doi_match = re.search(r'^DO\s+-\s+(.*)$', record, re.MULTILINE)
        doi = doi_match.group(1).strip() if doi_match else None
        has_abstract = re.search(r'^AB\s+-', record, re.MULTILINE)
        
        abstract = None
        if doi and not has_abstract:
            print(f"[{idx+1}/{total}] Buscando abstract para o DOI: {doi}...")
            abstract = fetch_abstract_by_doi(doi, api_key)
            time.sleep(0.3)  # Evitar throttling da API
        
        lines = record.strip().split('\n')
        
        if abstract:
            abstract_clean = abstract.replace('\n', ' ').replace('\r', '')
            lines.append(f"AB  - {abstract_clean}")
            print(" -> Abstract adicionado com sucesso!")
        
        updated_records.append('\n'.join(lines) + '\nER  -')

    with open(output_path, 'w', encoding='utf-8') as f_out:
        f_out.write('\n\n'.join(updated_records) + '\n')
    
    print(f"\n✓ Concluído! Arquivo atualizado salvo em: {output_path}")

def add_abstracts_to_ris(input_path, output_path, api_key):
    if not os.path.exists(input_path):
        print(f"Arquivo de entrada não encontrado: {input_path}")
        return

    print("Lendo referências e verificando registros existentes...")
    
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    records = content.split('ER  -')
    total = len(records) - 1  

    # Carrega registros já processados no arquivo de saída (caso exista) para retomar de onde parou
    existing_dois_with_abs = set()
    existing_records_map = {}
    
    if os.path.exists(output_path):
        print("Arquivo de saída já existe. Carregando progresso anterior...")
        with open(output_path, 'r', encoding='utf-8', errors='ignore') as f_out_existing:
            existing_content = f_out_existing.read()
        existing_records = existing_content.split('ER  -')
        for rec in existing_records:
            if not rec.strip():
                continue
            doi_m = re.search(r'^DO\s+-\s+(.*)$', rec, re.MULTILINE)
            if doi_m:
                doi_val = doi_m.group(1).strip()
                if 'AB  -' in rec:
                    existing_dois_with_abs.add(doi_val)
                existing_records_map[doi_val] = rec.strip() + '\nER  -'

    updated_records = []

    for idx, record in enumerate(records):
        record_clean = record.strip()
        if not record_clean:
            continue
        
        doi_match = re.search(r'^DO\s+-\s+(.*)$', record_clean, re.MULTILINE)
        doi = doi_match.group(1).strip() if doi_match else None
        has_abstract = re.search(r'^AB\s+-', record_clean, re.MULTILINE)
        
        # Se já temos o registro salvo com abstract no output, reaproveita ele
        if doi and doi in existing_records_map:
            print(f"[{idx+1}/{total}] DOI {doi} já processado anteriormente. Mantendo.")
            updated_records.append(existing_records_map[doi])
            continue

        lines = record_clean.split('\n')
        
        # Se tem DOI mas não tem abstract nem no original nem nos salvos
        if doi and not has_abstract and doi not in existing_dois_with_abs:
            print(f"[{idx+1}/{total}] Buscando abstract para o DOI: {doi}...")
            abstract = fetch_abstract_by_doi(doi, api_key)
            time.sleep(0.3)  # Evitar throttling da API
            
            if abstract:
                abstract_clean = abstract.replace('\n', ' ').replace('\r', '')
                lines.append(f"AB  - {abstract_clean}")
                print(" -> Abstract adicionado com sucesso!")
            else:
                print(" -> Abstract não encontrado na API.")
        elif has_abstract:
            print(f"[{idx+1}/{total}] Abstract já presente no registro original para DOI: {doi}.")

        current_record_str = '\n'.join(lines) + '\nER  -'
        updated_records.append(current_record_str)
        
        # SALVAMENTO IMEDIATO: Grava no arquivo a cada alteração/iteração para não perder progresso
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write('\n\n'.join(updated_records) + '\n')

    print(f"\n✓ Concluído! Arquivo atualizado salvo em: {output_path}")



def main(args):
    API_KEY = os.getenv("ELSEVIER_KEY")
    FILES_DIR, FILE_NAME = args[0], args[1]

    input_ris = os.path.join(FILES_DIR, f'{FILE_NAME}.ris')
    output_ris_with_abstracts = os.path.join(FILES_DIR, f'{FILE_NAME}_w_abs.ris')
    
    add_abstracts_to_ris(input_ris, output_ris_with_abstracts, API_KEY)

if __name__ == "__main__":
    main(sys.argv[1:])