from flask import Flask, render_template, request, jsonify, redirect, session
from user_manage import login, User, all_users
from init import sys_init

app = Flask(__name__)
app.secret_key = 'your_secret_key'


with app.app_context():
    sys_init()


@app.route('/')
def index():
    #Connect to the Dtaabase here.
    # def connect_db()
    # connection = mysql.connector.connect
    if request.args:
        return render_template('index.html', messages =request.args['messages'])
    else:
        return render_template('index.html', messages = '')


@app.route('/users')
def users():
    all = all_users()
    return render_template('users.html', users = all)

@app.route('/users2')
def users2():
    all = all_users()
    return render_template('usersajax.html', users = all)


@app.route('/usersajax', methods=['POST'])
def get_users():
    users = all_users()  # Assuming all_users() returns a list of user objects
    user_data = [{'username': user.username, 'email': user.email} for user in users]
    return jsonify(user_data)


@app.route('/ajaxkeyvalue', methods=['POST'])
def ajax():
    data = request.json  # Assuming the AJAX request sends JSON data
    print(data)
    # Process the data
    username = data['username']
    password = data['password']

    print(username)
    print(password)


    user = login(username, password)
    if not user:
        response_data ={'status' : 'fail'}
    else:
        session['logged_in'] = True
        session['username'] = username
        session['user'] = {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone
        }

        response_data = {'status' :'ok', 'user': user.to_json()}


    return jsonify(response_data)


@app.route('/profile')
def profile():

    user_data = session.get('user')

    if user_data:
        # Reconstruct the user object
        user = User(user_id=user_data['id'], username=user_data['username'],
                password_hash='', first_name=user_data['first_name'],
                last_name=user_data['last_name'], email=user_data['email'], phone=user_data['phone'])

        print(user.email)

        return render_template('profile.html', user_info=user)
    else:
        return redirect('/?messages=Please login again!')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



if __name__ == '__main__':
    app.run(debug=True)
