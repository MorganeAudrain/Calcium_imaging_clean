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


def run_alignment(mouse,sessions, dview):
    """
    This is the main function for the alignment step. It applies methods
    from the CaImAn package used originally in motion correction
    to do alignment.

    """
    for session in sessions:
        sql = "SELECT motion_correction_meta  FROM Analysis WHERE mouse = ? AND session=?"
        val = [mouse, session]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        data = []
        inter = []
        for x in result:
            inter += x
        for y in inter:
            data.append(y)

        # Update the database

        file_name = f"mouse_{mouse}_session_{session}_alignment"
        sql1 = "UPDATE Analysis SET alignment_main=? WHERE mouse = ? AND session=? "
        val1 = [file_name, mouse, session]
        cursor.execute(sql1, val1)


        # Determine the output .mmap file name
        output_mmap_file_path = os.environ['DATA_DIR_LOCAL'] + f'data/interim/alignment/main/{file_name}.mmap'
        sql = "SELECT motion_correction_meta  FROM Analysis WHERE mouse = ? AND session=?"
        val = [mouse, session]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        input_mmap_file_list = []
        inter = []
        for x in result:
            inter += x
        for y in inter:
            input_mmap_file_list.append(y)

        sql = "SELECT motion_correction_cropping_points_x1,motion_correction_cropping_points_x2,motion_correction_cropping_points_y1,motion_correction_cropping_points_y2 FROM Analysis WHERE mouse = ? AND session=? AND trial=?"
        val = [mouse, session, i]
        cursor.execute(sql, val)
        result = cursor.fetchall()
        x_ = []
        _x = []
        y_ = []
        _y = []
        inter = []
        for i in result:
            inter += i
        for j in inter:
            x_.append(j)
            _x.append([j+1])
            y_.append([j+2])
            _y.append([j+3])

        new_x1 = max(x_)
        new_x2 = max(_x)
        new_y1 = max(y_)
        new_y2 = max(_y)
        m_list = []
        for i in range(len(input_mmap_file_list)):
            m = cm.load(input_mmap_file_list[i])
            m = m.crop(new_x1 - x1, new_x2 - x2, new_y1 - y1, new_y2 - y2, 0, 0)
            m_list.append(m)

        # Concatenate them using the concat function
        m_concat = cm.concatenate(m_list, axis=0)
        data_dir = os.environ['DATA_DIR'] + 'data/interim/alignment/main/'
        file_name = db.create_file_name(step_index, index)
        fname= m_concat.save(data_dir + file_name + '.mmap', order='C')

        # MOTION CORRECTING EACH INDIVIDUAL MOVIE WITH RESPECT TO A TEMPLATE MADE OF THE FIRST MOVIE
        logging.info(f'{alignment_index} Performing motion correction on all movies with respect to a template made of \
        the first movie.')
        t0 = datetime.datetime.today()

        # Create a template of the first movie
        template_index = trial_index_list.index(parameters['make_template_from_trial'])
        m0 = cm.load(input_mmap_file_list[template_index ])
        [x1, x2, y1, y2] = motion_correction_output_list[template_index]['meta']['cropping_points']
        m0 = m0.crop(new_x1 - x1, new_x2 - x2, new_y1 - y1, new_y2 - y2, 0, 0)
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
        movie= cm.load(mc.fname_tot_rig[0])
        # Crop all movies to those border pixels
        movie.crop(x_, _x, y_, _y, 0, 0)
        output['meta']['cropping_points'] = [x_, _x, y_, _y]

        #save motion corrected and cropped movie
        output_mmap_file_path_tot = movie.save(data_dir + file_name  + '.mmap', order='C')
        logging.info(f'{index} Cropped and saved rigid movie as {output_mmap_file_path_tot}')
        # Save the path in teh output dictionary
        output['main'] = output_mmap_file_path_tot
        # Remove the remaining non-cropped movie
        os.remove(mc.fname_tot_rig[0])

        # Create a timeline and store it
        timeline = [[trial_index_list[0], 0]]
        timepoints = [0]
        for i in range(1, len(m_list)):
            m = m_list[i]
            timeline.append([trial_index_list[i], timeline[i - 1][1] + m.shape[0]])
            timepoints.append(timepoints[i-1]+ m.shape[0])
            timeline_pkl_file_path = os.environ['DATA_DIR'] + f'data/interim/alignment/meta/timeline/{file_name}.pkl'
            with open(timeline_pkl_file_path,'wb') as f:
                pickle.dump(timeline,f)
        output['meta']['timeline'] = timeline_pkl_file_path
        timepoints.append(movie.shape[0])

        dt = int((datetime.datetime.today() - t0).seconds / 60)  # timedelta in minutes
        output['meta']['duration']['concatenation'] = dt
        logging.info(f'{alignment_index} Performed concatenation. dt = {dt} min.')

        for idx, row in df.iterrows():
            df.loc[idx, 'alignment_output'] = str(output)
            df.loc[idx, 'alignment_parameters'] = str(parameters)

        ## modify all motion correction file to the aligned version
        data_dir = os.environ['DATA_DIR'] + 'data/interim/motion_correction/main/'
        for i in range(len(input_mmap_file_list)):
            row = df.iloc[i].copy()
            motion_correction_output_list.append(motion_correction_output)
            aligned_movie = movie[timepoints[i]:timepoints[i+1]]
            file_name = db.create_file_name(2, selected_rows.iloc[i].name)
            motion_correction_output_aligned = aligned_movie.save(data_dir + file_name + '_els' + '.mmap',  order='C')
            new_output= {'main' : motion_correction_output_aligned }
            new_dict = eval(row['motion_correction_output'])
            new_dict.update(new_output)
            row['motion_correction_output'] = str(new_dict)
            df = db.append_to_or_merge_with_states_df(df, row)

    return df
