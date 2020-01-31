#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Melisa,Morgane
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
from Steps.alignment2 import run_alignment as main_alignment
from Steps.source_extraction import run_source_extraction as main_source_extraction
from Steps.component_evaluation import run_component_evaluation as main_component_evaluation
from Database.database_connection import database
mycursor = database.cursor()


#%% Settings
mouse_number = 56165
sessions = [1,2,4]
init_trial = 1
end_trial = 22
is_rest = None
decoding_v=1

#%% Select first data
sql = "SELECT decoding_main FROM Analysis WHERE mouse = %s AND decoding_v=%s"
val = (mouse_number, decoding_v)
mycursor.execute(sql, val)
myresult = mycursor.fetchone()
for x in myresult:
    mouse_row = x
plot_movie_frame(mouse_row)


#%% Parameters for different steps
parameters_motion_correction = {'motion_correct': True, 'pw_rigid': True, 'save_movie_rig': False,
                                'gSig_filt': (5, 5), 'max_shifts': (25, 25), 'niter_rig': 1,
                                'strides': (48, 48),
                                'overlaps': (96, 96), 'upsample_factor_grid': 2, 'num_frames_split': 80,
                                'max_deviation_rigid': 15,
                                'shifts_opencv': True, 'use_cuda': False, 'nonneg_movie': True, 'border_nan': 'copy'}

parameters_alignment = {'make_template_from_trial': '1', 'gSig_filt': (5, 5), 'max_shifts': (25, 25), 'niter_rig': 1,
                        'strides': (48, 48), 'overlaps': (96, 96), 'upsample_factor_grid': 2, 'num_frames_split': 80,
                        'max_deviation_rigid': 15, 'shifts_opencv': True, 'use_cuda': False, 'nonneg_movie': True,
                        'border_nan': 'copy'}

h_step = 10
parameters_equalizer = {'make_template_from_trial': '1', 'equalizer': 'histogram_matching', 'histogram_step': h_step}

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

parameters_component_evaluation = {'min_SNR': 5.5,
                                   'rval_thr': 0.75,
                                   'use_cnn': False}

n_processes = psutil.cpu_count()

#%% Start a new cluster
c, dview, n_processes = cm.cluster.setup_cluster(backend='local',n_processes=n_processes,single_thread=False)


#%% Run for different session

for session in [1,2,4]:
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
