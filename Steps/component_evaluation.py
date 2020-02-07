# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@author: Sebastian,Casper,Melisa,Morgane
"""

import caiman as cm
import psutil
from caiman.source_extraction.cnmf.cnmf import load_CNMF
import logging
import os

from Database.database_connection import database

mycursor = database.cursor()


def run_component_evaluation(file, set_version=None, session_wise=False, equalization=False):
    """
    This function is the one which evaluate if the previous extracted component are acceptable component or not
    Args:
        file: file that need to be evaluate
        set_version: version of component evaluation
        session_wise: if the we want to do the evaluation session wise or trial wise
        equalization: if the component evaluation is after equalization or not

    Returns:

    """
    sql = "SELECT mouse,session,trial,is_rest,cropping_v,decoding_v,motion_correction_v,source_extraction_v,equalization_v,alignment_v,component_evaluation_v,source_extraction_hdf5_file,source_extraction_mmap_file,source_extraction_session_wise,source_extraction_trial_wise,min_SNR,rval_thr,use_cnn FROM Analysis WHERE VALUES(?)"
    val = [file, ]
    mycursor.execute(sql, val)
    var = mycursor.fetchall()
    data = []
    inter = []
    for x in var:
        inter = x
    for y in inter:
        data.append(y)

    input_hdf5_file_path = data[0]
    input_mmap_file_path = data[1]
    data_dir = 'data/interim/component_evaluation/session_wise/' if data[13] else os.environ['DATA_DIR'] + 'data/interim/component_evaluation/trial_wise/'
    file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}"
    output_file_path = data_dir + f'main/{file_name}.hdf5'
    component_evaluation_v = data[10]

    # Update the database

    if data[10] == 0:
        data[10] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}.{data[10]}"
        output_meta_pkl_file_path = f'meta/metrics/{file_name}.pkl'
        sql1 = "UPDATE Analysis SET motion_correction_meta=?,motion_correction_v=? WHERE cropping_main=? "
        val1 = [output_meta_pkl_file_path, data[6], cropping_file]
        mycursor.execute(sql1, val1)

    else:
        data[10] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}"
        output_meta_pkl_file_path = f'meta/metrics/{file_name}.pkl'
        sql2 = "INSERT INTO Analysis (motion_correction_meta,motion_correction_v) VALUES (?,?)"
        val2 = [output_meta_pkl_file_path, data[6]]
        mycursor.execute(sql2, val2)
        database.commit()
        sql3 = "UPDATE Analysis SET decoding_main=?,decoding_v=?,mouse=?,session=?,trial=?,is_rest=?,input=?,home_path=?,cropping_v=?,cropping_main=? WHERE motion_correction_meta=? AND motion_correction_v=?"
        val3 = [data[9], data[4], data[0], data[1], data[2], data[3], data[7], data[8], data[5], cropping_file,
                output_meta_pkl_file_path, data[6]]
        mycursor.execute(sql3, val3)
    database.commit()
    output_file_path_full = os.environ['DATA_DIR'] + output_file_path
    parameters = {'min_SNR': data[15],
                  'rval_thr': data[16],
                  'use_cnn': data[17]}

    # Load CNMF object
    cnm = load_CNMF(input_hdf5_file_path)

    # Load the original movie
    Yr, dims, T = cm.load_memmap(input_mmap_file_path)
    images = Yr.T.reshape((T,) + dims, order='F')

    # Set the parameters
    cnm.params.set('quality', parameters)

    # Stop the cluster if one exists
    n_processes = psutil.cpu_count()
    try:
        cm.cluster.stop_server()
    except:
        pass

    # Start a new cluster
    c, dview, n_processes = cm.cluster.setup_cluster(backend='local',
                                                     n_processes=n_processes,
                                                     # number of process to use, if you go out of memory try to reduce this one
                                                     single_thread=False)
    # Evaluate components
    cnm.estimates.evaluate_components(images, cnm.params, dview=dview)

    logging.debug('Number of total components: ', len(cnm.estimates.C))
    logging.debug('Number of accepted components: ', len(cnm.estimates.idx_components))

    # Stop the cluster
    dview.terminate()

    # Save CNMF object
    cnm.save(output_file_path)
    component_evaluation_v += 1

    sql2 = "UPDATE Analysis SET component_evaluation_main=%s,component_evaluation_v=%s WHERE motion_correction_main=%s  "
    val2 = [output_file_path, component_evaluation_v]
    mycursor.execute(sql2, val2)
    database.commit()

    return output_file_path_full
