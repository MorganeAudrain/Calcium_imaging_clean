# -*- coding: utf-8 -*-
"""
@author: Sebastian,Casper,Melisa, Morgane
"""

import logging
import caiman as cm
import caiman.motion_correction
from caiman.motion_correction import MotionCorrect, high_pass_filter_space
from caiman.source_extraction.cnmf import params as params
import configuration
import datetime
import os
import numpy as np
import pickle
import math
from Database.database_connection import database

cursor = database.cursor()


def run_alignment(mouse, sessions,motion_correction_v, cropping_v, dview):
    """
    This is the main function for the alignment step. It applies methods
    from the CaImAn package used originally in motion correction
    to do alignment.

    """
    for session in sessions:
        # Update the database

        file_name = f"mouse_{mouse}_session_{session}_alignment"
        sql1 = "UPDATE Analysis SET alignment_main=? WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=? "
        val1 = [file_name, mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql1, val1)

        # Determine the output .mmap file name
        output_mmap_file_path = os.environ['DATA_DIR_LOCAL'] + f'data/interim/alignment/main/{file_name}.mmap'
        sql = "SELECT motion_correction_main  FROM Analysis WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=? "
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        input_mmap_file_list = []
        inter = []
        for x in result:
            inter += x
        for y in inter:
            input_mmap_file_list.append(y)

        sql = "SELECT motion_correction_cropping_points_x1 FROM Analysis WHERE mouse = ? AND session=?AND motion_correction_v =? AND cropping_v=? "
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        x_ = []
        inter = []
        for i in result:
            inter += i
        for j in range(0,len(inter)):
            x_.append(inter[j])

        sql = "SELECT motion_correction_cropping_points_x2 FROM Analysis WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=? "
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        _x = []
        inter = []
        for i in result:
            inter += i
        for j in range(0,len(inter)):
            _x.append(inter[j])

        sql = "SELECT motion_correction_cropping_points_y1 FROM Analysis WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=?"
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        _y = []
        inter = []
        for i in result:
            inter += i
        for j in range(0,len(inter)):
            _y.append(inter[j])

        sql = "SELECT motion_correction_cropping_points_y2 FROM Analysis WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=?"
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        y_ = []
        inter = []
        for i in result:
            inter += i
        for j in range(0,len(inter)):
            y_.append(inter[j])

        new_x1 = max(x_)
        new_x2 = max(_x)
        new_y1 = max(y_)
        new_y2 = max(_y)
        m_list = []
        for i in range(len(input_mmap_file_list)):
            m = cm.load(input_mmap_file_list[i])
            m = m.crop(new_x1 - x_[i], new_x2 - _x[i], new_y1 - y_[i], new_y2 - _y[i], 0, 0)
            m_list.append(m)

        # Concatenate them using the concat function
        m_concat = cm.concatenate(m_list, axis=0)
        fname = m_concat.save(output_mmap_file_path, order='C')

        # MOTION CORRECTING EACH INDIVIDUAL MOVIE WITH RESPECT TO A TEMPLATE MADE OF THE FIRST MOVIE
        logging.info('Performing motion correction on all movies with respect to a template made of the first movie.')
        t0 = datetime.datetime.today()
        # parameters alignment
        sql5 = "SELECT make_template_from_trial,gSig_filt,max_shifts,niter_rig,strides,overlaps,upsample_factor_grid,num_frames_split,max_deviation_rigid,shifts_opencv,use_conda,nonneg_movie, border_nan  FROM Analysis WHERE alignment_main=? "
        val5 = [file_name, ]
        cursor.execute(sql5, val5)
        myresult = cursor.fetchall()
        para = []
        aux = []
        for x in myresult:
            aux = x
        for y in aux:
            para.append(y)
        parameters = {'make_template_from_trial': para[0], 'gSig_filt': (para[1], para[1]),
                      'max_shifts': (para[2], para[2]),
                      'niter_rig': para[3],
                      'strides': (para[4], para[4]), 'overlaps': (para[5], para[5]), 'upsample_factor_grid': para[6],
                      'num_frames_split': para[7],
                      'max_deviation_rigid': para[8], 'shifts_opencv': para[9], 'use_cuda': para[10],
                      'nonneg_movie': para[11],
                      'border_nan': para[12]}
        # Create a template of the first movie
        template_index = parameters['make_template_from_trial']
        m0 = cm.load(input_mmap_file_list[1])
        [x1, x2, y1, y2] = [x_,_x,y_,_y]
        for i in range(len(input_mmap_file_list)):
            m0 = m0.crop(new_x1 - x_[i], new_x2 - _x[i], new_y1 - y_[i], new_y2 - _y[i], 0, 0)
        m0_filt = cm.movie(
            np.array([high_pass_filter_space(m_, parameters['gSig_filt']) for m_ in m0]))
        template0 = cm.motion_correction.bin_median(
            m0_filt.motion_correct(5, 5, template=None)[0])  # may be improved in the future

        # Setting the parameters
        opts = params.CNMFParams(params_dict=parameters)

        # Create a motion correction object
        mc = MotionCorrect(fname, dview=dview, **opts.get_group('motion'))

        # Perform non-rigid motion correction
        mc.motion_correct(template=template0, save_movie=True)

        # Cropping borders
        x_ = math.ceil(abs(np.array(mc.shifts_rig)[:, 1].max()) if np.array(mc.shifts_rig)[:, 1].max() > 0 else 0)
        _x = math.ceil(abs(np.array(mc.shifts_rig)[:, 1].min()) if np.array(mc.shifts_rig)[:, 1].min() < 0 else 0)
        y_ = math.ceil(abs(np.array(mc.shifts_rig)[:, 0].max()) if np.array(mc.shifts_rig)[:, 0].max() > 0 else 0)
        _y = math.ceil(abs(np.array(mc.shifts_rig)[:, 0].min()) if np.array(mc.shifts_rig)[:, 0].min() < 0 else 0)

        # Load the motion corrected movie into memory
        movie = cm.load(mc.fname_tot_rig[0])
        # Crop all movies to those border pixels
        movie.crop(x_, _x, y_, _y, 0, 0)
        sql1 = "UPDATE Analysis SET alignment_x1=?, alignment_x2 =?, alignment_y1=?, alignment_y2=? WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=?"
        val1 = [x_,_x,y_,_y, mouse, session, motion_correction_v,cropping_v]
        cursor.execute(sql1, val1)


        # save motion corrected and cropped movie
        output_mmap_file_path_tot = movie.save(os.environ['DATA_DIR_LOCAL'] + f'data/interim/alignment/main/{file_name}.mmap', order='C')
        logging.info(f' Cropped and saved rigid movie as {output_mmap_file_path_tot}')
        # Remove the remaining non-cropped movie
        os.remove(mc.fname_tot_rig[0])

        # Create a timeline and store it
        sql = "SELECT trial FROM Analysis WHERE mouse = ? AND session=? AND motion_correction_v =? AND cropping_v=?"
        val = [mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        trial_index_list = []
        inter = []
        for i in result:
            inter += i
        for j in range(0,len(inter)):
            trial_index_list.append(inter[j])

        timeline = [[trial_index_list[0], 0]]
        timepoints = [0]
        for i in range(1, len(m_list)):
            m = m_list[i]
            timeline.append([trial_index_list[i], timeline[i - 1][1] + m.shape[0]])
            timepoints.append(timepoints[i - 1] + m.shape[0])
            timeline_pkl_file_path = os.environ['DATA_DIR'] + f'data/interim/alignment/meta/timeline/{file_name}.pkl'
            with open(timeline_pkl_file_path, 'wb') as f:
                pickle.dump(timeline, f)
        sql1 = "UPDATE Analysis SET alignment_timeline=? WHERE mouse = ? AND session=?AND motion_correction_v =? AND cropping_v=? "
        val1 = [timeline_pkl_file_path, mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql1, val1)
        timepoints.append(movie.shape[0])

        dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
        sql1 = "UPDATE Analysis SET alignment_duration_concatenation=? WHERE mouse = ? AND session=?AND motion_correction_v =? AND cropping_v=? "
        val1 = [dt, mouse, session,motion_correction_v,cropping_v]
        cursor.execute(sql1, val1)
        logging.info(f' Performed concatenation. dt = {dt} min.')

        ## modify all motion correction file to the aligned version
        data_dir = os.environ['DATA_DIR'] + 'data/interim/motion_correction/main/'
        for i in range(len(input_mmap_file_list)):
            aligned_movie = movie[timepoints[i]:timepoints[i + 1]]
            motion_correction_output_aligned = aligned_movie.save(data_dir + file_name + '_els' + '.mmap', order='C')
            sql1 = "UPDATE Analysis SET motion_correct_align=? WHERE motion_correction_meta=? AND motion_correction_v"
            val1 = [motion_correction_output_aligned, input_mmap_file_list[i],motion_correction_v]
            cursor.execute(sql1, val1)

    database.commit()
    return
