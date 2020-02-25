# -*- coding: utf-8 -*-
"""
@author: Sebastian,Casper,Melisa,Morgane
"""

import datetime
import logging
import os
import pickle

import configuration

import caiman as cm
import numpy as np
from caiman.motion_correction import MotionCorrect
from caiman.source_extraction.cnmf import params as params

from Database.database_connection import database

cursor = database.cursor()


def run_motion_correction(cropping_file, dview):
    """
    This is the function for motion correction. Its goal is to take in a decoded and
    cropped .tif file, perform motion correction, and save the result as a .mmap file.

    This function is only runnable on the cn76 server because it requires parallel processing.

    Args:
        cropping_file: tif file after cropping
        dview: cluster

    Returns:
        row: pd.DataFrame object
            The row corresponding to the motion corrected analysis state.
    """
    # Get output file paths

    data_dir = os.environ['DATA_DIR_LOCAL'] + 'data/interim/motion_correction/'
    sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,input,home_path,decoding_main FROM Analysis WHERE cropping_main=? ORDER BY motion_correction_v"
    val = [cropping_file, ]
    cursor.execute(sql, val)
    result = cursor.fetchall()
    data = []
    inter = []
    for x in result:
        inter = x
    for y in inter:
        data.append(y)

    # Update the database

    if data[6] == 0:
        data[6] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}"
        output_meta_pkl_file_path = f'meta/metrics/{file_name}.pkl'
        sql1 = "UPDATE Analysis SET motion_correction_meta=?,motion_correction_v=? WHERE cropping_main=? "
        val1 = [output_meta_pkl_file_path, data[6], cropping_file]
        cursor.execute(sql1, val1)

    else:
        data[6] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}"
        output_meta_pkl_file_path = f'meta/metrics/{file_name}.pkl'
        sql2 = "INSERT INTO Analysis (motion_correction_meta,motion_correction_v) VALUES (?,?)"
        val2 = [output_meta_pkl_file_path, data[6]]
        cursor.execute(sql2, val2)
        database.commit()
        sql3 = "UPDATE Analysis SET decoding_main=?,decoding_v=?,mouse=?,session=?,trial=?,is_rest=?,input=?,home_path=?,cropping_v=?,cropping_main=? WHERE motion_correction_meta=? AND motion_correction_v=?"
        val3 = [data[9], data[4], data[0], data[1], data[2], data[3], data[7], data[8], data[5], cropping_file,
                output_meta_pkl_file_path, data[6]]
        cursor.execute(sql3, val3)
    database.commit()
    output_meta_pkl_file_path_full = data_dir + output_meta_pkl_file_path

    # Calculate movie minimum to subtract from movie
    cropping_file_full = os.environ['DATA_DIR_LOCAL'] + cropping_file
    min_mov = np.min(cm.load(cropping_file_full))

    # Apply the parameters to the CaImAn algorithm

    sql5 = "SELECT motion_correct,pw_rigid,save_movie_rig,gSig_filt,max_shifts,niter_rig,strides,overlaps,upsample_factor_grid,num_frames_split,max_deviation_rigid,shifts_opencv,use_conda,nonneg_movie, border_nan  FROM Analysis WHERE cropping_main=? "
    val5 = [cropping_file, ]
    cursor.execute(sql5, val5)
    myresult = cursor.fetchall()
    para = []
    aux = []
    for x in myresult:
        aux = x
    for y in aux:
        para.append(y)
    parameters = {'motion_correct': para[0], 'pw_rigid': para[1], 'save_movie_rig': para[2],
                  'gSig_filt': (para[3], para[3]), 'max_shifts': (para[4], para[4]), 'niter_rig': para[5],
                  'strides': (para[6], para[6]),
                  'overlaps': (para[7], para[7]), 'upsample_factor_grid': para[8], 'num_frames_split': para[9],
                  'max_deviation_rigid': para[10],
                  'shifts_opencv': para[11], 'use_cuda': para[12], 'nonneg_movie': para[13],
                  'border_nan': para[14]}
    caiman_parameters = parameters.copy()
    caiman_parameters['min_mov'] = min_mov
    opts = params.CNMFParams(params_dict=caiman_parameters)

    # Rigid motion correction (in both cases)

    logging.info('Performing rigid motion correction')
    t0 = datetime.datetime.today()

    # Create a MotionCorrect object

    mc = MotionCorrect([cropping_file_full], dview=dview, **opts.get_group('motion'))

    # Perform rigid motion correction

    mc.motion_correct_rigid(save_movie=parameters['save_movie_rig'], template=None)
    dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
    logging.info(f' Rigid motion correction finished. dt = {dt} min')

    # Obtain template, rigid shifts and border pixels

    total_template_rig = mc.total_template_rig
    shifts_rig = mc.shifts_rig

    # Save template, rigid shifts and border pixels in a dictionary

    meta_pkl_dict = {
        'rigid': {
            'template': total_template_rig,
            'shifts': shifts_rig,
        }
    }
    sql = "UPDATE Analysis SET duration_rigid=? WHERE motion_correction_meta=? AND motion_correction_v=? "
    val = [dt, output_meta_pkl_file_path, data[6]]
    cursor.execute(sql, val)

    if parameters['save_movie_rig'] == 1:
        # Load the movie saved by CaImAn, which is in the wrong
        # directory and is not yet cropped

        logging.info(f' Loading rigid movie for cropping')
        m_rig = cm.load(mc.fname_tot_rig[0])
        logging.info(f' Loaded rigid movie for cropping')

        # Get the cropping points determined by the maximal rigid shifts

        x_, _x, y_, _y = get_crop_from_rigid_shifts(shifts_rig)

        # Crop the movie

        logging.info(f' Cropping and saving rigid movie with cropping points: [x_, _x, y_, _y] = {[x_, _x, y_, _y]}')
        m_rig = m_rig.crop(x_, _x, y_, _y, 0, 0)
        meta_pkl_dict['rigid']['cropping_points'] = [x_, _x, y_, _y]
        sql = "UPDATE Analysis SET motion_correction_cropping_points_x1=?,motion_correction_cropping_points_x2=?,motion_correction_cropping_points_y1=?,motion_correction_cropping_points_y2=? WHERE motion_correction_meta=? AND motion_correction_v=? "
        val = [x_, _x, y_, _y, output_meta_pkl_file_path, data[6]]
        cursor.execute(sql, val)

        # Save the movie

        rig_role = 'alternate' if parameters['pw_rigid'] else 'main'
        fname_tot_rig = m_rig.save(data_dir + rig_role + '/' + file_name + '_rig' + '.mmap', order='C')
        logging.info(f' Cropped and saved rigid movie as {fname_tot_rig}')

        # Remove the remaining non-cropped movie

        os.remove(mc.fname_tot_rig[0])

        sql = "UPDATE Analysis SET motion_correction_rig_role=? WHERE motion_correction_meta=? AND motion_correction_v=? "
        val = [fname_tot_rig, output_meta_pkl_file_path, data[6]]
        cursor.execute(sql, val)
        database.commit()

    # If specified in the parameters, apply piecewise-rigid motion correction
    if parameters['pw_rigid'] == 1:
        logging.info(f' Performing piecewise-rigid motion correction')
        t0 = datetime.datetime.today()
        # Perform non-rigid (piecewise rigid) motion correction. Use the rigid result as a template.
        mc.motion_correct_pwrigid(save_movie=True, template=total_template_rig)
        # Obtain template and filename
        total_template_els = mc.total_template_els
        fname_tot_els = mc.fname_tot_els[0]

        dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
        meta_pkl_dict['pw_rigid'] = {
            'template': total_template_els,
            'x_shifts': mc.x_shifts_els,
            'y_shifts': mc.y_shifts_els  # removed them initially because they take up space probably
        }

        logging.info(f' Piecewise-rigid motion correction finished. dt = {dt} min')

        # Load the movie saved by CaImAn, which is in the wrong
        # directory and is not yet cropped

        logging.info(f' Loading pw-rigid movie for cropping')
        m_els = cm.load(fname_tot_els)
        logging.info(f' Loaded pw-rigid movie for cropping')

        # Get the cropping points determined by the maximal rigid shifts

        x_, _x, y_, _y = get_crop_from_pw_rigid_shifts(np.array(mc.x_shifts_els),
                                                       np.array(mc.y_shifts_els))
        # Crop the movie

        logging.info(f' Cropping and saving pw-rigid movie with cropping points: [x_, _x, y_, _y] = {[x_, _x, y_, _y]}')
        m_els = m_els.crop(x_, _x, y_, _y, 0, 0)
        meta_pkl_dict['pw_rigid']['cropping_points'] = [x_, _x, y_, _y]

        # Save the movie

        fname_tot_els = m_els.save(data_dir + 'main/' + file_name + '_els' + '.mmap', order='C')
        logging.info(f'Cropped and saved rigid movie as {fname_tot_els}')

        # Remove the remaining non-cropped movie

        os.remove(mc.fname_tot_els[0])

        sql = "UPDATE Analysis SET  motion_correction_main=?, motion_correction_cropping_points_x1=?,motion_correction_cropping_points_x2=?,motion_correction_cropping_points_y1=?,motion_correction_cropping_points_y2=?,duration_pw_rigid=? WHERE motion_correction_meta=? AND motion_correction_v=? "
        val = [fname_tot_els, x_, _x, y_, _y, dt, output_meta_pkl_file_path, data[6]]
        cursor.execute(sql, val)
        database.commit()

    # Write meta results dictionary to the pkl file


    pkl_file = open(output_meta_pkl_file_path_full, 'wb')
    pickle.dump(meta_pkl_dict, pkl_file)
    pkl_file.close()

    return fname_tot_els, data[6]


def get_crop_from_rigid_shifts(shifts_rig):
    x_ = int(round(abs(np.array(shifts_rig)[:, 1].max()) if np.array(shifts_rig)[:, 1].max() > 0 else 0))
    _x = int(round(abs(np.array(shifts_rig)[:, 1].min()) if np.array(shifts_rig)[:, 1].min() < 0 else 0))
    y_ = int(round(abs(np.array(shifts_rig)[:, 0].max()) if np.array(shifts_rig)[:, 0].max() > 0 else 0))
    _y = int(round(abs(np.array(shifts_rig)[:, 0].min()) if np.array(shifts_rig)[:, 0].min() < 0 else 0))
    return x_, _x, y_, _y


def get_crop_from_pw_rigid_shifts(x_shifts_els, y_shifts_els):
    x_ = int(round(abs(x_shifts_els.max()) if x_shifts_els.max() > 0 else 0))
    _x = int(round(abs(x_shifts_els.min()) if x_shifts_els.min() < 0 else 0))
    y_ = int(round(abs(y_shifts_els.max()) if y_shifts_els.max() > 0 else 0))
    _y = int(round(abs(x_shifts_els.min()) if x_shifts_els.min() < 0 else 0))
    return x_, _x, y_, _y
