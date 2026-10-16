#!/bin/bash


ROOT='/app'
FILES_DIR='./original_ris_files'
FILE_NAME='export_33c5d528-ebbf-4878-96aa-bc4ee1aa5119_2026-10-05T181520.829246286_6'

python3 -u data_retrivel.py "$FILES_DIR" "$FILE_NAME"


# VERSION="6"
# OPTICAL_BANDS="swir1,nir,red,green"
# OPTICAL_INDICES="NDVI,MNDWI"
