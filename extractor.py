import os
import glob
import time
from typing import List, Literal, Optional
import pandas as pd
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv(override=True)



class MiningPaperExtraction(BaseModel):
    titulo_artigo: str = Field(
        description="Título completo do artigo."
    )
    ano_publicacao: Optional[int] = Field(
        description="Ano de publicação do artigo."
    )
    # rq1_1_modelos_rn: List[str] = Field(
    #     description=(
    #         "Lista objetiva de modelos/arquiteturas de Redes Neurais usados, podem ser modelo de Machine Learning ou qualquer estrutura designada para realizar a classificação/detecção de mineraçcôes com solo exposto "
    #         "(ex.: 'U-Net', 'Swin-Unet', 'YOLOv11x-seg', 'ResNet-50', 'GCN', 'ViT', 'CNN', 'Autoencoder'). "
    #         # "Se não usar redes neurais, retornar ['None']."
    #     )
    # )
    rq1_1_modelos_metodos: List[str] = Field(
        description=(
            "Todos os modelos ou métodos efetivamente treinados, executados, avaliados ou "
            "comparados nos experimentos e resultados do artigo para detecção, segmentação ou "
            "classificação de mineração em solo exposto — incluindo tanto o modelo proposto "
            "quanto os baselines/modelos comparados experimentalmente (ex.: 'AuxTransUNet', "
            "'U-Net', 'DeepLab v3 (ResNet50)', 'DeepLab v3+ (ResNet50)', 'ViT-Unet', "
            "'R50-ViT-Unet', 'TransUNet', 'Swin-Unet', 'SegFormer', 'Random Forest', "
            "'SVM', 'NDVI thresholding'). "
            "NÃO inclua as configurações dos modelos utilizados (ex: função de ativação, função de loss, Adam, FocalLoss e etc"
            "NÃO inclua modelos citados apenas na Introdução, Trabalhos Relacionados ou "
            "referências sem execução experimental no artigo, nem métodos usados apenas como "
            "pré-processamento ou geração de rótulos/dados de apoio."
        )
    )
    rq1_2_escopo_tarefa: List[
        Literal[
            "Semantic Segmentation",
            "Instance Segmentation",
            "Bounding Box",
            "Pixel Classification",
            "Scene Classification",
        ]
    ] = Field(
        description="Formulação espacial da saída do modelo. Escolha apenas dentre as opções permitidas.Pixel Classification faz referencia a modelos de machine learning que agem no nivel do pixel"
    )
    rq1_3_alvo: List[str] = Field(
        description=(
            "Alvo espacial mapeado. Padronize usando termos curtos como: "
            "'Mining Footprint', 'Open-pit', 'Spoil Dumps / Waste Rock', "
            "'Mining Ponds', 'Oil Wells', 'LULC Multi-class com mineração'. "
            "Nota: excluir barragens de rejeitos (TSF) se não aplicável, ou indicar se for o foco."
        )
    )
    rq1_4_modo_deteccao: Literal["Blind mode", "Prior ROI", "Hybrid"] = Field(
        description=(
            "'Blind mode' se varre a cena/região aberta sem máscaras/cadastros prévios na inferência, é permitido se a região de interesse (ROI) for ampla e não voltada para algum tipo de LULC espacĩfico. Ex:cidade, estado, região e etc; "
            "'Prior ROI' se recorta apenas minas/inventários previamente conhecidos. Ex: classificação dentro de alertas prévios e etc"
        )
    )
    rq1_5_benchmarks: List[str] = Field(
        description=(
            "Comparações explícitas realizadas (ex.: 'DL vs Random Forest', 'DL vs SVM', "
            "'Multiple DL architectures', 'None')."
        )
    )
    rq2_1_sensores: List[str] = Field(
        description=(
            "Satélites/sensores usados com nomes padronizados "
            "(ex.: 'Sentinel-2', 'Landsat-8', 'Landsat-5/7/8/9', 'Sentinel-1 SAR', 'PlanetScope', 'Google Earth', 'ALOS PALSAR')."
        )
    )
    rq2_2_resolucao_espacial: List[str] = Field(
        description=(
            "Resoluções espaciais dos dados de entrada padronizadas (ex.: '10m', '30m', '1.8m', '<5m') "
            "e se há comparação de escala ('Scale comparison: Yes' ou 'Scale comparison: No')."
        )
    )
    rq2_3_features: List[str] = Field(
        description=(
            "Atributos/canais usados no treino de forma curta "
            "(ex.: 'Blue, Red, Green', 'VV','VH', 'NDVI', 'kNDVI', 'BSI', 'MNDWI', 'DEM', 'LandTrendr','NIR', 'TIR1','TIR2','SWIR1',SWIR2','Red Edge 1')."
            " Não considerar termos como gerais e muito especĩficos do artigo:  'Frequency-domain features','Imaginary part of DFT','High-frequency mask' "
        )
    )
    rq2_4_pais_regiao: List[str] = Field(
        description="País(es) e região(ões) de estudo/inferência (ex.: 'European Union','China (Shanxi)', 'Peru (Madre de Dios)', 'Chile (Antofagasta)', 'Global')."
    )
    rq3_1_dataset_supervisionado: str = Field(
        description=(
            "Resumo objetivo em até 15 palavras sobre existência, origem e rotulagem do dataset "
            "(ex.: 'Field surveys GPS', 'Visual-interpretation (Google Earth)', 'Mapbiomas derived')."
        )
    )
    # rq3_2_preprocessamento_augmentation: List[str] = Field(
    #     description=(
    #         "Técnicas padronizadas de pré-processamento e augmentation "
    #         "(ex.: 'Atmospheric Correction', 'Median/Mean Compositing', 'Normalization', 'geometric correction','Upsampling' "
    #         "'Geometric Augmentation (Flip/Rotate)', 'Synthetic Data (GAN/Diffusion)', 'None')."
    #     )
    # )

    rq3_2_preprocessamento_augmentation: List[str] = Field(
        description=(
            "Técnicas de pré-processamento, geração de atributos/dados de apoio, "
            "curadoria de amostras/rótulos e data augmentation (ex.: 'Atmospheric Correction', "
            "'Median/Mean Compositing', 'Normalization', 'LandTrendr', 'CCDC', 'DTW', "
            "'Geometric Augmentation', "
            "'Synthetic Data (GAN/Diffusion)', 'None'). "
            "Se 'LandTrendr' ou algoritmos similares forem usados para extrair trajetórias, "
            "gerar dados de apoio ou apoiar a rotulagem/pré-processamento, registre aqui."
        )
    )

    rq3_3_nuvens_sombras_continuo: List[str] = Field(
        description=(
            "Como lida com nuvens/sombras e continuidade temporal. Padronize entre: "
            "'Cloud-free scene selection', 'Temporal compositing', 'Cloud/shadow masking (QA/Fmask)', "
            "'SAR all-weather fusion', 'Direct inference with clouds/shadows', 'Continuous monitoring', 'Not reported'."
        )
    )
    rq4_1_pos_processamento: List[str] = Field(
        description=(
            "Técnicas aplicadas após a predição da rede "
            "(ex.: 'Morphological Operations', 'Majority/Spatial Filtering', 'Vectorization / GIS Overlay', 'Threshold Tuning', 'None')."
        )
    )
    rq4_2_metricas_validacao: List[str] = Field(
        description=(
            "Métricas quantitativas padronizadas "
            "(ex.: 'IoU / mIoU', 'F1-score', 'Precision', 'Recall', 'Overall Accuracy', 'Kappa coefficient', 'mAP50')."
        )
    )
    observacao_revisor: str = Field(
        description="Nota curta (máx. 20 palavras) destacando limitações ou alertas metodológicos relevantes para triagem."
    )


