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
from Database.database_connection import database

mycursor = database.cursor()


def run_steps(n_steps, mouse_number, sessions, init_trial, end_trial, is_rest,dview):
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
            for trial in range(init_trial, end_trial):
                main_decoding(mouse_number, session, trial, is_rest)

    # Cropping
    if n_steps == '1':

        print("You can choose the decoding version that you want to crop if you don't want to choose one particular enter None and the default value will be 1")
        decoding_v = input(" decoding version : ")
        if decoding_v == 'None':
            decoding_v=1
        else:
            decoding_v=int(decoding_v)
        for session in sessions:
            for i in range(init_trial, end_trial):
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND trial=? AND decoding_v= ?"
                val = [mouse_number, session, is_rest, i, decoding_v]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()
                for x in var:
                    mouse_row = x
                main_cropping(mouse_row)

    # Motion correction
    if n_steps == '2':
        print("You can choose the cropping version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        cropping_v = input(" cropping version : ")

        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=? AND session= ? AND is_rest=? AND decoding_v=? AND trial=? ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]
                    mycursor.execute(sql,val)
                    var = mycursor.fetchall()
                    cropping_v=[]
                    for x in var:
                        cropping_v = x
                    cropping_v=cropping_v[0]
                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT cropping_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, cropping_v, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()

    # Alignment
    if n_steps == '3':
        print(
            "You can choose the cropping version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        cropping_v = input(" cropping version : ")

        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND trial=%s ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]

                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, 1, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()

    # Equalization
    if n_steps == '4':
        print(
            "You can choose the cropping version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        cropping_v = input(" cropping version : ")

        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND trial=%s ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]

                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, 1, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()

    # Source extraction
    if n_steps == '5':
        print(
            "You can choose the motion correction version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        motion_correction_v = input(" motion correction version : ")
        print(
            "You can choose the alignment version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        alignment_v = input(" motion correction version : ")
        print(
            "You can choose the equalization version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        equalization_v = input(" motion correction version : ")
        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND trial=%s ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]

                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, 1, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()

    # Component Evaluation
    if n_steps == '6':
        print(
            "You can choose the source extraction version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        source_extraction_v = input(" source extraction version : ")

        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND trial=%s ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]

                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, 1, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()

    # Registration
    if n_steps == '7':
        print(
            "You can choose the component evaluation version that you want to motion correct if you don't want to choose one particular enter None and the default value will be the latest version of cropping")
        component_evaluation_v = input(" source extraction version : ")

        for session in sessions:
            for i in range(init_trial, end_trial):
                if cropping_v == 'None':
                    sql = "SELECT cropping_v FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND trial=%s ORDER BY cropping_v"
                    val = [mouse_number, session, is_rest, decoding_v, i]

                else:
                    cropping_v = int(cropping_v)
                sql = "SELECT decoding_main FROM Analysis WHERE mouse=%s AND session= %s AND is_rest=%s AND decoding_v=%s AND cropping_v=%s AND trial=%s"
                val = [mouse_number, session, is_rest, decoding_v, 1, i]
                mycursor.execute(sql, val)
                var = mycursor.fetchall()
    # Every steps
    if n_steps == 'all':
        for session in sessions:
            for trial in range(init_trial, end_trial):
                # Decoding
                decoded_file = main_decoding(mouse_number, session, trial, is_rest)

                # Cropping
                cropped_file, cropping_version = main_cropping(decoded_file)

                # Motion correction
                motion_correct_file, motion_correction_version = main_motion_correction(cropped_file, dview)

                # Alignment
                aligned_file, alignment_version = main_alignment(motion_correct_file, dview)

                # Equalization
                equalized_file, equalization_version = main_equalizing(aligned_file, session_wise=True)

                # Source extraction
                source_extracted_file, source_extraction_version = main_source_extraction(equalized_file, dview)

                # Component evaluation
                component_evaluated_file=main_component_evaluation(source_extracted_file, session_wise=True)

                # Registration
                main_registration(component_evaluated_file)
