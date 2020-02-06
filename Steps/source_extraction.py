# -*- coding: utf-8 -*-

import datetime

import caiman as cm 
from caiman.source_extraction import cnmf
from caiman.source_extraction.cnmf import params as params
import Analysis_tools.analysis_files_manipulation as fm

import caiman.base.rois
import logging

import numpy as np 
import os
import psutil

from Database.database_connection import database

mycursor = database.cursor()

gSig = 5
gSiz = 4 * gSig + 1

parameters_source_extraction = {'equalization': False, 'session_wise': True, 'fr': 10, 'decay_time': 0.1,
                                'min_corr': 0.8,
                                'min_pnr': 7, 'p': 1, 'K': None, 'gSig': (gSig, gSig),
                                'gSiz': (gSiz, gSiz),
                                'merge_thr': 0.7, 'rf': 60, 'stride': 30, 'tsub': 1, 'ssub': 2, 'p_tsub': 1,
                                'p_ssub': 2, 'low_rank_background': None, 'nb': 0, 'nb_patch': 0,
                                'ssub_B': 2,
                                'init_iter': 2, 'ring_size_factor': 1.4, 'method_init': 'corr_pnr',
                                'method_deconvolution': 'oasis', 'update_background_components': True,
                                'center_psf': True, 'border_pix': 0, 'normalize_init': False,
                                'del_duplicates': True, 'only_init': True}

def run_source_extraction(input_mmap_file_path, dview, session_wise = False):
    """
    This is the function for source extraction.
    Its goal is to take in a .mmap file,
    perform source extraction on it using cnmf-e and save the cnmf object as a .pkl file.
    """
    # Determine input path

    if parameters['session_wise']:
        sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,source_extraction_v FROM Analysis WHERE alignment_main=%s "
        val = [input_mmap_file_path, ]
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        data = []
        for x in myresult:
            data += x
        data[5] +=1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[5]}.{data[4]}.{data[5]}.{data[6]}.{data[5]}"
        if parameters['equalization']:
            sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,source_extraction_v FROM Analysis WHERE equalization_main=%s "
            val = [input_mmap_file_path, ]
            mycursor.execute(sql, val)
            myresult = mycursor.fetchall()
            data = []
            for x in myresult:
                data += x
            data[5] += 1
            file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[5]}.{data[4]}.{data[5]}.{data[6]}.{data[5]}"
    else:
        sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,source_extraction_v FROM Analysis WHERE motion_correction_main=%s "
        val = [input_mmap_file_path, ]
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        data = []
        for x in myresult:
            data += x
        data[5] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[5]}.{data[4]}.{data[5]}.{data[6]}.{data[5]}"

    # Determine output paths
    if parameters['session_wise']:
        data_dir = os.environ['DATA_DIR'] + 'data/interim/source_extraction/session_wise/'
    else:
        data_dir = os.environ['DATA_DIR'] + 'data/interim/source_extraction/trial_wise/'
    output_file_path = data_dir + f'main/{file_name}.hdf5'

    # Load memmory mappable input file
    if os.path.isfile(input_mmap_file_path):
        Yr, dims, T = cm.load_memmap(input_mmap_file_path)
        images = Yr.T.reshape((T,) + dims, order='F')
    else:
        logging.warning(' .mmap file does not exist. Cancelling')

    # SOURCE EXTRACTION
    # Check if the summary images are already there
    corr_npy_file_path, pnr_npy_file_path = fm.get_corr_pnr_path(input_mmap_file_path, gSig_abs = parameters['gSig'][0])
    
    if corr_npy_file_path != None and os.path.isfile(corr_npy_file_path):  
        # Already computed summary images
        logging.info(' Already computed summary images')
        cn_filter = np.load(corr_npy_file_path)
        pnr = np.load(pnr_npy_file_path)
    else:
        # Compute summary images
        t0 = datetime.datetime.today()
        logging.info(' Computing summary images')
        cn_filter, pnr = cm.summary_images.correlation_pnr(images[::1], gSig = parameters['gSig'][0], swap_dim=False)
        dt = int((datetime.datetime.today() - t0).seconds/60) # timedelta in minutes
        logging.info(f' Computed summary images. dt = {dt} min')
        # Saving summary images as npy files
        gSig = parameters['gSig'][0]
        corr_npy_file_path = data_dir + f'/meta/corr/{file_name}_gSig_{gSig}.npy'
        pnr_npy_file_path = data_dir + f'/meta/pnr/{file_name}_gSig_{gSig}.npy'
        with open(corr_npy_file_path, 'wb') as f:
            np.save(f, cn_filter)
        with open(pnr_npy_file_path, 'wb') as f:
            np.save(f, pnr)

    # Calculate min, mean, max value for cn_filter and pnr
    corr_min, corr_mean, corr_max = cn_filter.min(), cn_filter.mean(), cn_filter.max()
    pnr_min, pnr_mean, pnr_max = pnr.min(), pnr.mean(), pnr.max()
    # If min_corr and min_pnr are specified via a linear equation, calculate this value
    if type(parameters['min_corr']) == list:
        min_corr = parameters['min_corr'][0]*corr_mean + parameters['min_corr'][1]
        parameters['min_corr'] = min_corr
        logging.info(f' Automatically setting min_corr = {min_corr}')
    if type(parameters['min_pnr']) == list:
        min_pnr =  parameters['min_pnr'][0]*pnr_mean + parameters['min_pnr'][1]
        parameters['min_pnr'] = min_pnr
        logging.info(f' Automatically setting min_pnr = {min_pnr}')

    # Set the parameters for caiman
    opts = params.CNMFParams(params_dict = parameters)   
    
    # SOURCE EXTRACTION 
    logging.info(' Performing source extraction')
    t0 = datetime.datetime.today()
    n_processes = psutil.cpu_count()
    logging.info(f' n_processes: {n_processes}')
    cnm = cnmf.CNMF(n_processes = n_processes, dview = dview, params = opts)
    cnm.fit(images)
    cnm.estimates.dims = dims

    # Calculate the center of masses
    cnm.estimates.center = caiman.base.rois.com(cnm.estimates.A, images.shape[1], images.shape[2])
    
    # Save the cnmf object as a hdf5 file 
    logging.info(f' Saving cnmf object')
    cnm.save(output_file_path)
    dt = int((datetime.datetime.today() - t0).seconds/60) # timedelta in minutes
    logging.info(f' Source extraction finished. dt = {dt} min')
    
    # Write necessary variables in row and return
    sql3 = "UPDATE Analysis SET decoding_main=%s,decoding_v=%s,mouse=%s,session=%s,trial=%s,is_rest=%s WHERE cropping_main=%s AND cropping_v=%s"
    val3 = [input_path, data[5], data[0], data[1], data[2], data[3], output_tif_file_path, data[4]]
    mycursor.execute(sql3, val3)
    database.commit()
    row_local.loc['source_extraction_parameters'] = str(parameters)
    row_local.loc['source_extraction_output'] = str(output)
    output['meta']['corr']['meta'] = {'min': corr_min, 'mean': corr_mean, 'max': corr_max}
    pnr_min, pnr_mean, pnr_max = pnr.min(), pnr.mean(), pnr.max()
    output['meta']['pnr']['meta'] = {'min': pnr_min, 'mean': pnr_mean, 'max': pnr_max}
    # Store the number of neurons
    output['meta']['K'] = len(cnm.estimates.C)
    output['meta']['duration']['source_extraction'] = dt
        
    return output_file_path
