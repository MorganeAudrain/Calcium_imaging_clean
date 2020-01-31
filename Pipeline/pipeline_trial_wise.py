#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Melisa,Morgane
"""

import os
import psutil
import configuration
import caiman as cm

from Steps.decoding import run_decoder as main_decoding
from Steps.cropping import run_cropper as main_cropping
from steps.equalizer import  run_equalizer as main_equalizing
from Steps.cropping import cropping_segmentation
from analysis.figures import plot_movie_frame
from Steps.motion_correction import run_motion_correction as main_motion_correction
from steps.alignment2 import run_alignmnet as main_alignment
from steps.source_extraction import run_source_extraction as main_source_extraction
from steps.component_evaluation import run_component_evaluation as main_component_evaluation


# Paths
analysis_states_database_path = paths.analysis_states_database_path
backup_path = os.environ['PROJECT_DIR'] +  'references/analysis/backup/'
states_df = db.open_analysis_states_database(path = analysis_states_database_path)

mouse_number = 56165
sessions = [1,2,4]
init_trial = 1
end_trial = 22
is_rest = None

#  Select first data
selected_rows = db.select(states_df, 'decoding', mouse=mouse_number, is_rest=is_rest, decoding_v= 1)
mouse_row = selected_rows.iloc[0]
#mouse_row = main_decoding(mouse_row)
plot_movie_frame(mouse_row)

# select cropping parameters
parameters_cropping = cropping_interval()  # check whether it is better to do it like this or to use the functions get
# and set parameters from the data_base_manipulation file
parameters_cropping['segmentation'] = True
parameters_cropping_list = cropping_segmentation(parameters_cropping)

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
##sesion wise paramenters
parameters_source_extraction = {'equalization': False, 'session_wise': False, 'fr': 10, 'decay_time': 0.1,
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

##trial_wise_parameters
parameters_source_extraction = {'equalization': False, 'session_wise': False, 'fr': 10, 'decay_time': 0.1,
                                'min_corr': 0.6,
                                'min_pnr': 4, 'p': 1, 'K': None, 'gSig': (gSig, gSig),
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


parameters_component_evaluation = {'min_SNR': 4,
                                   'rval_thr': 0.6,
                                   'use_cnn': False}

n_processes = psutil.cpu_count()
#cm.cluster.stop_server()
# Start a new cluster
c, dview, n_processes = cm.cluster.setup_cluster(backend='local',
                                                 n_processes=n_processes,
                                                 single_thread=False)


for session in [1,2,4]:
    print(session)
    # Run decoding for group of data tha have the same cropping parameters (same mouse)
    selection = selected_rows.query('(session ==' + f'{session}' + ')')
    #for i in range(init_trial,end_trial):
    #    print(i)
    #    selection = selected_rows.query('(trial ==' + f'{i}' + ')')
    #    for j in range(len(selection)):
    #        mouse_row = selection.iloc[j]
    #        mouse_row = main_decoding(mouse_row)
    #        states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row)
    #        db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)

    decoding_version = mouse_row.name[4]
    # Run cropping for the already decoded group

    for parameters_cropping in parameters_cropping_list:
        selected_rows = db.select(states_df,'cropping',mouse = mouse_number,session=session, is_rest=is_rest,
                                  decoding_v = decoding_version,
                                  cropping_v= 0 )

        for i in range(init_trial,end_trial):
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row = main_cropping(mouse_row, parameters_cropping)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row)
                db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)

        cropping_version = mouse_row.name[5] # set the cropping version to the one currently used
        # Select rows to be motion corrected using current version of cropping, define motion correction parameters
        # (refer to parameter_setting_motion_correction)
        selected_rows = db.select(states_df,'motion_correction',mouse = mouse_number,session=session, is_rest=is_rest,
                                  decoding_v = decoding_version,
                                  cropping_v= cropping_version,
                                  motion_correction_v= 0)
        for i in range(init_trial,end_trial):
            print(i)
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row = main_motion_correction(mouse_row, parameters_motion_correction,dview)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row)
                db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)

        motion_correction_version = mouse_row.name[6]
        # alignment
        selected_rows = db.select(states_df,'alignment',mouse = mouse_number, session = session, is_rest= is_rest,
                                  decoding_v= decoding_version,
                                  cropping_v = cropping_version,
                                  motion_correction_v = motion_correction_version,
                                  alignment_v= 0)

        selected_rows = main_alignment(selected_rows, parameters_alignment, dview)
        for i in range(len(selected_rows)):
            new_index = db.replace_at_index1(selected_rows.iloc[i].name, 4 + 3, 1)
            row_new = selected_rows.iloc[i].copy()
            row_new.name = new_index
            states_df = db.append_to_or_merge_with_states_df(states_df, row_new)
            db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)
        alignment_version = row_new.name[7]

        #Run equalization
        #selected_rows = db.select(states_df,'alignment',mouse = mouse_number,session=session, trial = 1, is_rest=0,
        #                          decoding_v= decoding_version,
        #                          cropping_v = cropping_version,
        #                          motion_correction_v=motion_correction_version,
        #                         alignment_v=alignment_version)
        #states_df = main_equalizing(selected_rows, states_df, parameters_equalizer, session_wise= True)
        #db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)

        #SOURCE EXTRACTION IN INDIVIDUAL FILES
        selected_rows = db.select(states_df,'source_extraction',mouse = mouse_number, session = session, is_rest= is_rest,
                                  decoding_v = decoding_version,
                                  cropping_v = cropping_version,
                                  motion_correction_v = motion_correction_version,
                                  alignment_v= alignment_version,
                                  source_extraction_v=0)

        for i in range(init_trial,end_trial):
            print(i)
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row_new = main_source_extraction(mouse_row, parameters_source_extraction, dview)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row_new)
                db.save_analysis_states_database(states_df, path=analysis_states_database_path, backup_path=backup_path)

        source_extraction_version = mouse_row_new.name[8]

#%% run separately component evaluation

# evaluation
decoding_version = 1
for session in [2,4]:
    print(session)
    # Run decoding for group of data tha have the same cropping parameters (same mouse)
    selection = selected_rows.query('(session ==' + f'{session}' + ')')
    for cropping_version in [1,2,3,4]:
        print(cropping_version)
        selected_rows = db.select(states_df,'component_evaluation',mouse = mouse_number, session = session, is_rest= is_rest,
                                  decoding_v= decoding_version,
                                  cropping_v = cropping_version,
                                  motion_correction_v = 100,
                                  alignment_v= 0,
                                  source_extraction_v=1)
        for i in range(init_trial,end_trial):
            print(i)
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row_new = main_component_evaluation(mouse_row, parameters_component_evaluation)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row_new)
                db.save_analysis_states_database(states_df, path=analysis_states_database_path, backup_path = backup_path)

##########


decoding_version = 1
session = 1
cropping_version = 1
alignment_version = 1

for session in [1,2,4]:
    print(session)
    # Run decoding for group of data tha have the same cropping parameters (same mouse)
    selection = selected_rows.query('(session ==' + f'{session}' + ')')
    # Run cropping for the already decoded group
    for cropping_version in [1,2,3,4]:
        selected_rows = db.select(states_df, 'motion_correction', mouse=mouse_number, session=session, is_rest=is_rest,
                                  decoding_v=decoding_version,
                                  cropping_v=cropping_version,
                                  motion_correction_v=0)
        for i in range(init_trial, end_trial):
            print(i)
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row = main_motion_correction(mouse_row, parameters_motion_correction, dview)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row)
                db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)
                print(mouse_row.name)
        #Run alignment
        alignment_version = 0
        selected_rows = db.select(states_df,'alignment',mouse = mouse_number,session=session,
                                  decoding_v= decoding_version,
                                  cropping_v = cropping_version,
                                  motion_correction_v=1,
                                  alignment_v=alignment_version)
        new_selected_rows = main_alignment(selected_rows, parameters_alignment, dview)
        for i in range(len(new_selected_rows)):
            new_index = db.replace_at_index1(new_selected_rows.iloc[i].name, 4 + 3, 1)
            row_new = selected_rows.iloc[i].copy()
            row_new.name = new_index
            new_index = db.replace_at_index1(selected_rows.iloc[i].name, 4 + 2, 200)
            row_new.name = new_index
            states_df = db.append_to_or_merge_with_states_df(states_df, row_new)
            db.save_analysis_states_database(states_df, analysis_states_database_path, backup_path)
        alignment_version = row_new.name[7]
        #mouse_row_new = main_equalizing(selected_rows, states_df, parameters_equalizer, session_wise= True)
        #states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row_new)
        #db.save_analysis_states_database(states_df, path=a        #SOURCE EXTRACTION IN ALIGNED (AND EQUALIZED FILES)
        selected_rows = db.select(states_df,'source_extraction',mouse = mouse_number, session = session, is_rest= is_rest,
                                  decoding_v = decoding_version,
                                  cropping_v = cropping_version,
                                  motion_correction_v = 100,
                                  alignment_v= 0,
                                  source_extraction_v=0)
        for i in range(init_trial,end_trial):
            print(i)
            selection = selected_rows.query('(trial ==' + f'{i}' + ')')
            for j in range(len(selection)):
                mouse_row = selection.iloc[j]
                mouse_row_new = main_source_extraction(mouse_row, parameters_source_extraction, dview)
                states_df = db.append_to_or_merge_with_states_df(states_df, mouse_row_new)
                db.save_analysis_states_database(states_df, path=analysis_states_database_path, backup_path=backup_path)
        source_extraction_version = mouse_row_new.name[8]
