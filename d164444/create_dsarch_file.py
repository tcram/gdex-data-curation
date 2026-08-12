#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging
from pathlib import Path
import xarray as xr

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dsid = 'd164444'

# Parent directory of model ensemble data
data_dir = Path('/glade/campaign/cgd/cas/schwarzwald/bcd_me')
work_dir = os.path.join(os.environ.get('GDEXWORK', '/lustre/desc1/gdex/work'), 'tcram')
output_dir = Path(work_dir) / dsid / 'dsarch'

group_index = '1'
data_format = 'ZARR'
dsarch_headers = {
    'LF': 'LocalFile', 
    'DF': 'DataFormat',
    'GI': 'GroupIndex',
    'DE': 'Description'
}

# Iterate through each model directory and read each Zarr store
# Store the model directory name, data format, group index, and description in a dictionary,
# then write the dictionary to the dsarch file as a line of text with the format:
# model_dir_name<:>data_format<:>group_index<:>description<:>

ds_info_list = []

for model_dir in data_dir.iterdir():
    if model_dir.is_dir() and model_dir.name.endswith('.zarr'):
        logging.info(f'Reading Zarr store: {model_dir}')
        try:
            ds = xr.open_zarr(model_dir)
            logging.info(f'Successfully read Zarr store: {model_dir}')
            # Perform any additional processing on the dataset here
            description = ds.attrs.get('DESCRIPTION', 'No description available')
            logging.info(f'Dataset description: {description}')
            ds_info_list.append({
                'model_dir': str(model_dir),
                'data_format': data_format,
                'group_index': group_index,
                'description': description
            })
            # outfile.write("<:>".join([str(model_dir), data_format, group_index, description]) + "<:>\n")
        except Exception as e:
            logging.error(f'Error reading Zarr store {model_dir}: {e}')

# Write the collected dataset information to the dsarch file with each column formatted to be as wide as the longest entry in that column
model_dir_width = max(len(ds_info['model_dir']) for ds_info in ds_info_list)
data_format_width = max(len(ds_info['data_format']) for ds_info in ds_info_list)
group_index_width = max(len(ds_info['group_index']) for ds_info in ds_info_list)
description_width = max(len(ds_info['description']) for ds_info in ds_info_list)

model_dir_width = max(model_dir_width, len(dsarch_headers['LF']))
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
outfile.write(f"{'LocalFile':<{model_dir_width}} <:> {'DataFormat':<{data_format_width}} <:> {'GroupIndex':<{group_index_width}} <:> {'Description':<{description_width}} <:>\n")

for ds_info in ds_info_list:
    model_dir = ds_info['model_dir']
    data_format = ds_info['data_format']
    group_index = ds_info['group_index']
    description = ds_info['description']    

    outfile.write(f"{model_dir:<{model_dir_width}} <:> {data_format:<{data_format_width}} <:> {group_index:<{group_index_width}} <:> {description:<{description_width}} <:>\n")

outfile.close()