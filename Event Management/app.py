from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from user_manage import register_user, user_login, User
from event_manage import create_event, update_rsvp, get_rsvp_by_user_and_event, get_events_by_host, update_event, delete_event
from event_manage import add_rsvp, get_event_by_id, remove_rsvp, get_rsvps_by_user, get_rsvp_count, delete_rsvps_for_event, get_events
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
        # Use .get() to fetch form fields and handle the optional phone field
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        # Handle optional phone input
        phone = request.form.get('phone', '')  # Allow phone to be optional (no strip needed)

        # If any mandatory field is empty, return an error message
        if not all([username, password, email, first_name, last_name]):
            return render_template('register.html', error="All fields except phone are required.")

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
@login_required
def dashboard():
    user_id = session['user']['id']
    hosted_events = get_events_by_host(user_id) or []

    # Fetch RSVPs and make sure events are unique
    rsvps = get_rsvps_by_user(user_id) or []

    # Create a set to store unique event IDs
    unique_event_ids = set(rsvp[1] for rsvp in rsvps if rsvp)

    # Use the unique event IDs to get events
    attending_events = [get_event_by_id(event_id) for event_id in unique_event_ids]

    return render_template('dashboard.html', hosted_events=hosted_events, attending_events=attending_events)

@app.route('/profile')
@login_required
def profile():
    user_data = session.get('user')

    if user_data:
        user = User(id=user_data['id'], username=user_data['username'],
                    hashed_password='', first_name=user_data['first_name'],
                    last_name=user_data['last_name'], email=user_data['email'])

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

    # Fetch all RSVPs for the user
    rsvps = get_rsvps_by_user(user_id) or []

    # Create a set to store unique event IDs (to avoid duplicate entries)
    unique_event_ids = set(rsvp[1] for rsvp in rsvps if rsvp)

    # Use the unique event IDs to get the event details
    attending_events = [get_event_by_id(event_id) for event_id in unique_event_ids]

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
            'category': request.form['category'],  # Add this line to collect category
            'host_id': session['user']['id']  # Set the current user as the host
        }

        # Create the event and retrieve its ID
        event_id = create_event(event_data)

        # Automatically RSVP the user (event creator) to their own event
        user_id = session['user']['id']
        add_rsvp(user_id, event_id, guests=1)

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

    event = get_event_by_id(event_id)
    if not event:
        return "Event not found", 404

    # Calculate total current RSVPs for the event
    total_rsvp_guests = get_rsvp_count(event_id)

    # Check if the RSVP exceeds the event capacity
    if total_rsvp_guests + guests > event.capacity:
        error_msg = f"Error: The number of guests exceeds the event capacity of {event.capacity} guests."
        return render_template('event_details.html', event=event, error=error_msg)

    # Proceed with the RSVP if within the allowed capacity
    add_rsvp(user_id, event_id, guests)

    return redirect(url_for('event_details_route', event_id=event_id))

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

@app.route('/view_events')
@login_required
def view_events():
    # Fetch all events from the database
    events = get_events()

    # Pass the list of events to the template
    return render_template('view_events.html', events=events, page='view_events')


@app.route('/event/<int:event_id>')
@login_required
def event_details_route(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return "Event not found", 404

    # Get RSVP details for the logged-in user for this event
    user_id = session['user']['id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT guests FROM rsvps WHERE user_id = ? AND event_id = ?', (user_id, event_id))
    rsvp = cursor.fetchone()

    # If RSVP exists, pass the guest count (excluding the user)
    attending_guests = None
    if rsvp:
        attending_guests = rsvp[0] - 1  # Subtract 1 to exclude the user

    return render_template('event_details.html', event=event, attending_guests=attending_guests)

@app.route('/edit_rsvp/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_rsvp_route(event_id):
    user_id = session['user']['id']

    # If it's a GET request, render the form for editing the RSVP
    if request.method == 'GET':
        event = get_event_by_id(event_id)
        current_rsvp = get_rsvp_by_user_and_event(user_id, event_id)
        return render_template('edit_rsvp.html', event=event, current_rsvp=current_rsvp)

    # If it's a POST request, handle the form submission and update the RSVP
    if request.method == 'POST':
        new_guests = int(request.form.get('guests', 0))  # New number of guests user is RSVPing

        # Get the event details
        event = get_event_by_id(event_id)
        if not event:
            return "Event not found", 404

        # Get the current RSVP details for this user
        current_rsvp = get_rsvp_by_user_and_event(user_id, event_id)
        current_guest_count = current_rsvp['guests'] if current_rsvp else 0

        # Calculate total RSVPs excluding the current user's existing RSVP
        total_rsvp_guests = get_rsvp_count(event_id) - current_guest_count

        # Check if the new RSVP exceeds the event capacity
        if total_rsvp_guests + new_guests > event.capacity:
            error_msg = f"Error: The new number of guests exceeds the event capacity of {event.capacity} guests."
            return render_template('event_details.html', event=event, error=error_msg)

        # Update the RSVP with the new guest count
        update_rsvp(user_id, event_id, new_guests)

        return redirect(url_for('event_details_route', event_id=event_id))

@app.route('/remove_rsvp/<int:event_id>', methods=['POST'])
@login_required
def remove_rsvp_route(event_id):
    user_id = session['user']['id']

    # Call the correct remove_rsvp function from event_manage.py
    remove_rsvp(user_id, event_id)

    return redirect(url_for('event_details_route', event_id=event_id))

if __name__ == '__main__':
    app.run(debug=True)
