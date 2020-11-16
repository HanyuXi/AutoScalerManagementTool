import pymysql


#import aws_credentials as rds
conn = pymysql.connect(
        host= "assignment1-ece1779.cgm5nkly1umo.us-east-1.rds.amazonaws.com", #endpoint link
        port = 3306, # 3306
        user = "admin", # admin
        password = "adminadmin", #adminadmin
        db="assignment1-ece1779"
        )

##Update here from SQL file
#Table Creation
#cursor=conn.cursor()
#create_table="""
#INSERT INTO `users` (`id`, `username`, `password`, `email`, `admin`, `api_registered`) VALUES (1, 'test', 'pbkdf2:sha256:150000$LcMw2gg3$c9dedb1034a04d74ce9f9f0cf5ab64ceefa04a8665e2d20183756e289e10aaeb', 'laoxi02@gmail.com', true, false);
#"""
#cursor.execute(create_table)
#conn.commit()


def insert_details(name,email,comment,gender):
    cur=conn.cursor()
    cur.execute("INSERT INTO Details (name,email,comment,gender) VALUES (%s,%s,%s,%s)", (name,email,comment,gender))
    conn.commit()

def get_details():
    cur=conn.cursor()
    cur.execute("SELECT *  FROM users")
    details = cur.fetchall()
    print(details)
    return details
get_details()