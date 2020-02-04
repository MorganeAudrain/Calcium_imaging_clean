# -*- coding: utf-8 -*-
"""
Created on November 2019

@author: Melisa, Morgane
"""

import caiman as cm
import os
import numpy as np
from skimage import io
from Database.database_connection import database

mycursor = database.cursor()


def run_equalizer(input_tif_file_list, parameters, session_wise=False):
    """
    This function is meant to help with differences in contrast in different trials and session, to equalize general
    brightness or reduce photobleaching. It corrects the video and saves them in the corrected version. It can be run
    with the already aligned videos or trial by trial. for trial by trial, a template is required.

    params parameters: dict -> contains parameters concerning equalization

    returns : None
    """

    # Determine the output path
    output_tif_file_path = os.environ['DATA_DIR'] + f'data/interim/equalizer/main/'

    if session_wise:
        movie_original = cm.load(input_tif_file_list)  # load video as 3d array already concatenated
        if parameters['make_template_from_trial'] == 0:
            movie_equalized = do_equalization(movie_original)
        else:
            movie_equalized = np.empty_like(movie_original)
            source = movie_original[0:100, :, :]
            # equalize all the videos loads in m_list_reshape with the histogram of source
            for j in range(int(movie_original.shape[0] / 100)):
                want_to_equalize = movie_original[j * 100:(j + 1) * 100, :, :]
                movie_equalized[j * 100:(j + 1) * 100, :, :] = do_equalization_from_template(reference=want_to_equalize,
                                                                                             source=source)
        # Save the movie
        sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v FROM Analysis WHERE alignment_main=%s"
        val = [input_tif_file_list, ]
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        data = []
        for x in myresult:
            data += x
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[5]}.{data[4]}.{data[6]}.{data[7]}"
        equalized_path = movie_equalized.save(output_tif_file_path + file_name + '.mmap', order='C')


    else:
        sql = "SELECT decoding_main,mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v FROM Analysis WHERE alignment_main=%s"
        val = [input_tif_file_list, ]
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        data = []
        for x in myresult:
            data += x
        decoding_output=data[1]

        # load the videos as np.array to be able to manipulate them
        m_list = []
        shape_list = []
        h_step = parameters['histogram_step']
        for i in range(len(input_tif_file_list)):
            im = io.imread(input_tif_file_list[i])  # load video as 3d array
            m_list.append(im)  # and adds all the videos to a list
            shape_list.append(im.shape) # list of sizes to cut the videos in time for making all of them having the same length

        min_shape = min(shape_list)
        new_shape = (100 * int(min_shape[0] / 100), min_shape[1], min_shape[2])  # new videos shape
        m_list_reshape = []
        m_list_equalized = []
        source = m_list[0][0:100, :, :]
        # equalize all the videos load in m_list_reshape with the histogram of source

        for i in range(len(input_tif_file_list)):
            video = m_list[i]
            if parameters['make_template_from_trial'] == 0:
                equalized_video = do_equalization(video)
            else:
                m_list_reshape.append(video[:new_shape[0], :, :])
                equalized_video = np.empty_like(video[:new_shape[0], :, :])
                for j in range(int(min_shape[0] / 100)):
                    want_to_equalize = m_list_reshape[i][j * 100:(j + 1) * 100, :, :]
                    equalized_video[j * 100:(j + 1) * 100, :, :] = do_equalization_from_template(
                        reference=want_to_equalize, source=source)
            m_list_equalized.append(equalized_video)

        # convert the 3d np.array to a caiman movie and save it as a tif file, so it can be read by motion correction script.
        for i in range(len(input_tif_file_list)):
            movie_original = cm.movie(m_list_reshape[i])
            movie_equalized = cm.movie(m_list_equalized[i])

            output['main'] = output_tif_file_path + db.create_file_name(0, row_local.name) + '.tif'
            auxiliar = eval(row_local.loc['decoding_output'])
            auxiliar.update({'equalizing_output': output})
            row_local.loc['decoding_output'] = str(auxiliar)
            movie_equalized.save(output_tif_file_path + db.create_file_name(0, row_local.name) + '.tif')
            states_df = db.append_to_or_merge_with_states_df(states_df, row_local)

    db.save_analysis_states_database(states_df, paths.analysis_states_database_path, paths.backup_path)

    return


def do_equalization(reference):
    """
    Do equalization in a way that the cumulative density function is a linear function on pixel value using the complete
    range where the image is define.
    :arg referece -> image desired to equalize

    """
    # flatten (turns an n-dim-array into 1-dim)
    # sorted pixel values
    srcInd = np.arange(0, 2 ** 16, 2 ** 16 / len(reference.flatten()))
    srcInd = srcInd.astype(int)
    refInd = np.argsort(reference.flatten())
    # assign...
    dst = np.empty_like(reference.flatten())
    dst[refInd] = srcInd
    dst.shape = reference.shape

    return dst


def do_equalization_from_template(source=None, reference=None):
    """
    Created on Fri May 19 22:34:51 2017

    @author: sebalander (Sebastian Arroyo, Universidad de Quilmes, Argentina)

    do_equalization(source, reference) -> using 'cumulative density'
    Takes an image source and reorder the pixel values to have the same
    pixel distribution as reference.

    params : source -> original image which distribution is taken from
    params: reference -> image which pixel values histograms is wanted to be changed

    return: new source image that has the same pixel values distribution as source.
    """

    # flatten (turns an n-dim-array into 1-dim)
    srcV = source.flatten()
    refV = reference.flatten()

    # sorted pixel values
    srcInd = np.argsort(srcV)
    # srcSort = np.sort(srcV)
    refInd = np.argsort(refV)

    # assign...
    dst = np.empty_like(refV)
    dst[refInd] = srcV[srcInd]
    # dst[refInd] = srcSort

    dst.shape = reference.shape

    return dst
