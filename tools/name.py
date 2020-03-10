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

for i in range(0,len(mouse)):
    mouse1 = mouse.iloc[i]
    date1=date.iloc[i]
    trail1=trial.iloc[i]
    datetime1=datetime.iloc[i]
    path0=path.iloc[i]
    data=[]
    data1=[]
    for p in path0:
        for m in mouse1:
            for t in trail1:
                for d in date1:

                    for dt in datetime1:
                        data=p
                        for i in range(0,len(data)):
                            if data[i] == '/':
                                data1=data[:i]
                        path1=data1
                        file_name=f'{d}_{m}_trial{t}_{d}%.f_0000.avi' % dt

                        file=path1+'/'+file_name
                        df['behavioral_path']=file
                        df.to_excel('behavioral_path.xlsx')

