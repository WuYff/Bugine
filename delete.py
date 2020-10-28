import sqlite3
import os
import json

conn = sqlite3.connect('review_extend.db')
c = conn.cursor()
c.execute('SELECT * FROM apps')
app_list = c.fetchall()
for i, name, table_name ,cate in app_list:
    print(i)
    c.execute("delete from {} where star_num > 3;".format(table_name))
conn.commit()
conn.close()
