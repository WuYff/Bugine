# import sqlite3
# conn = sqlite3.connect('issue.db')
# c = conn.cursor()
# symbol = 'RHAT'
# c.execute("select issue_num, comments, state, title, body, commit_id, labels from {} order by length(body) desc".format("hakr$AnExplorer") )
#
# print(c.fetchone())
#
# c.execute("select issue_num, commit_id, labels from {} order by length(body) desc".format("hakr$AnExplorer") )
#
# print(c.fetchone())
#
# c.execute("select * from {} order by length(body) desc".format("hakr$AnExplorer") )
# r = c.fetchall()
# print(len(r))

import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('stopwords')
