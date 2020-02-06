#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane
"""
#%% Importation

import psutil
import configuration
import caiman as cm

from Steps.decoding import run_decoder as main_decoding
from Steps.cropping import run_cropper as main_cropping
from Steps.equalizer import  run_equalizer as main_equalizing
from Steps.cropping import cropping_segmentation
from Analysis_tools.figures import plot_movie_frame
from Steps.motion_correction import run_motion_correction as main_motion_correction
from Steps.alignment import run_alignment as main_alignment
from Steps.source_extraction import run_source_extraction as main_source_extraction
from Steps.component_evaluation import run_component_evaluation as main_component_evaluation
from Database.database_connection import database
mycursor = database.cursor()

#%% Start a new cluster

n_processes = psutil.cpu_count()
c, dview, n_processes = cm.cluster.setup_cluster(backend='local',n_processes=n_processes,single_thread=False)

def run_steps(n_steps, mouse_number, sessions, init_trial, end_trial, is_rest):

    if steps == 1:
        print('Choose the mouse, session, how many trial and resting or non resting trial you want to analyse')
        mouse_number = int(input("mouse number : "))
        sessions = input(" session : ")
        main_decoding(mouse_number, sessions,'*' , '*')





for session in sessions:
    print(session)
    #%% Decoding
    main_decoding(mouse_number,session,'*','*')
    #%% Cropping
    for i in range(init_trial,end_trial):
        print(i)
        sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
        val = [mouse_number, session, is_rest, decoding_v,1,i]
        mycursor.execute(sql, val)
        var = mycursor.fetchall()
        for x in var:
            mouse_row = x
        cropped_file,cropping_version = main_cropping(mouse_row)

        #%% Motion correction
        motion_correct_file,motion_correction_version = main_motion_correction(cropped_file, parameters_motion_correction,dview)

        #%% Alignment
        aligned_file,alignment_version = main_alignment(motion_correct_file, parameters_alignment, dview)

        #%% Equalization
        equalized_file,equalization_version  = main_equalizing(aligned_file, parameters_equalizer, session_wise= True)

        #%% Source extraction (after alignment and equalization)
        source_extracted_file,source_extraction_version = main_source_extraction(equalized_file, parameters_source_extraction, dview)


#%% Run separately component evaluation

#%% Evaluation
dview.terminate()
for session in [1, 2,4]:
    print(session)
    for cropping_version in [1,2,3,4]:
        print(cropping_version)
        sql = "SELECT source_extraction_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND motion_correction_v=%s AND alignment_v=%s AND source_extraction_v=%s"
        val = [mouse_number, session, is_rest, decoding_v,cropping_version,motion_correction_version,source_extraction_version]
        mycursor.execute(sql, val)
        var = mycursor.fetchall()
        for x in var:
            mouse_row = x
        mouse_row_new = main_component_evaluation(mouse_row, parameters_component_evaluation, session_wise= True)


#%% Run equalization,source extraction

decoding_version = 1
motion_correction_version = 1

for session in [1,2,4]:
    print(session)
    for cropping_version in [1,2,3,4]:
        # Run equalization
        alignment_version = 1
        sql = "SELECT alignment_main FROM Analysis WHERE mouse=%s AND session= %s AND trial=%s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND motion_correction_v=%s AND alignment_v=%s AND source_extraction_v=%s AND "
        val = [mouse_number, session,1, 0, decoding_v, cropping_version, motion_correction_version,
               alignment_version]
        mycursor.execute(sql, val)
        var = mycursor.fetchall()
        for x in var:
            aligned_file = x
        equalized_file = main_equalizing(aligned_file , parameters_equalizer, session_wise= True)

        # All aligned videos are save in one file
        mouse_row_new = main_source_extraction(equalized_file, parameters_source_extraction, dview)
