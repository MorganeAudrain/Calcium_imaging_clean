#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane

This program is for create a excel sheet where all the behavioral path are storage
"""
# Importation
import pandas as pd

# Read the excel
df = pd.read_excel(r'calcium_analysis_checked_videos.xlsx')
data=pd.DataFrame(df, columns= ['condition'])
print(data)