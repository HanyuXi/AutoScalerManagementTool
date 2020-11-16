from app import webapp,  mysql
from flask import render_template, request, flash, redirect, jsonify, make_response, session, url_for
from .const import ErrorMessages
import os, cv2, json
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import boto3
import requests
r = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/assignment2S3')
json_obj = r.json()
print(json_obj)
TOKEN = json_obj["Token"]
AccessKeyId = json_obj["AccessKeyId"]
SecretAccessKey=json_obj["SecretAccessKey"]
BUCKET_NAME='ece1779a2hanyu'
con = con = pymysql.connect(
        host= "assignment1-ece1779.cgm5nkly1umo.us-east-1.rds.amazonaws.com", #endpoint link
        port = 3306, # 3306
        user = "admin", # admin
        password = "adminadmin", #adminadmin
        db="assignment1-ece1779"
        )
s3 = boto3.client(
  's3',
  region_name = 'us-east-1',
  aws_access_key_id= AccessKeyId,
  aws_secret_access_key=SecretAccessKey,
  aws_session_token=TOKEN)
#for b in s3.list_objects(Bucket='ece1779a2hanyu')['Contents']:
#    print(b)
##Function tools
def generate_success_responses(val):
    response = make_response(
                jsonify(
                    {"success": True, "payload": val}
                ),
                202,
            )
    response.headers["Content-Type"] = "application/json"
    return response

def generate_error_responses(val):
    response = make_response(
                jsonify(
                    {"success": False, "error": {"code": "servererrorcode", "message": val}}
                ),
                404,
            )
    response.headers["Content-Type"] = "application/json"
    return response


def check_file_type(file_list):
    failure_file_list = []
    for f in file_list:
        if f.filename.split(".")[-1] not in webapp.config["ALLOWED_IMAGE_EXTENSIONS"]:
            failure_file_list.append(f.filename)
    if len(failure_file_list) == 0:
        return (True, [])
    else:
        return (False, failure_file_list)


def run_image_detection(img_path, filename, username):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    new_file_name = filename.split(".")[0]+"_processed."+filename.split(".")[-1]
    output_img_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username,'work/',new_file_name)
    print(output_img_path)
    print(os.getcwd())
    ##Change to FaceMaskDectection working directory
    os.chdir("app/FaceMaskDetection")
    #from is still accessing from app level
    from .FaceMaskDetection.pytorch_infer import inference
    res_list = inference(img, output_img_path, show_result=True, target_shape=(360, 360))
    ##Change back to Flask working directory
    os.chdir("../..")
    payload = {"filename": new_file_name}
    num_faces = len(res_list)
    num_unmasked = len([x[0] for x in res_list if x[0] == 0])
    num_masked = len([x[0] for x in res_list if x[0] == 1])
    payload = {"filename": new_file_name, "num_faces":num_faces, "num_unmasked":num_unmasked, "num_masked":num_masked}
    return payload

@webapp.route('/home/upload', methods=['GET'])
def upload_interface():
    return render_template('file_upload.html')



@webapp.route('/upload/success', methods=['GET'])
def success_upload_interface():
    username = session["username"]
    payload = request.args['messages']
    payload = json.loads(payload)
    new_file_name = payload["filename"]
    full_filename = os.path.join('/static/images/', username, 'work', new_file_name)
    s3_filename = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username, 'work', new_file_name)
    s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=s3_filename,
                    Key = s3_filename
                )
    print(full_filename)
    return render_template('file_upload_success.html', new_image = full_filename, payload=payload )

@webapp.route('/upload/image', methods=['POST'])
def img_upload():
    file_obj = request.files
    if 'file' not in file_obj:
        flash("This endpoint is only for file based post request")
        return redirect('/home/upload')
    #Convert the ImmutableMultiDic]t class to list
    file_list = file_obj.getlist('file')
    # Check if user uploads empty files
    if file_list[0].filename == '':
       flash(ErrorMessages.EMPTY_FILE_UPLOAD)
       return redirect(request.url)
    # Check is file type is allowed type
    status, failure_items = check_file_type(file_list)
    if not status:
        flash(ErrorMessages.INVALID_FILE_FORMAT + str(failure_items))
        return redirect('/home/upload')
    #Save the files to local directory
    if len(file_list) > 1:
        flash(ErrorMessages.MULTI_FILE_ERROR)
        return redirect(request.url)
    #get username
    user_id = session["id"]
    username = session["username"]
    img_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username, 'work',file_list[0].filename)
    file_list[0].save(img_path)
    print(img_path)
    s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=img_path,
                    Key = img_path
                )
    payload = run_image_detection(img_path, file_list[0].filename, username)
    print(payload)
    messages = json.dumps(payload)
    #session['messages'] = messages
    #except Exception as e:
    ##    print(e)
    #    return generate_error_responses(str(e))
    #### show processed img on website and srore the history imgs
    img_type= None
    if payload["num_faces"] == 0:
        img_type = "noface"
    elif payload["num_faces"] == payload["num_masked"]:
        img_type = "allmasks"
    elif payload["num_masked"] == 0:
        img_type = "nomasks"
    else:
        img_type = "somemasks"
    #new_value = cur.execute('SELECT COUNT(*) FROM images')
    #f = list(new_value)[0]+1
    #print(f)
    #saved_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username, str(f)+".jpeg")
    #file_list[0].save(saved_path)
    try: 
        cur = con.cursor()
        saved_path = os.path.join('/static/images', username, 'work',file_list[0].filename)
        cur.execute("INSERT INTO images SET image_path= %s, image_type=%s, user_id=%s", (saved_path, img_type, user_id))
        con.commit()
        return redirect(url_for('success_upload_interface', messages=messages))
    except Exception as e:
        print(e)
        flash(str(e))
        return redirect(request.url)
    


