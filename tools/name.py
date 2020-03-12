#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane

This program is for create a excel sheet where all the behavioral path are storage
"""
# Importation
import pandas as pd

df = pd.read_excel(r'calcium_analysis_checked_videos.xlsx')
mouse=pd.DataFrame(df, columns= ['mouse'])
date=pd.DataFrame(df, columns= ['date'])
trial=pd.DataFrame(df, columns= ['trial'])
datetime=pd.DataFrame(df, columns= ['timestamp'],dtype='float64')
path=pd.DataFrame(df, columns= ['Calcium_video'])
date_b=pd.DataFrame(df, columns= ['date_bis'], dtype='str')
df['behavioral_path']=path
b_path=pd.DataFrame(df, columns= ['behavioral_path'])
for i in range(0,len(mouse)):
    mouse1 = mouse.iloc[i]
    date1=date.iloc[i]
    trail1=trial.iloc[i]
    datetime1=datetime.iloc[i]
    path0=path.iloc[i]
    date_b0=date_b.iloc[i]
    b_path0 = b_path.iloc[i]
    data=[]
    data1=[]
    for p in path0:
        for m in mouse1:
            for t in trail1:
                for d in date1:
                    for db in date_b0:
                        for dt in datetime1:
                            for bp in b_path0:
                                data=p
                                for i in range(0,len(data)):
                                    if data[i] == '/':
                                        data1=data[:i]
                                path1=data1
                                file_name=f'{d}_{m}_Trial{t}_{db}-%.f_0000.avi' % dt

                                file=path1+'/'+file_name
                                print(file)

