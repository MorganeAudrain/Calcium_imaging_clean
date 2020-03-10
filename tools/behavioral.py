#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane

check behavioral path
"""
import pandas as pd

df = pd.read_excel(r'behavioral_path.xlsx')
b_path=pd.DataFrame(df, columns= ['behavioral_path'])

for i  in range(0,588):
    b_path1 = b_path.iloc[i]
    for p in b_path1:
        print(p)
        open(p)
