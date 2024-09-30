import sqlite3

# Helper function to manage database connection and cursor
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows you to fetch results as dictionaries
    return conn


class Event:
    def __init__(self, id, name, date, time, location, description, capacity, host_id, category, host_name):
        self.id = id
        self.name = name
        self.date = date
        self.time = time
        self.location = location
        self.description = description
        self.capacity = capacity
        self.host_id = host_id
        self.category = category
        self.host_name = host_name  # Host name included for display purposes

    def to_dict(self):
        """Convert the Event object into a dictionary format."""
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'time': self.time,
            'location': self.location,
            'description': self.description,
            'capacity': self.capacity,
            'host_id': self.host_id,
            'category': self.category,
            'host_name': self.host_name  # Include host name for display
        }


# Function to create a new event
def create_event(event_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (name, date, time, location, description, capacity, host_id, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        event_data['name'],
        event_data['date'],
        event_data['time'],
        event_data['location'],
        event_data['description'],
        event_data['capacity'],
        event_data['host_id'],
        event_data.get('category', 'Other')  # Fallback to 'Other' if category is missing
    ))
    event_id = cursor.lastrowid  # Get the ID of the newly created event
    conn.commit()
    conn.close()
    return event_id


# Function to get all events
def get_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT events.*, users.username AS host_name
        FROM events
        JOIN users ON events.host_id = users.id
    ''')
    events = cursor.fetchall()
    conn.close()
    return [Event(*event) for event in events]


# Function to get events by host (user) ID
def get_events_by_host(host_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT events.*, users.username AS host_name
        FROM events
        JOIN users ON events.host_id = users.id
        WHERE events.host_id = ?
    ''', (host_id,))
    events = cursor.fetchall()
    conn.close()
    return [Event(*event) for event in events]


# Function to get RSVPs by user ID
def get_rsvps_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, event_id, guests FROM rsvps WHERE user_id = ?', (user_id,))
    rsvps = cursor.fetchall()
    conn.close()
    return rsvps


# Function to get RSVPs for a specific event
def get_rsvps_by_event_id(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvps WHERE event_id = ?', (event_id,))
    rsvps = cursor.fetchall()
    conn.close()
    return rsvps


# Function to get RSVP count for an event (total number of guests attending)
def get_rsvp_count(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(guests) FROM rsvps WHERE event_id = ?', (event_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count if count else 0


# Function to remove an RSVP for a user from an event
def remove_rsvp(user_id, event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rsvps WHERE user_id = ? AND event_id = ?', (user_id, event_id))
    conn.commit()
    conn.close()


# Function to update an RSVP
def update_rsvp(user_id, event_id, new_guests):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE rsvps
        SET guests = ?
        WHERE user_id = ? AND event_id = ?
    ''', (new_guests, user_id, event_id))
    conn.commit()
    conn.close()


# Function to get an RSVP by user and event ID
def get_rsvp_by_user_and_event(user_id, event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM rsvps
        WHERE user_id = ? AND event_id = ?
    ''', (user_id, event_id))
    rsvp = cursor.fetchone()
    conn.close()
    return rsvp


# Function to get event guests (user IDs and their RSVP count)
def get_event_guests(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, guests FROM rsvps WHERE event_id = ?', (event_id,))
    guests = cursor.fetchall()
    conn.close()
    return guests


# Function to update an event
def update_event(event_id, event_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE events
        SET name = ?, date = ?, time = ?, location = ?, description = ?, capacity = ?
        WHERE id = ?
    ''', (
        event_data['name'], event_data['date'], event_data['time'],
        event_data['location'], event_data['description'],
        event_data['capacity'], event_id
    ))
    conn.commit()
    conn.close()


# Function to delete an event
def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()


# Function to add an RSVP for a user to an event
def add_rsvp(user_id, event_id, guests):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the current RSVP count for the event
    cursor.execute('SELECT capacity FROM events WHERE id = ?', (event_id,))
    event_capacity = cursor.fetchone()['capacity']

    # Get the total number of guests already RSVPed
    cursor.execute('SELECT SUM(guests) FROM rsvps WHERE event_id = ?', (event_id,))
    current_rsvps = cursor.fetchone()[0] or 0

    if current_rsvps + guests > event_capacity:
        return False  # RSVP would exceed capacity

    cursor.execute('''
        INSERT INTO rsvps (user_id, event_id, guests)
        VALUES (?, ?, ?)
    ''', (user_id, event_id, guests))
    conn.commit()
    conn.close()
    return True


# Function to search events based on a query
def search_events(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_term = f'%{query}%'
    cursor.execute('''
        SELECT events.*, users.username AS host_name
        FROM events
        JOIN users ON events.host_id = users.id
        WHERE events.name LIKE ? OR events.location LIKE ? OR events.description LIKE ? OR events.category LIKE ?
    ''', (search_term, search_term, search_term, search_term))
    events = cursor.fetchall()
    conn.close()
    return [Event(*event) for event in events]


# Function to get an event by ID
def get_event_by_id(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT events.*, users.username AS host_name
        FROM events
        JOIN users ON events.host_id = users.id
        WHERE events.id = ?
    ''', (event_id,))
    event = cursor.fetchone()
    conn.close()

    if event:
        return Event(*event)
    return None


# Function to delete RSVPs associated with a specific event
def delete_rsvps_for_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rsvps WHERE event_id = ?', (event_id,))
    conn.commit()
    conn.close()
