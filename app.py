from flask import Flask, render_template, request, session, redirect
import pyrebase
#from flask_mongoengine import MongoEngine
from flask import session
from modules.PasswordGenerator import PasswordGenerator

app = Flask(
    __name__,
    static_url_path='',
    static_folder='static',
    template_folder='templates',
)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "mysecret"

config = {
    "apiKey": "AIzaSyByhDkHc-IQGnu6BFWPZZk1Ens7td7God8",
    "authDomain": "cloud-computing-7-trekb.firebaseapp.com",
    "databaseURL": "https://cloud-computing-7-trekb-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storageBucket": "cloud-computing-7-trekb.appspot.com",
}
#initialize firebase
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

# Database


class NewUser:
    def __init__(self, name, email, username, password):
        self.name = name
        self.email = email
        self.username = username
        self.password = password

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'username': self.username,
            'password': self.password,
        }

class Passwords:
    def __init__(self, user, website, username, password):
        self.user = user
        self.website = website
        self.username = username
        self.password = password

    def to_dict(self):
        return {
            "user": self.user,
            "website": self.website,
            "username": self.username,
            "password": self.password,
        }


@app.before_request
def create_session():
    session.permanent = app.config["SESSION_PERMANENT"]
    session.modified = True

# Server

#index
@app.route('/')
def home():
    return render_template('index.html')

#Login
@app.route('/login')
def login():
    return render_template('login.html', error_message='')


@app.route('/login.py', methods=['POST', 'GET'])
def login_user():
    try:
        # Get the username and password from the form
        username = request.form['login--username']
        password = request.form['login--password']

        # Check if the user exists in the Firebase database
        user_data = db.child("users").child(username).get().val()

        if user_data and user_data['password'] == password:
            # Create Session
            session['username'] = username

            # Redirect to Dashboard
            return render_template('/main.html', user=user_data['name'], username=username)
        else:
            return render_template('login.html', error_message="Invalid username or password")
    except:
        return redirect('/')


@app.route('/register')
def register():
    return render_template('register.html', error_message='')


@app.route('/register.py', methods=['POST'])
def register_user():
    username = request.form['register--username']
    user = db.child("users").child(username).get()
    if user.val():
        return render_template("register.html", error_message="Username already exists")
    else:
        new_user = NewUser(
            name=request.form['register--name'],
            email=request.form['register--email'],
            username=username,
            password=request.form['register--password'],
        )
        db.child("users").child(username).set(new_user.to_dict())
        return render_template('login.html')


@app.route('/gen_pass')
def generate_password():
    PSWD = PasswordGenerator()
    return {"password": f'{PSWD.get_password()}'}


@app.route('/save_pass', methods=['POST'])
def save_password():
    # Handle Same username for same website
    data = request.get_json()
    user = session['username']
    website = data['website']
    username = data['username']
    password = data['password']

    passwords = db.child("passwords").get().val()
    if passwords:
        for key, value in passwords.items():
            if value['user'] == user and value['website'] == website and value['username'] == username:
                return {"message": "Exists"}
    else:
        passwords = {}

    new_pass = Passwords(
        user=user,
        website=website,
        username=username,
        password=password,
    )
    db.child("passwords").push(new_pass.to_dict())
    return {'message': 'Saved'}, 200



@app.route('/get_pass', methods=['GET'])
def get_password():
    if not session['username']:
        return redirect('/')
    passwords = db.child("passwords").order_by_child("user").equal_to(session['username']).get().val()
    data = []
    for key, password in passwords.items():
        data.append(password)
    return {"passwords": data}, 200

@app.route('/search_pass', methods=['POST'])
def search_password():
    if not session['username']:
        return redirect('/')
    data = request.get_json()
    passwords = db.child("passwords").order_by_child("user").equal_to(data['username']).get().val()
    filtered_passwords = []
    if passwords:
        for password in passwords.values():
            if password['website'] == data['website']:
                filtered_passwords.append(password)
    return {"passwords": filtered_passwords}, 200

@app.route('/del_pass', methods=['POST'])
def delete_password():
    if not session['username']:
        return redirect('/')
    data = request.get_json()
    passwords = db.child("passwords").order_by_child("user").equal_to(session['username']).get().val()
    for key, password in passwords.items():
        if password['website'] == data['website'] and password['username'] == data['username']:
            db.child("passwords").child(key).remove()
    return {"message": "OK"}, 200



@app.route('/logout.py')
def logout():
    session['username'] = None
    return redirect('/')

@app.route('/set/')
def set():
    session['key'] = 'value'
    return 'ok'

@app.route('/get/')
def get():
    return session.get('key', 'not set')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
