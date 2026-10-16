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

def add_abstracts_to_ris(input_path, output_path, api_key):
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



def main(args):
    API_KEY = os.getenv("ELSEVIER_KEY")
    FILES_DIR, FILE_NAME = args[0], args[1]

    input_ris = os.path.join(FILES_DIR, f'{FILE_NAME}.ris')
    output_ris_with_abstracts = os.path.join(FILES_DIR, f'{FILE_NAME}_w_abs.ris')
    
    add_abstracts_to_ris(input_ris, output_ris_with_abstracts, API_KEY)

if __name__ == "__main__":
    main(sys.argv[1:])