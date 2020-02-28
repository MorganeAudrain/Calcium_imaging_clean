# -*- coding: utf-8 -*-

import caiman as cm
from caiman.source_extraction import cnmf
from caiman.source_extraction.cnmf import params as params
import datetime
import caiman.base.rois
import logging
import configuration
import numpy as np
import os
import psutil

from Database.database_connection import database

cursor = database.cursor()


def run_source_extraction(input_file, dview):
    """
    This is the function for source extraction.
    Its goal is to take in a .mmap file,
    perform source extraction on it using cnmf-e and save the cnmf object as a .pkl file.
    """

    sql = "SELECT equalization,source_extraction_session_wise,fr,decay_time,min_corr,min_pnr,p,K,gSig,merge_thr,rf,stride,tsub,ssub,p_tsub,p_ssub,low_rank_background,nb,nb_patch,ssub_B,init_iter,ring_size_factor,method_init,method_deconvolution,update_background_components,center_psf,border_pix,normalize_init,del_duplicates,only_init  FROM Analysis WHERE motion_correction_main =?  OR alignment_main = ? OR equalization_main =?"
    val = [input_file, input_file, input_file]
    cursor.execute(sql, val)
    result = cursor.fetchall()
    para = []
    inter = []
    for x in result:
        inter = x
    for y in inter:
        para.append(y)
    gSiz = 4 * para[8] + 1
    parameters = {'equalization': para[0], 'session_wise': para[1], 'fr': para[2], 'decay_time': para[3],
                  'min_corr': para[4],
                  'min_pnr': para[5], 'p': para[6], 'K': para[7], 'gSig': (para[8], para[8]),
                  'gSiz': (gSiz, gSiz),
                  'merge_thr': para[9], 'rf': para[10], 'stride': para[11], 'tsub': para[12], 'ssub': para[13],
                  'p_tsub': para[14],
                  'p_ssub': para[15], 'low_rank_background': para[16], 'nb': para[17], 'nb_patch': para[18],
                  'ssub_B': para[19],
                  'init_iter': para[20], 'ring_size_factor': para[21], 'method_init': para[22],
                  'method_deconvolution': para[23], 'update_background_components': para[24],
                  'center_psf': para[25], 'border_pix': para[26], 'normalize_init': para[27],
                  'del_duplicates': para[28], 'only_init': para[29]}
    # Determine output paths

    if parameters['session_wise']:
        data_dir = os.environ['DATA_DIR_LOCAL'] + 'data/interim/source_extraction/session_wise/'
    else:
        data_dir = os.environ['DATA_DIR_LOCAL'] + 'data/interim/source_extraction/trial_wise/'

    sql1 = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,source_extraction_v,input,home_path,decoding_main FROM Analysis WHERE  motion_correction_main =?  OR alignment_main = ? OR equalization_main =?"
    val1 = [input_file, input_file, input_file]
    cursor.execute(sql1, val1)
    result = cursor.fetchall()
    data = []
    inter = []
    for x in result:
        inter = x
    for y in inter:
        data.append(y)

    # Update the database

    if data[9] == 0:
        data[9] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}"
        output_file_path = data_dir + f'main/{file_name}.hdf5'
        sql1 = "UPDATE Analysis SET source_extraction_main=?,source_extraction_v=? WHERE  motion_correction_main =?  OR alignment_main = ? OR equalization_main =? "
        val1 = [output_file_path, data[9], input_file, input_file, input_file]
        cursor.execute(sql1, val1)

    else:
        data[9] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}"
        output_file_path = data_dir + f'main/{file_name}.hdf5'
        sql2 = "INSERT INTO Analysis (source_extraction_main,source_extraction_v) VALUES (?,?)"
        val2 = [output_file_path, data[10]]
        cursor.execute(sql2, val2)
        database.commit()

    database.commit()

    # Load memmory mappable input file
    if os.path.isfile(input_file):
        Yr, dims, T = cm.load_memmap(input_file)
        images = Yr.T.reshape((T,) + dims, order='F')
    else:
        logging.warning(f' .mmap file does not exist. Cancelling')


    # SOURCE EXTRACTION
    # Check if the summary images are already there
    corr_npy_file_path, pnr_npy_file_path = get_corr_pnr_path(gSig_abs=parameters['gSig'][0])

    if corr_npy_file_path != None and os.path.isfile(corr_npy_file_path):
        # Already computed summary images
        logging.info(f' Already computed summary images')
        cn_filter = np.load(corr_npy_file_path)
        pnr = np.load(pnr_npy_file_path)
    else:
        # Compute summary images
        t0 = datetime.datetime.today()
        logging.info(f' Computing summary images')
        cn_filter, pnr = cm.summary_images.correlation_pnr(images[::1], gSig=parameters['gSig'][0], swap_dim=False)
        dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
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

    # If min_corr and min_pnr are specified via a linear equation, calculate
    # this value
    if type(parameters['min_corr']) == list:
        min_corr = parameters['min_corr'][0] * corr_mean + parameters['min_corr'][1]
        parameters['min_corr'] = min_corr
        logging.info(f' Automatically setting min_corr = {min_corr}')
    if type(parameters['min_pnr']) == list:
        min_pnr = parameters['min_pnr'][0] * pnr_mean + parameters['min_pnr'][1]
        parameters['min_pnr'] = min_pnr
        logging.info(f' Automatically setting min_pnr = {min_pnr}')

    # Set the parameters for caiman
    opts = params.CNMFParams(params_dict=parameters)

    # SOURCE EXTRACTION
    logging.info(f' Performing source extraction')
    t0 = datetime.datetime.today()
    n_processes = psutil.cpu_count()
    logging.info(f' n_processes: {n_processes}')
    cnm = cnmf.CNMF(n_processes=n_processes, dview=dview, params=opts)
    cnm.fit(images)
    cnm.estimates.dims = dims

    # Calculate the center of masses
    cnm.estimates.center = caiman.base.rois.com(cnm.estimates.A, images.shape[1], images.shape[2])

    # Save the cnmf object as a hdf5 file
    logging.info(f' Saving cnmf object')
    cnm.save(output_file_path)
    dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
    logging.info(f' Source extraction finished. dt = {dt} min')

    sql1 = "UPDATE Analysis SET duration_summary_images=?,source_extraction_corr=?, source_extraction_pnr=?, source_extraction_corr_min =?, source_extraction_corr_mean=?, source_extraction_corr_max=?, source_extraction_pnr_min=?,source_extraction_pnr_mean=?,source_extraction_pnr_max=?,source_extraction_k=?,source_extraction_duration=?,min_corr=?,min_pnr=? WHERE source_extraction_main= ? AND source_extraction_v=? "
    val1 = [dt, corr_npy_file_path, pnr_npy_file_path, corr_min, corr_mean, corr_max, pnr_min, pnr_mean, pnr_max,
            len(cnm.estimates.C), dt, output_file_path, data[9]]
    cursor.execute(sql1, val1)

    return output_file_path, data[9]


def get_corr_pnr_path(gSig_abs=None):
    os.chdir(os.environ['DATA_DIR_LOCAL'])
    corr_dir = 'data/interim/source_extraction/trial_wise/meta/corr'
    corr_path = None
    for path in os.listdir(corr_dir):
            if gSig_abs == None:
                corr_path = os.path.join(corr_dir, path)
            else:
                if path[-5] == str(gSig_abs):
                    corr_path = os.path.join(corr_dir, path)
    pnr_dir = 'data/interim/source_extraction/trial_wise/meta/pnr'
    pnr_path = None
    for path in os.listdir(pnr_dir):
            if gSig_abs == None:
                pnr_path = os.path.join(pnr_dir, path)
            else:
                if path[-5] == str(gSig_abs):
                    pnr_path = os.path.join(pnr_dir, path)

    return corr_path, pnr_path

