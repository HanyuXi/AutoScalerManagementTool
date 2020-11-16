from app import webapp, mysql
from flask import render_template, redirect, url_for, request, session, make_response,jsonify
from .img_process import generate_error_responses
from .const import ErrorMessages
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import os
import pymysql
#import img_process
con = pymysql.connect(
        host= "assignment1-ece1779.cgm5nkly1umo.us-east-1.rds.amazonaws.com", #endpoint link
        port = 3306, # 3306
        user = "admin", # admin
        password = "adminadmin", #adminadmin
        db="assignment1-ece1779"
        )

@webapp.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        cursor=con.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        print(account["password"])
        if account and check_password_hash(account["password"], request.form['password']):
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['is_admin'] = account['admin']
            print(session)
            # Redirect to page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            error = "Invalid credentials or username does not exist. Please try again"
    return render_template('login.html', error=error)

@webapp.route('/password/recovery', methods=['GET', 'POST'])
def password_recovery():
    error = None
    if request.method == 'POST' and 'username' in request.form and 'new_password' in request.form:
        username = request.form['username']
        email = request.form['email']
        cur =con.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s and email=%s', (username,email))
        # Fetch one record and return result
        account = cur.fetchone()
        if account:
            new_password = generate_password_hash(request.form["new_password"])
            cur.execute("UPDATE users SET password=%s WHERE username = %s", (new_password, username,))
            con.commit()
            # Redirect to page
            error = "The password has been updated"
        else:
            # Account doesnt exist or username/password incorrect
            error = "No Matching Username and Email can be found. "
    
    return render_template('password_recovery.html', error=error)

@webapp.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('is_admin', None)
   # Redirect to login page
   return redirect(url_for('login'))

@webapp.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    error = None
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cur = con.cursor()
        new_value= cur.execute("SELECT * FROM users WHERE username = %s or email=%s",(username,email))
        if new_value> 0:
            error =  "the username or email exists"
        else:
            # store the information to database
            try:
                cur.execute("INSERT INTO users (username, password, email, admin, api_registered) VALUES (%s, %s, %s, false, false)", (username,generate_password_hash(password) ,email))
                con.commit()
                new_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username)
                os.mkdir(new_path)
                new_path = os.path.join(new_path, "work")
                os.mkdir(new_path)
                return render_template('register_success.html')
            except Exception as e:
                error = ("Problem inserting into DB" +str(e))
                return render_template('register.html', msg=error)
    elif request.method == 'POST':
        error = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=error)

@webapp.route('/delete', methods=['GET', 'POST'])
def delete():
    # Output message if something goes wrong...
    error = None
    cur = con.cursor()
    if request.method == 'GET':
        cur.execute("SELECT username FROM users WHERE admin = false")
        list_of_users = cur.fetchall()
        res = []
        for x in list_of_users:
            a = list(x)
            res.append(a[0])
        return render_template('delete.html', list_of_users = res)

    if request.method == 'POST':
        # Create variables for easy access
        if "username" not in request.form:
            error = "There is no user to delete"
            return render_template('delete.html', msg=error)

        username = request.form['username']
        try:
            cur.execute("DELETE FROM users WHERE username = %s", (username, ))
            con.commit()
            new_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username)
            import shutil
            shutil.rmtree(new_path)
            return render_template('delete_success.html')
        except Exception as e:
            error = ("Problem deleting the query. Here is the error message: " +str(e))
            return render_template('delete.html', msg=error)

@webapp.route('/change/password', methods=['GET', 'POST'])
def change_password():
    error = None
    cur = con.cursor()
    is_admin = True if session['is_admin'] == 1 else False
    payload = {"username":session['username'], "is_admin":is_admin}

    if request.method == 'POST':
        # Create variables for easy access
        if "new_password" not in request.form or request.form["new_password"].strip() == "": 
            error = "The password can not be empty"
            return render_template('change_password.html', payload = payload, msg=error)

        username = session['username']
        new_password = generate_password_hash(request.form["new_password"])
        try:
            cur.execute("UPDATE users SET password=%s WHERE username = %s", (new_password, username,))
            error = "The password has been updated successfully! Go back to home page"
            con.commit()
            return render_template('change_password.html', payload = payload, msg=error)
        except Exception as e:
            error = ("Problem updating the query. Here is the error message: " +str(e))
            return render_template('change_password.html', msg=error)

    return render_template('change_password.html', payload = payload, msg=error)


def register_generate_success_responses():
    response = make_response(
                jsonify(
                    {"success": True}
                ),
                202,
            )
    response.headers["Content-Type"] = "application/json"
    return response


@webapp.route('/api/register', methods=['POST'])
def api_register():
    try:
        if "username" not in request.json or "password" not in request.json:
            return generate_error_responses(ErrorMessages.INCORRECT_PARAMS)
        username = request.json['username']
        password = request.json['password']
        cur = con.cursor()
        new_value= cur.execute("SELECT * FROM users WHERE username = %s",(username,))
        if new_value> 0:
            return generate_error_responses(ErrorMessages.USER_EXISTS)
        else:
            cur.execute("INSERT INTO users (username, password, admin, api_registered) VALUES (%s, %s, false, true)", (username,generate_password_hash(password)))
            con.commit()
            new_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username)
            os.mkdir(new_path)
            new_path = os.path.join(new_path, "work")
            os.mkdir(new_path)
            return register_generate_success_responses()
    except Exception as e:
        error = "Problem inserting into DB" + str(e)
        return generate_error_responses(error)