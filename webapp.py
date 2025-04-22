from flask import Flask,request,jsonify,redirect,url_for,render_template
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2 
from datetime import datetime




app = Flask(__name__)

dbhost = 'localhost'
dbuser = 'postgres'
dbdatabase = 'testchatdb'
dbport  = '5432'
dbpassword = "allmight.1"

login_message = ""
search_message = ""
chatname = ""

def get_query(queryinput,input,qtype):
    with psycopg2.connect(
        dbname = dbdatabase,
        host = dbhost,
        user = dbuser,
        port = dbport,
        password = dbpassword
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            if qtype == "select":
                cur.execute(queryinput,input)
                result = cur.fetchone()
                return result
            elif qtype == "insert" or qtype == "update":
                cur.execute(queryinput,input)

def log(message,logfile="info.log"):
    logs = "logs\\" + logfile
    with open(logs,"a") as logger:
        logging = f"[{datetime.now()}] {message}\n"
        print(logging)
        logger.write(logging)


log("starting server")

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/login')
def login():
    global login_message
    return render_template("login.html",message = login_message)


@app.route("/chats/<username>")
def chats(username):
    global search_message
    """
    with psycopg2.connect(
        dbname = dbdatabase,
        host = dbhost,
        user = dbuser,
        port = dbport,
        password = dbpassword
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
        cur.execute("select contacts,last_chat from users where name = %s",(username,))
        data = cur.fetchone()
        contact = data[0]
        last_chat = data[1]

        
    """
    return render_template("chatpage.html",name = username,search_message =search_message)


@app.route("/create_user")
def create_user():
    return render_template("create_user.html")



@app.route("/api/create_user",methods=["POST"])
def create_user_api():
    global login_message
    name = request.form["username"]
    email = request.form["email"]
    raw_password = request.form["password"]
    password = generate_password_hash(raw_password)
    log(f"/api/create_user request: {request} ")

    with psycopg2.connect(
        dbname = dbdatabase,
        host = dbhost,
        user = dbuser,
        port = dbport,
        password = dbpassword
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("select name,email from users where name = %s and email = %s",(name,email))
            row = cur.fetchone()
            if row != None :
                login_message = f"\"{name}\" is already a user!"
                return redirect(url_for("login"))
            elif row == None:
                cur.execute("insert into users(name,email,password,created_at) values(%s,%s,%s,now())",(name,email,password))
                cur.execute("select name,email from users where name = %s and email = %s",(name,email))
                confirmrow = cur.fetchone()
                print(confirmrow)
                if confirmrow[0] == name and confirmrow[1] == email:
                    login_message = "user created successfully!"
                    return redirect(url_for("login"))


@app.route("/api/login", methods=["post"])
def login_api():
    global login_message
    name = request.form["username"]
    raw_password = request.form["password"]
    with psycopg2.connect(
        dbname = dbdatabase,
        host = dbhost,
        user = dbuser,
        port = dbport,
        password = dbpassword
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("select name,password from users where name = %s",(name,))
            row = cur.fetchone()
            if row == None:
                login_message = f"\"{name}\" does not exists!"
                return redirect(url_for("login"))
            elif row[0] == name and not check_password_hash(row[1],raw_password):
                login_message = f"incorrect password!"
                return redirect(url_for("login"))
            elif row[0] == name and check_password_hash(row[1],raw_password):
                return redirect(url_for("chats",username = row[0]))


@app.route("/api/send_message",methods=["POST"])
def send_message():
    username = request.form["user"]
    print(f"sender : {username}")
    message = request.form["message"]
    print(f"message: {message}")
    with psycopg2.connect(
        dbname = dbdatabase,
        host = dbhost,
        user = dbuser,
        port = dbport,
        password = dbpassword
    ) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("select id,last_chat from users where name = %s",(username,))
            usertable = list(cur.fetchone())
            print(usertable)
            owner_id = usertable[0]
            last_chat = usertable[1]
            cur.execute("select id from users where name = %s",(last_chat,))
            receiver_id = cur.fetchone()
            cur.execute("insert into chats(owner_id,receiver_id,created_at,content) values(%s,%s,now(),%s)",(owner_id,receiver_id,message))
            return redirect(url_for("chats",username = username))




@app.route("/api/add_contacts",methods=["POST"])
def add_contact():
    global search_message
    name = request.form["user"]
    contact = request.form["search"]

    receiver = get_query("select name from users where name = %s",(contact,),"select") 
    receivers = get_query("select unnest(contacts) from users where name = %s",(name,),"select")
    print(f"receivers check : {receivers}")

    if receiver != None and receivers != None:
        receivers = list(receivers)
        print(f"receivers check two : {receivers}")
        for i in receivers:
            if receiver == i:
                search_message = "contact already added"
                return redirect(url_for("chats",username = name))
        if receiver not in receivers: 
            search_message = "contact added"
            get_query("update users set last_chat = %s,contacts = array_append(contacts,%s) where name = %s",(contact,contact,name),"update")
            return redirect(url_for("chats",username = name))

            
    elif receiver != None and receivers == None:
            search_message = "contact added"
            get_query("update users set last_chat = %s,contacts = array_append(contacts,%s) where name = %s",(contact,contact,name),"update")
            return redirect(url_for("chats",username = name))
    elif receiver == None:
        search_message = "that person does not exist"
        return redirect(url_for("chats",username = name))
"""
    
@app.route("/api/get_contacts",methods=["GET"])
def get_contacts():
    pass
    
@app.route("/api/get_chats",methods=["GET"])
def get_chats():
    pass
"""







if __name__ == "__main__":
    app.run(debug=True)