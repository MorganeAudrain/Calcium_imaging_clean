#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane
"""
#%% Importation

import psutil
import configuration
import caiman as cm

from Steps.decoding import run_decoder as main_decoding
from Steps.cropping import run_cropper as main_cropping
from Steps.equalizer import  run_equalizer as main_equalizing
from Steps.cropping import cropping_segmentation
from Analysis_tools.figures import plot_movie_frame
from Steps.motion_correction import run_motion_correction as main_motion_correction
from Steps.alignment import run_alignment as main_alignment
from Steps.source_extraction import run_source_extraction as main_source_extraction
from Steps.component_evaluation import run_component_evaluation as main_component_evaluation
from Database.database_connection import database
mycursor = database.cursor()

def run_steps(steps):

    if steps == 1:
        print('Choose the mouse, session, how many trial and resting or non resting trial you want to analyse')
        mouse_number = int(input("mouse number : "))
        sessions = input(" session : ")
        main_decoding(mouse_number, sessions,'*' , '*')