# 2. Prompt de Sistema para rigor científico e padronização para gráficos
SYSTEM_INSTRUCTION = """
Você é um pesquisador especialista em Sensoriamento Remoto e Deep Learning conduzindo uma Revisão Sistemática da Literatura sobre detecção/segmentação de mineração em solo exposto.
Extraia as informações do artigo PDF anexado preenchendo rigorosamente o schema JSON solicitado.

REGRAS ESTRITAS:
1. Objetividade para Gráficos: Nos campos de lista, use sempre rótulos curtos, padronizados e em inglês técnico (ex.: 'U-Net' em vez de 'a modified U-Net architecture'), para que os valores possam ser agrupados diretamente em gráficos de frequência.
2. Sem Especulação: Extraia apenas o que está explicitamente comprovado no texto, tabelas ou figuras. Se algo não for mencionado, use 'Not reported' ou 'None'.
3. Rigor na RQ1.4 (Modo de Detecção): Classifique como 'Blind mode' apenas se o modelo varrer toda a cena/região livremente na inferência. Se o modelo depender de coordenadas cadastrais prévias ou recortes centrados em minas conhecidas, classifique como 'Prior ROI'.
4. Rigor na RQ3.3 (Nuvens/Sombras): Diferencie claramente artigos que apenas baixam cenas sem nuvens ('Cloud-free scene selection') daqueles que realmente operam de forma contínua sobre imagens com nuvens/sombras.
"""


