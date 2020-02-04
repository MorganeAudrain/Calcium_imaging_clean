#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Morgane

Create a new database for Calcium imaging data in SQL

"""

import sqlite3
database = sqlite3.connect('Calcium_imaging.db')
mycursor = database.cursor()




#%% Create table

mycursor.execute("CREATE TABLE Analysis(mouse INT, session  INT, trial INT, is_rest INT,input VARCHAR(255),home_path VARCHAR(255) , decoding_v INT, decoding_main VARCHAR(255), cropping_v INT, cropping_main VARCHAR(255), motion_correction_v INT, motion_correction_main VARCHAR(255), alignment_v INT, alignment_main VARCHAR(255), source_extraction_v INT, source_extraction_main VARCHAR(255), component_evaluation_v INT, component_evaluation_main VARCHAR(255), equalization_v INT, equalization_main VARCHAR(255), analyst VARCHAR(255), date INT, time INT)")
#change here the name of the table that you want create

#%% Add columns at the table varchar

mycursor.execute("ALTER TABLE Analysis ADD COLUMN input VARCHAR(255)")

#%% add columns at the table int

mycursor.execute("ALTER TABLE Experimental ADD COLUMN equalization_v INT")

#%% check if the table exist

mycursor.execute("SHOW TABLES")

for x in mycursor:
  print(x)


#%% Delete Table

mycursor.execute("DROP TABLE Analysis")

#%% Insert information into the table

sql = "INSERT INTO Analysis (steps) VALUES (%s)"
val = [("decoding"),
       ("cropping"),
       ("motion_correction"),
       ("alignment"),
       ("source_extraction"),
       ("component_evaluation"),]

#%%In case of one single row

mycursor.execute(sql, val)

database.commit()

print(mycursor.rowcount, "record inserted.")

#%% In case of multiple rows

mycursor.executemany(sql, val)

database.commit()

print(mycursor.rowcount, "was inserted.")

#%% check is the columns exists
mycursor.execute("SHOW COLUMNS FROM Analysis ")

for x in mycursor:
  print(x)

#%% update the table Experimental

sql= "UPDATE Analysis SET motion_correction_v=0 "

mycursor.execute(sql)

database.commit()

print(mycursor.rowcount, "records(s) affected")

#%% convert the old database into the sql onefin

import csv
with open('/home/morgane/Calcium_imaging.csv') as fin:
    dr = csv.reader(fin, delimiter=',')
    to_db = [(i['mouse'], i['session'],i['trial'],i['is_rest']) for i in dr]

mycursor.execute("INSERT INTO Analysis ((mouse, session,trial,is_rest,input,home_path) VALUES (?,?,?,?,?,?);", to_db)
database.commit()


#%% update

mycursor.execute("")

#%% check if data in column

mycursor.execute("SELECT * FROM Analysis WHERE motion_correction_v=0 ORDER BY trial,session,motion_correction_v ")

myresult = mycursor.fetchall()
data=[]
for x in myresult:
  data +=x


