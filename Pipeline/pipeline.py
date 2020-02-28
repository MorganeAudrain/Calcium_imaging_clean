#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Melisa,Morgane
"""
#%% Importation and parameters

from Steps.run_steps import run_steps
import psutil
import caiman as cm


print('Choose the mouse, session, how many trial you want to analyse')
mouse_number = int(input("mouse number : "))
sessions = input(" sessions : ")
print('Number of trial from Steps.run_steps_session_wise import run_steps that you want to analyse, if you want to analyse only one trial enter the same number for the first trial and the final one')
init_trial = int(input("begin with trial : "))
end_trial = int(input(" final trial to analyse: "))

print('Choose which steps you want to run: 0 -> decoding, 1 -> cropping, 2 -> motion correction, 3 -> alignment, 4 -> equalization, 5 -> source extraction, 6 -> component evaluation, 7 -> registration, all ->  every steps ')
n_steps = input(' steps :')

# start a cluster

n_processes = psutil.cpu_count()
c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=n_processes, single_thread=False)

process ='yes'
# Run steps that you want
while process == 'yes':

    run_steps(n_steps, mouse_number, sessions, init_trial, end_trial,dview)
    print('This step is finish. Do you want to run another step with those settings ? (yes or no)')
    process=input("answer : ")
    if process == 'yes':
        print('Choose which steps you want to run: 0 -> decoding, 1 -> cropping, 2 -> motion correction, 3 -> alignment, 4 -> equalization, 5 -> source extraction, 6 -> component evaluation, 7 -> registration, all ->  every steps ')
        n_steps = input(' steps :')
        run_steps(n_steps, mouse_number, sessions, init_trial, end_trial, dview)
    if process == 'no':
        print('Thanks for having used this pipeline. I hope everything went alright for you :)')
        dview.terminate()

