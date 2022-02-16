from app import app
from flaskext.mysql import MySQL

app.secret_key = 'EcgPS^fTkDa8qZz7JHHrFtz91&B%sTqzuAjrZD#LoqzLTtXlpl'
mysql = MySQL()
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'flaskwebscraping_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
