#!/usr/bin/env python3
"""
This script reads Zarr stores from a specified directory, extracts relevant information, 
and writes it to a dsarch input file. The dsarch input file is then used to archive the
Zarr files with the command 'dsarch <dnnnnnn> -if <dsarch_input_file>'.
Usage:
    python create_dsarch_file.py

Ensure that the required dependencies are installed:
    pip install xarray zarr
"""

import os
import logging
from pathlib import Path
import xarray as xr
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dsid = 'd164444'

# Parent directory of model ensemble data and the working directory for dsarch output
data_dir = Path('/glade/campaign/cgd/cas/schwarzwald/bcd_me')
work_dir = os.path.join(os.environ.get('GDEXWORK', '/lustre/desc1/gdex/work'), 'tcram')
output_dir = Path(work_dir) / dsid / 'dsarch'

group_index = '1'
data_format = 'ZARR'
dsarch_headers = {
    'LF': 'LocalFile', 
    'WF': 'WebFile',
    'DF': 'DataFormat',
    'GI': 'GroupIndex',
    'DE': 'Description'
}

def get_zarr_year_range(zarr_store_path):
    """
    Extract the temporal range from the Zarr store's attributes.
    Returns a list [start_year, end_year] if available, otherwise an appropriate message.
    """
    try:
        ds = xr.open_zarr(zarr_store_path)
        years = ds['calendar_year'].values # numpy.ndarray of years
        if years.size > 0:
            start_year = int(np.nanmin(years))
            end_year = int(np.nanmax(years))
            return [start_year, end_year]
        else:
            return f"No time data available in {zarr_store_path}"
    except Exception as e:
        logging.error(f"Error extracting temporal range from {zarr_store_path}: {e}")
        return "Error extracting temporal range"
    
# Iterate through each model directory and read each Zarr store
# Store the model directory name, data format, group index, and description in a dictionary,
# then write the dictionary to the dsarch file as a line of text with the format:
# model_dir_name<:>data_format<:>group_index<:>description<:>

ds_info_list = []

output_dir.mkdir(parents=True, exist_ok=True)
metadata_file = output_dir / 'metadata.txt'
metadataf = open(metadata_file, 'w')

for model_dir in data_dir.iterdir():
    if model_dir.is_dir() and model_dir.name.endswith('.zarr'):
        logging.debug(f'Reading Zarr store: {model_dir}')
        try:
            ds = xr.open_zarr(model_dir)
            logging.info(f'Successfully read Zarr store: {model_dir}')
            # Perform any additional processing on the dataset here
            description = ds.attrs.get('DESCRIPTION', 'No description available')
            ds_info_list.append({
                'model_dir': str(model_dir),
                'zarr_store': str(model_dir.name),
                'data_format': data_format,
                'group_index': group_index,
                'description': description
            })
            metadataf.write(f"{model_dir.name}:\n")
            metadataf.write(f"Temporal range: {get_zarr_year_range(model_dir)}\n")
        except Exception as e:
            logging.error(f'Error reading Zarr store {model_dir}: {e}')

metadataf.write("Min/max temporal range across all Zarr stores:\n")
all_ranges = [get_zarr_year_range(model_dir) for model_dir in data_dir.iterdir() if model_dir.is_dir() and model_dir.name.endswith('.zarr')]
metadataf.write(f"{min(all_ranges)} - {max(all_ranges)}\n")
metadataf.close()

# The zarr store ('zarr_store') naming structure is:
# `bcd_me_[type]_[ESM].zarr`
# With type = 
# `qdm` (1-degree time series by GWL)
# `qdm-byyr` (1-degree time series by year)
# `qdm-qplad` (0.25-degree statistics by GWL)
# and ESM = Earth System Model, e.g. `CESM2`, `GFDL-ESM4`, etc.

# Re-order the ds_info_list based first on type, then alphabetically on the ESM name extracted from the model directory name
def extract_type_and_esm(model_dir_name):
    parts = model_dir_name.replace('.zarr', '').split('_')
    return parts[2], parts[3]

ds_info_list.sort(key=lambda ds_info: extract_type_and_esm(ds_info['zarr_store']))

# Write the collected dataset information to the dsarch file with each column formatted to be as wide as the longest entry in that column
model_dir_width = max(len(ds_info['model_dir']) for ds_info in ds_info_list)
zarr_store_width = max(len(ds_info['zarr_store']) for ds_info in ds_info_list)
data_format_width = max(len(ds_info['data_format']) for ds_info in ds_info_list)
group_index_width = max(len(ds_info['group_index']) for ds_info in ds_info_list)
description_width = max(len(ds_info['description']) for ds_info in ds_info_list)

model_dir_width = max(model_dir_width, len(dsarch_headers['LF']))
zarr_store_width = max(zarr_store_width, len(dsarch_headers['WF']))
data_format_width = max(data_format_width, len(dsarch_headers['DF']))
group_index_width = max(group_index_width, len(dsarch_headers['GI']))
description_width = max(description_width, len(dsarch_headers['DE']))

dsarch_file = output_dir / f'{dsid}.dsarch'
outfile = open(dsarch_file, 'w')
outfile.write(f"Dataset<=>{dsid}\n")
outfile.write("AW<!>\n")
outfile.write("WT<=>D\n")
outfile.write("WC<!>\n")
outfile.write("ON<=>F\n")
outfile.write(f"{'LocalFile':<{model_dir_width}} <:> {'WebFile':<{zarr_store_width}} <:> {'DataFormat':<{data_format_width}} <:> {'GroupIndex':<{group_index_width}} <:> {'Description':<{description_width}} <:>\n")

for ds_info in ds_info_list:
    model_dir = ds_info['model_dir']
    zarr_store = ds_info['zarr_store']
    data_format = ds_info['data_format']
    group_index = ds_info['group_index']
    description = ds_info['description']    

    outfile.write(f"{model_dir:<{model_dir_width}} <:> {zarr_store:<{zarr_store_width}} <:> {data_format:<{data_format_width}} <:> {group_index:<{group_index_width}} <:> {description:<{description_width}} <:>\n")

outfile.close()