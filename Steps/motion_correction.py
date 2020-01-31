# -*- coding: utf-8 -*-
"""
@author: Sebastian,Casper,Morgane
"""

import os
import logging
import datetime
import pickle
import numpy as np
import caiman as cm
from caiman.motion_correction import MotionCorrect, high_pass_filter_space
from caiman.source_extraction.cnmf import params as params
from Database.database_connection import database

mycursor = database.cursor()


def run_motion_correction(cropped_file, dview):

    """

    This is the function for motion correction. Its goal is to take in a decoded and
    cropped .tif file, perform motion correction, and save the result as a .mmap file.

    This function is only runnable on the cn76 server because it requires parralel processing.

    Args:
        cropped_file
        parameters :  motion_correction_parameters
        dview: cluster

    Returns:
        row: pd.DataFrame object
            The row corresponding to the motion corrected analysis state.
    """

    # Forcing parameters
    sql="SELECT motion_correct,pw_rigid,save_movie_rig,gSig_filt,max_shifts,niter_rig,strides,overlaps,upsample_factor_grid,num_frames_split,max_deviation_rigid,shifts_opencv,use_cuda,nonneg_movie,border_nan FROM Analysis WHERE cropping_main=%s ORDER BY motion_correction_v"
    val=[cropped_file,]
    mycursor.execute(sql,val)
    myresult = mycursor.fetchall()
    parameters=[]
    for x in myresult:
        parameters+=x
    if not parameters[1]:
        parameters[2] = True

    # Get output file paths
    sql1="SELECT mouse,session,trial,is_rest,cropping_v,decoding_v,motion_correction_v FROM Analysis WHERE cropping_main=%s "
    val1=[cropped_file,]
    mycursor.execute(sql1,val1)
    myresult = mycursor.fetchall()
    data=[]
    for x in myresult:
        data+=x

    file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[5]}.{data[4]}.{data[6]}"
    data_dir = 'data/interim/motion_correction/'
    output_meta_pkl_file_path = data_dir + f'meta/metrics/{file_name}.pkl'

    sql2 = "UPDATE Analysis SET motion_correction_meta_metrics=%s WHERE motion_correction_v=%s  "
    val2 = [output_meta_pkl_file_path, parameters[0]]
    mycursor.execute(sql2,val2)
    database.commit()


    # Calculate movie minimum to subtract from movie 
    min_mov = np.min(cm.load(cropped_file))
    # Apply the parameters to the CaImAn algorithm
    caiman_parameters = parameters
    caiman_parameters['min_mov'] = min_mov
    opts = params.CNMFParams(params_dict = caiman_parameters)

    # Rigid motion correction (in both cases)
    logging.info(f' Performing rigid motion correction')
    t0 = datetime.datetime.today()

    
    # Create a MotionCorrect object   
    mc = MotionCorrect([cropped_file], dview = dview, **opts.get_group('motion'))
    # Perform rigid motion correction
    mc.motion_correct_rigid(save_movie = parameters[2], template = None)
    dt = int((datetime.datetime.today() - t0).seconds/60) # timedelta in minutes
    logging.info(f' Rigid motion correction finished. dt = {dt} min')
    # Obtain template, rigid shifts and border pixels
    total_template_rig = mc.total_template_rig
    shifts_rig = mc.shifts_rig 
    # Save template, rigid shifts and border pixels in a dictionary
    sql3 = "INSERT INTO Analysis (rigid_templates,rigid_shifts,meta_duration, meta_cropping_points) VALUES (%s,%s,%s,%s)"
    val3 = [total_template_rig, shifts_rig,dt,[0,0,0,0]]
    mycursor.execute(sql3, val3)
    database.commit()

    if parameters[2]:
        # Load the movie saved by CaImAn, which is in the wrong
        # directory and is not yet cropped
        logging.info(f' Loading rigid movie for cropping')
        m_rig = cm.load(mc.fname_tot_rig[0])
        logging.info(f'Loaded rigid movie for cropping')
        # Get the cropping points determined by the maximal rigid shifts
        x_, _x, y_, _y = get_crop_from_rigid_shifts(shifts_rig)
        # Crop the movie
        logging.info(f' Cropping and saving rigid movie with cropping points: [x_, _x, y_, _y] = {[x_, _x, y_, _y]}')
        #m_rig = m_rig.crop(x_, _x, y_, _y, 0, 0)

        # Save the movie 
        rig_role = 'alternate' if parameters[1] else 'main'
        fname_tot_rig  = m_rig.save(data_dir + rig_role + '/' + file_name + '_rig' + '.mmap',  order='C')
        logging.info(f'Cropped and saved rigid movie as {fname_tot_rig}')
        # Store the total path in output
        sql4 = "UPDATE Analysis SET rigig_cropping_points=%s,meta_cropping_points=%s, rig_role=%s WHERE motion_correction_meta_metrics=%s  "
        val4 = [[x_, _x, y_, _y], [x_, _x, y_, _y],fname_tot_rig, output_meta_pkl_file_path]
        mycursor.execute(sql4, val4)
        database.commit()
        # Remove the remaining non-cropped movie
        os.remove(mc.fname_tot_rig[0])
            

    # If specified in the parameters, apply piecewise-rigid motion correction
    if parameters[1]:
        logging.info(f' Performing piecewise-rigid motion correction')
        t0 = datetime.datetime.today()
        # Perform non-rigid (piecewise rigid) motion correction. Use the rigid result as a template.
        mc.motion_correct_pwrigid(save_movie=True, template = total_template_rig)
        # Obtain template and filename
        total_template_els = mc.total_template_els
        fname_tot_els = mc.fname_tot_els[0]
        
        dt = int((datetime.datetime.today() - t0).seconds/60) # timedelta in minutes
        logging.info(f' Piecewise-rigid motion correction finished. dt = {dt} min')
        sql4 = "UPDATE Analysis SET pw_rigid_template=%s,pw_rigid_x_shifts=%s, pw_rigid_y_shifts=%s,duration_pw_rigid WHERE motion_correction_meta_metrics=%s  "
        val4 = [total_template_els, mc.x_shifts_els,mc.y_shifts_els,dt, output_meta_pkl_file_path]
        mycursor.execute(sql4, val4)
        database.commit()
        
        # Load the movie saved by CaImAn, which is in the wrong
        # directory and is not yet cropped
        logging.info(f'Loading pw-rigid movie for cropping')
        m_els = cm.load(fname_tot_els)
        logging.info(f'Loaded pw-rigid movie for cropping')
        # Get the cropping points determined by the maximal rigid shifts
        x_, _x, y_, _y = get_crop_from_pw_rigid_shifts(np.array(mc.x_shifts_els), 
                                                       np.array(mc.y_shifts_els))       
        # Crop the movie
        logging.info(f' Cropping and saving pw-rigid movie with cropping points: [x_, _x, y_, _y] = {[x_, _x, y_, _y]}')
        #m_els = m_els.crop(x_, _x, y_, _y, 0, 0)
        sql5 = "UPDATE Analysis SET pw_rigid_cropping_points=%s,meta_cropping_points WHERE motion_correction_meta_metrics=%s  "
        val5 = [[x_, _x, y_, _y],[x_, _x, y_, _y], output_meta_pkl_file_path]
        mycursor.execute(sql5, val5)
        database.commit()

        # Save the movie 
        fname_tot_els  = m_els.save(data_dir + 'main/' + file_name + '_els' + '.mmap',  order='C')
        logging.info(f' Cropped and saved rigid movie as {fname_tot_els}')

        # Remove the remaining non-cropped movie
        os.remove(mc.fname_tot_els[0])
                
        # Store the total path in output
        sql5 = "UPDATE Analysis SET motion_correction_main,meta_cropping_points WHERE motion_correction_meta_metrics=%s  "
        val5 = [fname_tot_els,[x_, _x, y_, _y], output_meta_pkl_file_path]
        mycursor.execute(sql5, val5)
        database.commit()


    # Write meta results dictionary to the pkl file 
    pkl_file = open(output_meta_pkl_file_path, 'wb')
    pickle.dump(pkl_file)
    pkl_file.close()    

    return

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
