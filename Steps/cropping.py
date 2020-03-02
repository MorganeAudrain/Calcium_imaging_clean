# -*- coding: utf-8 -*-
"""
@author: Sebastian,Casper,Melisa,Morgane
"""

import caiman as cm
import logging
import os
import configuration
from Database.database_connection import database

mycursor = database.cursor()


def run_cropper(input_path, parameters):
    """
    This function takes in a decoded analysis state and crops it according to
    specified cropping points.

    Args:
        input_path the path of the decoding file

    """

    # Determine output .tif file path
    sql = "SELECT mouse,session,trial,is_rest,decoding_v,cropping_v,input,home_path FROM Analysis WHERE decoding_main=?"
    val = [input_path, ]
    mycursor.execute(sql, val)
    myresult = mycursor.fetchall()
    data = []
    aux = []
    for x in myresult:
        aux = x
    for y in aux:
        data.append(y)

    # update the database
    if data[5] == 0:
        data[5] = 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}"
        output_tif_file_path = f"data/interim/cropping/main/{file_name}.tif"
        sql1 = "UPDATE Analysis SET cropping_main=?,cropping_v=? WHERE decoding_main=? "
        val1 = [output_tif_file_path, data[5], input_path]
        mycursor.execute(sql1, val1)

    else:
        data[5] += 1
        file_name = f"mouse_{data[0]}_session_{data[1]}_trial_{data[2]}.{data[3]}.v{data[4]}.{data[5]}"
        output_tif_file_path = f"data/interim/cropping/main/{file_name}.tif"
        sql2 = "INSERT INTO Analysis (cropping_main,cropping_v) VALUES (?,?)"
        val2 = [output_tif_file_path, data[5]]
        mycursor.execute(sql2, val2)
        database.commit()
        sql3 = "UPDATE Analysis SET decoding_main=?,decoding_v=?,mouse=?,session=?,trial=?,is_rest=?,input=?,home_path=? WHERE cropping_main=? AND cropping_v=?"
        val3 = [input_path, data[4], data[0], data[1], data[2], data[3], data[6], data[7], output_tif_file_path,
                data[5]]
        mycursor.execute(sql3, val3)

    # Spatial cropping
    input_path = os.path.join(os.environ['DATA_DIR_LOCAL'], input_path)
    logging.info('Loading movie')
    m = cm.load(input_path)
    logging.info('Loaded movie')

    [x_, _x, y_, _y] = parameters['cropping_points_spatial']

    logging.info('Performing spatial cropping')
    m = m[:, x_:_x, y_:_y]
    logging.info(' Spatial cropping finished')
    output_tif_file_path_full = os.path.join(os.environ['DATA_DIR_LOCAL'], output_tif_file_path)
    # Save the movie
    m.save(output_tif_file_path_full)

    return output_tif_file_path, data[5]


def cropping_interval(mouse):
    """
    This function ask the user for cropping parameters
    """
    # Choose crop parameters
    x1 = int(input("Limit X1 : "))
    x2 = int(input("Limit X2 : "))
    y1 = int(input("Limit Y1 : "))
    y2 = int(input("Limit Y2 : "))
    sql = "UPDATE Analysis SET crop_spatial=?,cropping_points_spatial_x1=?,cropping_points_spatial_x2=?,cropping_points_spatial_y1=?,cropping_points_spatial_y2=?,crop_temporal=?,cropping_points_temporal=? WHERE mouse = ?"
    val = [True, x1, x2, y1, y2, False, None, mouse]
    mycursor.execute(sql, val)
    database.commit()
    parameters_cropping = {'crop_spatial': True, 'cropping_points_spatial': [y1, y2, x1, x2],
                           'crop_temporal': False, 'cropping_points_temporal': [], 'segmentation': True}
    return parameters_cropping


def cropping_segmentation(parameters_cropping):
    """
    This function takes the cropping interval and segment the image in 4 different regions.
    The pipeline should lately run in all the different regions.
    Returns:
    """
    cropping_parameters_list = []
    [y1, y2, x1, x2] = parameters_cropping['cropping_points_spatial']
    if parameters_cropping['segmentation']:
        y1_new1 = y1
        y2_new1 = round((y2 + y1) / 2) - 15
        y1_new2 = round((y2 + y1) / 2) + 15
        y2_new2 = y2
        x1_new1 = x1
        x2_new1 = round((x2 + x1) / 2) - 15
        x1_new2 = round((x2 + x1) / 2) + 15
        x2_new2 = x2
        cropping_parameters_list.append(
            {'crop_spatial': True, 'cropping_points_spatial': [y1_new1, y2_new1, x1_new1, x2_new1],
             'segmentation': False,
             'crop_temporal': False, 'cropping_points_temporal': []})
        cropping_parameters_list.append(
            {'crop_spatial': True, 'cropping_points_spatial': [y1_new1, y2_new1, x1_new2, x2_new2],
             'segmentation': False,
             'crop_temporal': False, 'cropping_points_temporal': []})
        cropping_parameters_list.append(
            {'crop_spatial': True, 'cropping_points_spatial': [y1_new2, y2_new2, x1_new1, x2_new1],
             'segmentation': False,
             'crop_temporal': False, 'cropping_points_temporal': []})
        cropping_parameters_list.append(
            {'crop_spatial': True, 'cropping_points_spatial': [y1_new2, y2_new2, x1_new2, x2_new2],
             'segmentation': False,
             'crop_temporal': False, 'cropping_points_temporal': []})
    else:
        cropping_parameters_list.append(parameters_cropping)

    return cropping_parameters_list
