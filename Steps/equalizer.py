# -*- coding: utf-8 -*-
"""
Created on November 2019

@author: Melisa,Morgane
"""

import caiman as cm
import os
import numpy as np


from Database.database_connection import database

cursor = database.cursor()


def run_equalizer(input_file, session_wise=False):
    """
    This function is meant to help with differences in contrast in different trials and session, to equalize general
    brightness or reduce photobleaching. It corrects the video and saves them in the corrected version. It can be run
    with the already aligned videos or trial by trial. for trial by trial, a template is required.
    """
    # Take all the parameters needed for equalization
    sql5 = "SELECT make_template_from_trial,equalizer,histogram_step FROM Analysis WHERE alignment_main=? OR motion_correction_main =? "
    val5 = [input_file,input_file ]
    cursor.execute(sql5, val5)
    myresult = cursor.fetchall()
    para = []
    aux = []
    for x in myresult:
        aux = x
    for y in aux:
        para.append(y)
    parameters = {'make_template_from_trial': para[0], 'equalizer': para[1],
                            'histogram_step': para[2]}


    # determine the output file
    output_tif_file_path = os.environ['DATA_DIR'] + f'data/interim/equalizer/main/'
    #determine the file name
    sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,motion_correction_v,alignment_v,equalization_v,input,home_path,decoding_main FROM Analysis WHERE alignment_main =? Or motion_correction_main =?"
    val = [input_file,input_file ]
    cursor.execute(sql, val)
    result = cursor.fetchall()
    data = []
    inter = []
    for x in result:
        inter = x
    for y in inter:
        data.append(y)

    # Update the database

    if data[8] == 0:
        data[8] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}"
        sql1 = "UPDATE Analysis SET equalization_main=?,equalization_v=? WHERE alignment_main=? "
        val1 = [file_name, data[8], input_file]
        cursor.execute(sql1, val1)

    else:
        data[8] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}.{data[6]}.{data[7]}.{data[8]}"
        sql2 = "INSERT INTO Analysis (motion_correction_meta,motion_correction_v) VALUES (?,?)"
        val2 = [file_name, data[8]]
        cursor.execute(sql2, val2)
        database.commit()
    database.commit()

    input_tif_file_list= os.path.join(os.environ['DATA_DIR_LOCAL'], input_file)
    movie_original = cm.load(input_tif_file_list)  # load video as 3d array already concatenated
    if parameters['make_template_from_trial'] == 0:
        movie_equalized = do_equalization(movie_original)
    else:
        movie_equalized = np.empty_like(movie_original)
        source = movie_original[0:100, :, :]
        # equalize all the videos loads in m_list_reshape with the histogram of source
        for j in range(int(movie_original.shape[0] / 100)):
            want_to_equalize = movie_original[j * 100:(j + 1) * 100, :, :]
            movie_equalized[j * 100:(j + 1) * 100, :, :] = do_equalization_from_template(reference=want_to_equalize, source=source)
    #Save the movie
    equalized_path = movie_equalized.save(output_tif_file_path + file_name + '.mmap', order='C')

    return output_tif_file_path

def do_equalization(reference):

    '''
    Do equalization in a way that the cumulative density function is a linear function on pixel value using the complete
    range where the image is define.
    :arg referece -> image desired to equalize

    '''
    # flatten (turns an n-dim-array into 1-dim)
    # sorted pixel values
    srcInd = np.arange(0, 2 ** 16, 2 ** 16 / len(reference.flatten()))
    srcInd = srcInd.astype(int)
    refInd = np.argsort(reference.flatten())
    #assign...
    dst = np.empty_like(reference.flatten())
    dst[refInd] = srcInd
    dst.shape = reference.shape

    return dst


def do_equalization_from_template(source = None, reference = None):

    '''
    Created on Fri May 19 22:34:51 2017

    @author: sebalander (Sebastian Arroyo, Universidad de Quilmes, Argentina)

    do_equalization(source, reference) -> using 'cumulative density'
    Takes an image source and reorder the pixel values to have the same
    pixel distribution as reference.

    params : source -> original image which distribution is taken from
    params: reference -> image which pixel values histograms is wanted to be changed

    return: new source image that has the same pixel values distribution as source.
    '''

    # flatten (turns an n-dim-array into 1-dim)
    srcV = source.flatten()
    refV = reference.flatten()

    # sorted pixel values
    srcInd = np.argsort(srcV)
    #srcSort = np.sort(srcV)
    refInd = np.argsort(refV)

    #assign...
    dst = np.empty_like(refV)
    dst[refInd] = srcV[srcInd]
    #dst[refInd] = srcSort

    dst.shape = reference.shape

    return dst
