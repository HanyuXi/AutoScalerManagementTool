from flask import Flask
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
webapp = Flask(__name__)

from app import manager_app 
