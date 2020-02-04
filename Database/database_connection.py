#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: Morgane

Connection with the SQL database

"""
import mysql.connector
import getpass

database = mysql.connector.connect(
  host="131.174.140.253",
  user="morgane",
  passwd=getpass.getpass(),
    database="Calcium_imaging",
    use_pure=True
)


