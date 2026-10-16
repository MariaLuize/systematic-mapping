import pandas as pd
import requests
import json


INPUT_ARTICLES = 'artigos.csv'
OUTPUT         = 'artigos_avaliados.csv'
MODEL          = 'gemma:2b'
URL_OLLAMA     = 'http://localhost:11434/api/generate'


CRITERIA = """
Critérios de Inclusão (CI):
CI1: O artigo aborda Inteligência Artificial na Educação.
CI2: O artigo foi publicado entre 2015 e 2024.

Critérios de Exclusão (CE):
CE1: O artigo é uma revisão de literatura (não é um estudo primário).
CE2: O artigo não está em inglês ou português.
"""


def assess_article(title, abstract):
    """Envia o artigo para o Ollama e retorna a avaliação em JSON."""
    
    prompt = f"""
    Você é um pesquisador acadêmico avaliando artigos para um mapeamento sistemático.
    
    {CRITERIOS}
    
    Artigo a ser avaliado:
    Título: {title}
    Resumo: {abstract}
    
    Avalie o artigo com base estritamente nos critérios acima. 
    Responda APENAS com um objeto JSON válido no seguinte formato exato, sem markdown adicional:
    {{
      "decisao": "INCLUIR" ou "EXCLUIR" ou "DUVIDA",
      "criterio_aplicado": "Nome do CI ou CE principal",
      "justificativa_curta": "Explicação em 1 frase"
    }}
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" 
    }

    try:
        response = requests.post(URL_OLLAMA, json=payload)
        response.raise_for_status()
        resultado_texto = response.json().get("response", "")
        
        # Converte a resposta de texto para um dicionário Python
        return json.loads(resultado_texto)
    
    except Exception as e:
        print(f"Erro ao processar o artigo '{titulo[:30]}...': {e}")
        return {"decisao": "ERRO", "criterio_aplicado": "-", "justificativa_curta": str(e)}

def main():
    df = pd.read_csv(INPUT_ARTICLES)
    
    if 'Titulo' not in df.columns or 'Resumo' not in df.columns:
        print("Erro: O arquivo CSV deve conter as colunas 'Titulo' e 'Resumo'.")
        return

    
    decisoes = []
    criteria = []
    justificativas = []

    total_artigos = len(df)
    print(f"Iniciando avaliação de {total_artigos} artigos com {MODELO}...\n")

    for index, row in df.iterrows():
        print(f"Processando [{index + 1}/{total_artigos}]: {row['Titulo'][:50]}...")
        
        avaliacao = avaliar_artigo(row['Titulo'], row['Resumo'])
        
        decisoes.append(avaliacao.get("decisao", "ERRO"))
        criterios.append(avaliacao.get("criterio_aplicado", "-"))
        justificativas.append(avaliacao.get("justificativa_curta", "-"))

    # Adiciona os resultados ao DataFrame original
    df['Decisao_LLM'] = decisoes
    df['Criterio_Aplicado'] = criterios
    df['Justificativa_LLM'] = justificativas

    # Salva o novo arquivo
    df.to_csv(ARQUIVO_SAIDA, index=False)
    print(f"\nProcessamento concluído! Resultados salvos em: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()