def process_pdfs(pdf_folder: str, output_prefix: str = "extracao_revisao_sistematica"):
    api_k = os.getenv("GEMINI_API_KEY")

    client = genai.Client()
    # for model in client.models.list():
    #     print(model.name, model.display_name)
    # die
    pdf_files = sorted(glob.glob(os.path.join(pdf_folder, "*.pdf")))

    if not pdf_files:
        print(f"Nenhum PDF encontrado em: {pdf_folder}")
        return

    records = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Processando: {filename}...")

        # Upload do PDF via File API
        uploaded_file = client.files.upload(file=pdf_path)

        try:
            # gemini-2.5-flash oferece excelente custo-benefício e precisão para leitura de PDFs longos;
            # troque para 'gemini-2.5-pro' se quiser raciocínio ainda mais profundo.
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    uploaded_file,
                    "Extraia todas as informações das RQs deste artigo seguindo rigorosamente as instruções.",
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=MiningPaperExtraction,
                    temperature=0.0,  # Determinístico para extração científica
                ),
            )

            # Valida e converte o JSON retornado pelo Pydantic
            parsed: MiningPaperExtraction = response.parsed
            row = parsed.model_dump()
            row["arquivo_pdf"] = filename

            # Converte listas em strings separadas por '; ' para facilitar leitura no Excel/CSV e explode() no pandas
            for key, val in row.items():
                if isinstance(val, list):
                    row[key] = "; ".join(val)

            records.append(row)
            print(f"  -> OK: {parsed.titulo_artigo[:60]}...")

        except Exception as e:
            print(f"  -> Erro ao processar {filename}: {e}")

        finally:
            # Remove o arquivo remoto após extração para manter o armazenamento limpo
            client.files.delete(name=uploaded_file.name)
            time.sleep(1)

    if records:
        df = pd.DataFrame(records)
        # Reordena para colocar o nome do arquivo primeiro
        cols = ["arquivo_pdf"] + [c for c in df.columns if c != "arquivo_pdf"]
        df = df[cols]

        df.to_csv(f"{output_prefix}.csv", index=False, encoding="utf-8-sig")
        df.to_excel(f"{output_prefix}.xlsx", index=False)
        print(f"\nExtração concluída! Salvo em {output_prefix}.csv e {output_prefix}.xlsx")


if __name__ == "__main__":
    process_pdfs(pdf_folder="./rpapers_pdf")