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
import configuration
from Database.database_connection import database

mycursor = database.cursor()

def run_component_evaluation(input_file, session_wise=False, equalization=False):

    sql = "SELECT source_extraction_session_wise,min_SNR,alignment_main,equalization_main,motion_correction_main,rval_thr,use_cnn FROM Analysis WHERE source_extraction_main=?"
    val = [input_file, ]
    mycursor.execute(sql, val)
    myresult = mycursor.fetchall()
    data = []
    aux = []
    for x in myresult:
        aux = x
    for y in aux:
        data.append(y)

    if session_wise:
        input_mmap_file_path = data[2]
    elif equalization:
        input_mmap_file_path  = data[3]
    else:
        input_mmap_file_path = data[4]

    parameters = {'min_SNR': data[1],'rval_thr': data[5],'use_cnn': data[6]}

    data_dir = os.environ['DATA_DIR_LOCAL'] + 'data/interim/component_evaluation/session_wise/' if \
    data[0] else os.environ['DATA_DIR_LOCAL'] + 'data/interim/component_evaluation/trial_wise/'

    sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,source_extraction_v,component_evaluation_v,input,home_path,decoding_main FROM Analysis WHERE source_extraction_main=?"
    val = [input_file, ]
    mycursor.execute(sql, val)
    result = mycursor.fetchall()
    data = []
    inter = []
    for x in result:
        inter = x
    for y in inter:
        data.append(y)

    # Update the database

    if data[10] == 0:
        data[10] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}.{data[10]}"
        output_file_path =  f'main/{file_name}.hdf5'
        sql1 = "UPDATE Analysis SET component_evaluation_main=?,component_evaluation_v=? WHERE source_extraction_main=? "
        val1 = [output_file_path, data[10], input_file]
        mycursor.execute(sql1, val1)

    else:
        data[10] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}.{data[9]}.{data[10]}"
        output_file_path =  f'main/{file_name}.hdf5'
        sql2 = "INSERT INTO Analysis (component_evaluation_main,component_evaluation_v) VALUES (?,?)"
        val2 = [output_file_path, data[10]]
        mycursor.execute(sql2, val2)
        database.commit()

    output_file_path_full= data_dir + output_file_path

    # Load CNMF object
    cnm = load_CNMF(input_mmap_file_path)

    # Load the original movie
    Yr, dims, T = cm.load_memmap(input_mmap_file_path)
    images = Yr.T.reshape((T,) + dims, order='F')

    # Set the parmeters
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
    cnm.save(output_file_path_full)

    return output_file_path