@webapp.route('/upload/history', methods=['GET'])
def history_images():
    user_id = session["id"]

    cur = con.cursor()


    somemasks_num = cur.execute("SELECT image_path FROM images WHERE user_id =%s and image_type=%s",(user_id, "somemasks"))
    somemasks_q = cur.fetchall()
    somemasks_list=[]
    if somemasks_num != 0:
        for i in somemasks_q:
            somemasks_list.append(list(i)[0])
    noface_num = cur.execute("SELECT image_path FROM images WHERE user_id =%s and image_type=%s",(user_id, "noface"))
    noface_q  = cur.fetchall()
    noface_list = []
    if noface_num !=0:
        for i in noface_q:
            noface_list.append(list(i)[0])
    allmasks_num = cur.execute("SELECT image_path FROM images WHERE user_id =%s and image_type=%s",(user_id, "allmasks"))
    allmasks_q = cur.fetchall()
    allmasks_list = []
    if allmasks_num !=0:
        for i in allmasks_q:
            allmasks_list.append(list(i)[0])
    nomasks_num = cur.execute("SELECT image_path FROM images WHERE user_id =%s and image_type=%s",(user_id, "nomasks"))
    nomasks_q = cur.fetchall()
    nomasks_list = []
    if nomasks_num !=0:
        for i in nomasks_q:
            nomasks_list.append(list(i)[0])
  
    return render_template('history_image.html',  noface=noface_list, allmasks=allmasks_list, nomasks=nomasks_list, somemasks=somemasks_list)




@webapp.route('/api/upload', methods=['POST'])
def img_upload_api():
    file_obj = request.files
    if 'file' not in file_obj:
        return generate_error_responses(ErrorMessages.EMPTY_FILE_UPLOAD)
    print(request)
    if "username" not in request.form or "password" not in request.form:
            return generate_error_responses(ErrorMessages.INCORRECT_PARAMS)
    username = request.form['username']
    password = request.form['password']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    account = cursor.fetchone()
    if account and check_password_hash(account["password"], request.form['password']):
        user_id = account["id"]
    else:
        return generate_error_responses(ErrorMessages.USER_NOT_EXISTS)

    #Convert the ImmutableMultiDic]t class to list
    file_list = file_obj.getlist('file')
    # Check if user uploads empty files
    if file_list[0].filename == '':
        return generate_error_responses(ErrorMessages.EMPTY_FILE_UPLOAD)
    # Check is file type is allowed type
    status, failure_items = check_file_type(file_list)
    if not status:
        return generate_error_responses(ErrorMessages.INVALID_FILE_FORMAT + str(failure_items))
    #Save the files to local directory
    if len(file_list) > 1:
        return generate_error_responses(ErrorMessages.MULTI_FILE_ERROR)
    img_path = os.path.join(webapp.config["IMAGE_UPLOADS_PATH"], username, 'work',file_list[0].filename)
    file_list[0].save(img_path)
    s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=img_path,
                    Key = img_path
                )
    payload = run_image_detection(img_path, file_list[0].filename, username)

    img_type= None
    if payload["num_faces"] == 0:
        img_type = "noface"
    elif payload["num_faces"] == payload["num_masked"]:
        img_type = "allmasks"
    elif payload["num_masked"] == 0:
        img_type = "nomasks"
    else:
        img_type = "somemasks"
    try: 
        cur = mysql.connection.cursor()
        con = mysql.connection
        saved_path = os.path.join('/static/images', username, 'work',file_list[0].filename)
        cur.execute("INSERT INTO images SET image_path= %s, image_type=%s, user_id=%s", (saved_path, img_type, user_id))
        con.commit()
        payload.pop("filename")
        return generate_success_responses(payload)
    except Exception as e:
        return generate_error_responses(str(e))
