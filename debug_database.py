import sqlite3
import os
import json




conn = sqlite3.connect('bungle.db')
c = conn.cursor()

# c.execute('SELECT * FROM reviews where app_id=?',t)
# app_name='org.stepic.droid'
# sql = "select id, content,star_num,helpful_num from reviews where app_id=\'{}\' order by length(content) desc"
# sql = "select * from apps"


# Insert a row of data
# c.execute("INSERT INTO apps VALUES ('org.videolan.vlc','VLC for Android','Video_Players_and_Editors	')")
# Insert a row of data
# c.execute("INSERT INTO apps VALUES ('com.wire','Wire','Business')")

# c.execute(sql)
# app_list = c.fetchall()

# for i in app_list:
#     print(i)


conn.commit()
conn.close()
