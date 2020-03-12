#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane
"""
# %% Importation

import configuration

from Steps.decoding import run_decoder as main_decoding
from Steps.cropping import run_cropper as main_cropping
from Steps.equalizer import run_equalizer as main_equalizing
from Steps.motion_correction import run_motion_correction as main_motion_correction
from Steps.alignment import run_alignment as main_alignment
from Steps.source_extraction import run_source_extraction as main_source_extraction
from Steps.component_evaluation import run_component_evaluation as main_component_evaluation
from Steps.registering import run_registration as main_registration
from Steps.cropping import cropping_interval
from Steps.cropping import cropping_segmentation
from Database.database_connection import database

mycursor = database.cursor()


def run_steps(n_steps, mouse_number, sessions, init_trial, end_trial, dview):
    """
    Function link with pipeline session wise for run every steps, or choose which steps you want to run
    Args:
        n_steps: which steps you want to run
        mouse_number: the mouse that you want to analyse
        sessions: sessions that you want to analyse
        init_trial: first trial to analyse
        end_trial: trial of the end of the analyse
        is_rest: resting or non resting period

    """
    # Decoding
    if n_steps == '0':
        for session in sessions:
            for trial in range(init_trial, (end_trial+1)):
                    main_decoding(mouse_number, session, trial)

    # Cropping
    if n_steps == '1':
        print("You can choose the decoding version that you want to crop if you don't want to choose one particular enter None and the default value will be 1")
        decoding_v = input(" decoding version : ")
        if decoding_v == 'None':
            decoding_v=1
        else:
            decoding_v=int(decoding_v)
        print('Choose the cropping section for this mouse')
        parameters_cropping = cropping_interval(mouse_number)
        parameters_cropping_list = cropping_segmentation(parameters_cropping)
        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    for parameters_cropping in parameters_cropping_list:
                        sql = "SELECT decoding_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? AND decoding_v= ?"
                        val = [mouse_number, session, is_rest, i, decoding_v]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        for x in var:
                            mouse_row = x
                        main_cropping(mouse_row[0],parameters_cropping)

    # Motion correction
    if n_steps == '2':
        print("You can choose the cropping version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        cropping_v = input(" cropping version : ")

        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if cropping_v == 'None':
                        sql = "SELECT cropping_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY cropping_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql,val)
                        var = mycursor.fetchall()
                        cropping_v=[]
                        for x in var:
                            cropping_v = x
                        cropping_v=cropping_v[0]
                    else:
                        cropping_v = int(cropping_v)
                    sql = "SELECT cropping_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND cropping_v=? AND trial=?"
                    val = [mouse_number, session, is_rest, cropping_v, i]
                    mycursor.execute(sql, val)
                    var = mycursor.fetchall()
                    for x in var:
                        mouse_row = x
                    main_motion_correction(mouse_row[0],dview)

    # Alignment
    if n_steps == '3':
        print(
            "You can choose the motion correction version and the cropping version that you want to equalize, for this step you should always choose an version")
        motion_correction_v = input(" motion correction version : ")
        cropping_v=input("cropping version:")
        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if cropping_v == 'None':
                        sql = "SELECT cropping_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY cropping_v"
                        val = [mouse_number, session, is_rest, cropping_v, i]
                        mycursor.execute(sql,val)
                        var = mycursor.fetchall()
                        cropping_v=[]
                        for x in var:
                            cropping_v = x
                        cropping_v=cropping_v[0]
                    else:
                        cropping_v = int(cropping_v)
                    if motion_correction_v == 'None':
                        sql = "SELECT motion_correction_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY motion_correction_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql,val)
                        var = mycursor.fetchall()
                        motion_correction_v=[]
                        for x in var:
                            motion_correction_v = x
                        motion_correction_v=motion_correction_v[0]
                    else:
                        motion_correction_v = int(motion_correction_v)
                    main_alignment(mouse_number, sessions, motion_correction_v, cropping_v, dview)

    # Equalization
    if n_steps == '4':
        print(
            "You can choose the motion correction version and the alignment version that you want to equalize if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        motion_correction_v = input(" motion correction version : ")
        alignment_v = input('alignment version:')


        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if motion_correction_v == 'None':
                        sql = "SELECT motion_correction_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY motion_correction_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql,val)
                        var = mycursor.fetchall()
                        motion_correction_v=[]
                        for x in var:
                            motion_correction_v = x
                        motion_correction_v=motion_correction_v[0]
                    else:
                        motion_correction_v = int(motion_correction_v)
                    if alignment_v == 'None':
                        sql = "SELECT alignment_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY alignment_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        alignment_v = []
                        for x in var:
                            alignment_v = x
                        alignment_v = alignment_v[0]
                    else:
                        alignment_v = int(alignment_v)
                    if alignment_v == 0:
                        sql = "SELECT motion_correction_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=?  AND trial=?"
                        val = [mouse_number, session, is_rest, motion_correction_v, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        for x in var:
                            mouse_row = x
                        main_equalizing(mouse_row[0], dview)
                    else:
                        sql = "SELECT alignment_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=? AND alignment_v =? AND trial=?"
                        val = [mouse_number, session, is_rest, motion_correction_v, alignment_v, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        for x in var:
                            mouse_row = x
                        main_equalizing(mouse_row[0], dview)
    # Source extraction
    if n_steps == '5':
        print(
            "You can choose the motion correction version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        motion_correction_v = input(" motion correction version : ")
        print(
            "You can choose the alignment version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        alignment_v = input(" alignment version : ")
        print(
            "You can choose the equalization version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        equalization_v = input(" equalization version : ")
        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if motion_correction_v == 'None':
                        sql = "SELECT motion_correction_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY motion_correction_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        motion_correction_v = []
                        for x in var:
                            motion_correction_v = x
                        motion_correction_v = motion_correction_v[0]
                    else:
                        motion_correction_v = int(motion_correction_v)
                    if alignment_v == 'None':
                        sql = "SELECT alignment_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY alignment_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        alignment_v = []
                        for x in var:
                            alignment_v = x
                        alignment_v = alignment_v[0]
                    else:
                        alignment_v = int(alignment_v)
                    if equalization_v == 'None':
                        sql = "SELECT equalization_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY equalization_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        equalization_v = []
                        for x in var:
                            equalization_v = x
                        equalization_v = equalization_v[0]
                    else:
                        equalization_v = int(equalization_v)
                    if alignment_v == 0:
                        if equalization_v ==0:
                            sql = "SELECT motion_correction_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=?  AND trial=?"
                            val = [mouse_number, session, is_rest, motion_correction_v, i]
                            mycursor.execute(sql, val)
                            var = mycursor.fetchall()
                            for x in var:
                                mouse_row = x
                            main_source_extraction(mouse_row[0], dview)
                        else:
                            sql = "SELECT equalization_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=? AND equalization_v = ? AND trial=?"
                            val = [mouse_number, session, is_rest, motion_correction_v, equalization_v, i]
                            mycursor.execute(sql, val)
                            var = mycursor.fetchall()
                            for x in var:
                                mouse_row = x
                            main_source_extraction(mouse_row[0], dview)

                    else:
                        if equalization_v == 0:
                            sql = "SELECT alignment_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=? AND alignment_v =?AND trial=?"
                            val = [mouse_number, session, is_rest, motion_correction_v,alignment_v, i]
                            mycursor.execute(sql, val)
                            var = mycursor.fetchall()
                            for x in var:
                                mouse_row = x
                            main_source_extraction(mouse_row[0], dview)

                        else:
                            sql = "SELECT equalization_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND motion_correction_v=? AND equalization_v = ? AND alignment_v=? AND trial=?"
                            val = [mouse_number, session, is_rest, motion_correction_v, equalization_v,alignment_v, i]
                            mycursor.execute(sql, val)
                            var = mycursor.fetchall()
                            for x in var:
                                mouse_row = x
                            main_source_extraction(mouse_row[0], dview)
    # Component Evaluation
    if n_steps == '6':
        print(
            "You can choose the source extraction version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        source_extraction_v = input(" source extraction version : ")

        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if source_extraction_v == 'None':
                        sql = "SELECT source_extraction_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY source_extraction_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        source_extraction = []
                        for x in var:
                            source_extraction= x
                        source_extraction_v = source_extraction[0]
                    else:
                        source_extraction_v = int(source_extraction_v)
                    sql = "SELECT source_extraction_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND source_extraction_v=? AND trial=?"
                    val = [mouse_number, session, is_rest, source_extraction_v, i]
                    mycursor.execute(sql, val)
                    var = mycursor.fetchall()
                    for x in var:
                        mouse_row = x
                    main_component_evaluation(mouse_row[0])

    # Registration
    if n_steps == '7':
        print(
            "You can choose the component evaluation version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        component_evaluation_v = input(" source extraction version : ")
        for session in sessions:
            for i in range(init_trial, (end_trial+1)):
                for is_rest in range(0,2):
                    if component_evaluation_v == 'None':
                        sql = "SELECT component_evaluation_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? ORDER BY component_evaluation_v"
                        val = [mouse_number, session, is_rest, i]
                        mycursor.execute(sql, val)
                        var = mycursor.fetchall()
                        component_evaluation = []
                        for x in var:
                            component_evaluation= x
                        component_evaluation_v = component_evaluation[0]
                    else:
                        component_evaluation_v = int(component_evaluation_v)
                    sql = "SELECT component_evaluation_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=?  AND component_evaluation_v=? AND trial=?"
                    val = [mouse_number, session, is_rest, component_evaluation_v, i]
                    mycursor.execute(sql, val)
                    var = mycursor.fetchall()
                    for x in var:
                        mouse_row = x
                    main_registration(mouse_row[0])
    # Every steps
    if n_steps == 'all':
        for session in sessions:
            for trial in range(init_trial, (end_trial+1)):
                for is_rest in range(0, 2):
                    # Decoding
                    decoded_file = main_decoding(mouse_number, session, trial)

                    # Cropping
                    parameters_cropping = cropping_interval(mouse_number)
                    parameters_cropping_list = cropping_segmentation(parameters_cropping)
                    for parameters_cropping_re in parameters_cropping_list:
                        cropped_file, cropping_version = main_cropping(decoded_file,parameters_cropping_re)

                    # Motion correction
                    motion_correct_file, motion_correction_version = main_motion_correction(cropped_file, dview)

                    # Alignment
                    aligned_file, alignment_version = main_alignment(mouse_number,sessions, motion_correction_version, cropping_version, dview)

                    # Equalization
                    equalized_file, equalization_version = main_equalizing(aligned_file, session_wise=True)

                    # Source extraction
                    source_extracted_file, source_extraction_version = main_source_extraction(equalized_file, dview)

                    # Component evaluation
                    component_evaluated_file=main_component_evaluation(source_extracted_file, session_wise=True)

                    # Registration
                    main_registration(component_evaluated_file)
