from flask import Flask
import os
from flask_mysqldb import MySQL

base_dir = os.path.dirname(os.path.abspath(__file__))


webapp = Flask(__name__)

webapp.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "jpeg", "jpg", "png"]
webapp.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
webapp.config["IMAGE_UPLOADS_PATH"] = os.path.join(base_dir, "static/images")
webapp.config["BASE_DIR"] = base_dir
# Enter your database connection details below
mysql = MySQL(webapp)
webapp.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
webapp.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
webapp.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
webapp.config['MYSQL_DB'] = os.getenv('MYSQL_DB')


from app import user_login 
from app import img_process
from app import home