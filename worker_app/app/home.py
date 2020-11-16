from app import webapp
from flask import render_template, request, flash, redirect, jsonify, make_response, session, url_for

@webapp.route('/home', methods=['GET'])
def home():
    is_admin = True if session['is_admin'] == 1 else False
    payload = {"username":session['username'], "is_admin":is_admin, }
    return render_template('home.html', is_admin = is_admin, payload = payload)

