from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from user_manage import register_user, user_login, User
from event_manage import create_event, get_event_by_id, update_event, delete_event, add_rsvp, get_events_by_host, get_rsvps_by_user, search_events, delete_rsvps_for_event
from init import sys_init, get_db_connection
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the system (create database and tables)
with app.app_context():
    sys_init()

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('index', messages="Please login to access this page"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']

        # Register the user
        success, message = register_user(username, password, email, first_name, last_name, phone)
        if success:
            return redirect(url_for('index', messages="Account created successfully!"))
        else:
            return render_template('register.html', error=message)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = user_login(username, password)

        if user:
            session['logged_in'] = True
            session['user'] = user.to_dict()
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect('/?messages=Please login to view your dashboard')
    
    user_id = session['user']['id']
    hosted_events = get_events_by_host(user_id) or []
    rsvps = get_rsvps_by_user(user_id) or []

    attending_events = [get_event_by_id(rsvp[1]) for rsvp in rsvps if rsvp]

    # Pass the events to the template
    return render_template('dashboard.html', hosted_events=hosted_events, attending_events=attending_events)


@app.route('/profile')
@login_required
def profile():
    user_data = session.get('user')

    if user_data:
        user = User(id=user_data['id'], username=user_data['username'],
                    hashed_password='', first_name=user_data['first_name'],
                    last_name=user_data['last_name'], email=user_data['email'], 
                    phone=user_data['phone'])

        return render_template('profile.html', user_info=user)
    else:
        return redirect(url_for('index', messages="Please login again!"))

@app.route('/hosted_events')
@login_required
def hosted_events():
    user_id = session['user']['id']
    hosted_events = get_events_by_host(user_id) or []
    return render_template('hosted_events.html', hosted_events=hosted_events)

@app.route('/attending_events')
@login_required
def attending_events():
    user_id = session['user']['id']
    rsvps = get_rsvps_by_user(user_id) or []
    attending_events = [get_event_by_id(rsvp[1]) for rsvp in rsvps if rsvp]
    return render_template('attending_events.html', attending_events=attending_events)


@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event_route():
    if request.method == 'POST':
        # Collect event data from the form
        event_data = {
            'name': request.form['name'],
            'date': request.form['date'],
            'time': request.form['time'],
            'location': request.form['location'],
            'description': request.form['description'],
            'capacity': int(request.form['capacity']),
            'host_id': session['user']['id']  # Set the current user as the host
        }
        
        # Create the event and retrieve its ID
        event_id = create_event(event_data)  # Ensure create_event returns the event ID
        
        # Automatically RSVP the user (event creator) to their own event
        user_id = session['user']['id']
        add_rsvp(user_id, event_id, guests=1)  # Add RSVP for the host with 1 guest by default
        
        return redirect(url_for('dashboard'))

    return render_template('create_event.html')


@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event_route(event_id):
    event = get_event_by_id(event_id)
    if not event or event.host_id != session['user']['id']:
        return "Unauthorized", 403

    if request.method == 'POST':
        event_data = {
            'name': request.form['name'],
            'date': request.form['date'],
            'time': request.form['time'],
            'location': request.form['location'],
            'description': request.form['description'],
            'capacity': int(request.form['capacity'])
        }
        update_event(event_id, event_data)
        return redirect(url_for('dashboard'))

    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event_route(event_id):
    event = get_event_by_id(event_id)
    if not event or event.host_id != session['user']['id']:
        return "Unauthorized", 403

    delete_rsvps_for_event(event_id)
    delete_event(event_id)
    return redirect(url_for('dashboard'))

@app.route('/rsvp/<int:event_id>', methods=['POST'])
@login_required
def rsvp_route(event_id):
    user_id = session['user']['id']
    guests = int(request.form.get('guests', 0))
    add_rsvp(user_id, event_id, guests)
    return redirect(url_for('dashboard'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    if not query:
        return redirect(url_for('dashboard'))

    # Query the database for matching events based on location, event name, host name, keywords, and category
    conn = get_db_connection()
    cursor = conn.cursor()

    search_query = f"""
        SELECT events.*, users.username AS host_name
        FROM events
        JOIN users ON events.host_id = users.id
        WHERE LOWER(events.name) LIKE ? 
        OR LOWER(events.location) LIKE ? 
        OR LOWER(users.username) LIKE ? 
        OR LOWER(events.description) LIKE ? 
        OR LOWER(events.category) LIKE ?
    """
    
    like_query = f"%{query}%"
    cursor.execute(search_query, (like_query, like_query, like_query, like_query, like_query))
    events = cursor.fetchall()

    conn.close()

    return render_template('search_results.html', events=events, query=query)


@app.route('/event/<int:event_id>')
def event_details_route(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return "Event not found", 404
    return render_template('event_details.html', event=event)

if __name__ == '__main__':
    app.run(debug=True)
