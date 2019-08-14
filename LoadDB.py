import pandas
import sqlite3
import csv
import pyodbc
import sys


def create_local_db():
    try:
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=XXX;DATABASE=XXX;UID=sa;PWD=XXX')
        cur = cnxn.cursor()
        cur.execute("select  r.Release_id, r.Release_name , r.Release_type , r.Status , b.Build_Id , b.Build_Number , b.Build_Server , b.Build_Status , b.Build_Link, b.Build_Completed from Release r join Build b on r.Release_id = b.Release_Id ")
        result = cur.fetchall()

        #Getting Field Header names
        column_names = [i[0] for i in cur.description]
        fp = open('Result_Set.csv' ,'w+')
        myFile = csv.writer(fp, lineterminator = '\n') #use lineterminator for windows
        myFile.writerow(column_names)
        myFile.writerows(result)
        fp.close()
        cnxn.close()

        conn = sqlite3.connect("local.db")

        df = pandas.read_csv("Result_Set.csv")
        df.to_sql("data", conn, if_exists='replace', index=False)
        conn.close()
        return True
    except:
        print("Exception Occured while caching!!", sys.exc_info()[0])
        return False