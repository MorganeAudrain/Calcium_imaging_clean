#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Melisa,Morgane
"""

#%% Importation and parameters

from Steps.run_steps_trial_wise import run_steps
import psutil
import caiman as cm


print('Choose the mouse, session, how many trial and resting or non resting trial you want to analyse')
mouse_number = int(input("mouse number : "))
sessions = input(" sessions : ")
print('Number of trial that you want to analyse, if you want to analyse only one trial enter the same number for the first trial and the final one')
init_trial = int(input("begin with trial : "))
end_trial = int(input(" final trial to analyse: "))
print('Choose if you want to the resting period (enter 1) or the non resting (enter 0) if you do not want to choose enter None ')
is_rest = int(input(" is-rest: "))

print('Choose which steps you want to run: 0 -> decoding, 1 -> cropping, 2 -> motion_correction, 3 -> alignment, 4 -> equalization, 5 -> source_extraction, 6 -> component_evaluation, all ->  every steps ')
n_steps = input(' steps :')

#%% start a cluster

n_processes = psutil.cpu_count()
c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=n_processes, single_thread=False)

#%% Run steps that you want

run_steps(n_steps, mouse_number, sessions, init_trial, end_trial, is_rest)

