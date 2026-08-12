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
output_dir = Path(work_dir) / dsid

dsarch_file = output_dir / f'{dsid}.dsarch'
group_index = '1'
data_format = 'ZARR'


outfile = open(dsarch_file, 'w')
outfile.write(f"Dataset<=>{dsid}\n")
outfile.write("AW<!>\n")
outfile.write("WT<=>D\n")
outfile.write("WC<!>\n")
outfile.write("ON<=>F\n")
outfile.write("LocalFile                                       <:>DataFormat <:>GroupIndex <:>Description <:>\n")

# Iterate through each model directory and read each Zarr store
for model_dir in data_dir.iterdir():
    if model_dir.is_dir() and model_dir.name.endswith('.zarr'):
        logging.info(f'Reading Zarr store: {model_dir}')
        try:
            ds = xr.open_zarr(model_dir)
            logging.info(f'Successfully read Zarr store: {model_dir}')
            # Perform any additional processing on the dataset here
            description = ds.attrs.get('DESCRIPTION', 'No description available')
            logging.info(f'Dataset description: {description}')
            outfile.write("<:>".join([str(model_dir), data_format, group_index, description]) + "<:>\n")
        except Exception as e:
            logging.error(f'Error reading Zarr store {model_dir}: {e}')

outfile.close()