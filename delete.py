import sqlite3
import os
import json

# conn = sqlite3.connect('review_extend.db')
# c = conn.cursor()
# c.execute('SELECT * FROM apps')
# app_list = c.fetchall()
# for i, name, table_name ,cate in app_list:
#     print(i)
#     c.execute("delete from {} where star_num > 3;".format(table_name))
# conn.commit()
# conn.close()


conn = sqlite3.connect('bungle.db')
c = conn.cursor()
# t=('org.stepic.droid',)
# c.execute('DELETE FROM reviews WHERE star_num > 3')
# c.execute('INSERT INTO apps (id,name,category) VALUES (\'com.wire\', \'Wire\', \'Communication\')' )
# c.execute('INSERT INTO apps (id,name,category) VALUES (\'org.videolan.vlc\', \'VLC for Android\', \'Multi_Media\')' )
# c.execute('SELECT * FROM reviews where app_id=?',t)
app_name='org.stepic.droid'
sql = "select id, content,star_num,helpful_num from reviews where app_id=\'{}\' order by length(content) desc"

c.execute(sql.format(app_name))
app_list = c.fetchall()
print(len(app_list))
# for i in app_list:
#     print(i)

conn.commit()
conn.close()
