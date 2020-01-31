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

def run_component_evaluation(file, parameters, set_version = None, session_wise = False, equalization = False):

    sql = "SELECT source_extraction_hdf5_file,source_extraction_mmap_file,source_extraction_session_wise,source_extraction_trial_wise,mouse,session,trial,is_rest,cropping_v,decoding_v,motion_correction_v,source_extraction_v,equalization_v,alignment_v,component_evaluation_v FROM Analysis WHERE motion_correction_main=%s"
    val = [file,]
    mycursor.execute(sql, val)
    var = mycursor.fetchall()
    data=[]
    for x in var:
        data += x
    input_hdf5_file_path = data[0]
    input_mmap_file_path = data[1]
    data_dir = os.environ['DATA_DIR'] + 'data/interim/component_evaluation/session_wise/' if data[2] else os.environ['DATA_DIR'] + 'data/interim/component_evaluation/trial_wise/'
    file_name = f"mouse_{data[4]}_session_{data[5]}_trial_{data[6]}.{data[7]}.v{data[8]}.{data[9]}.{data[10]}.{data[11]}.{data[12]}.{data[13]}"
    output_file_path = data_dir + f'main/{file_name}.hdf5'
    component_evaluation_v= data[14]

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
                                                     n_processes=n_processes,  # number of process to use, if you go out of memory try to reduce this one
                                                     single_thread=False)
    # Evaluate components
    cnm.estimates.evaluate_components(images, cnm.params, dview=dview)

    logging.debug('Number of total components: ', len(cnm.estimates.C))
    logging.debug('Number of accepted components: ', len(cnm.estimates.idx_components))
    
    # Stop the cluster
    dview.terminate()

    # Save CNMF object
    cnm.save(output_file_path)
    component_evaluation_v +=1

    sql2 = "UPDATE Analysis SET component_evaluation_main=%s,component_evaluation_v=%s WHERE motion_correction_main=%s  "
    val2 = [output_file_path, component_evaluation_v]
    mycursor.execute(sql2,val2)
    database.commit()

    return output_file_path
