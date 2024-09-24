import sqlite3

# Helper function to manage database connection and cursor
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows you to fetch results as dictionaries
    return conn


class Event:
    def __init__(self, id, name, date, time, location, description, capacity, host_id, category):
        self.id = id
        self.name = name
        self.date = date
        self.time = time
        self.location = location
        self.description = description
        self.capacity = capacity
        self.host_id = host_id
        self.category = category  # New field for category

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
            'category': self.category  # Include the category
        }


# Function to create a new event
def create_event(event_data):
    conn = sqlite3.connect('users.db')
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
        event_data['category']  # Include category in the insert
    ))
    event_id = cursor.lastrowid  # Get the ID of the newly created event
    conn.commit()
    conn.close()
    return event_id

# Get all events in the system
def get_events():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events')
        events = cursor.fetchall()
        return [Event(*event) for event in events]
    finally:
        conn.close()

# Get events by the host (user) ID
def get_events_by_host(host_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE host_id = ?', (host_id,))
    events = cursor.fetchall()
    conn.close()

    # Ensure the Event constructor matches the number of columns being returned
    return [Event(*event) for event in events]


# Get RSVPs by user ID
def get_rsvps_by_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, event_id, guests FROM rsvps WHERE user_id = ?', (user_id,))
        rsvps = cursor.fetchall()
        return rsvps
    finally:
        conn.close()

# Get RSVPs for a specific event
def get_rsvps_by_event_id(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rsvps WHERE event_id = ?', (event_id,))
        rsvps = cursor.fetchall()
        return rsvps
    finally:
        conn.close()

# Get RSVP count for an event
def get_rsvp_count(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(guests) FROM rsvps WHERE event_id = ?', (event_id,))
        count = cursor.fetchone()[0]
        return count if count else 0
    finally:
        conn.close()

# Get event guests (user IDs and their RSVP count)
def get_event_guests(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, guests FROM rsvps WHERE event_id = ?', (event_id,))
        guests = cursor.fetchall()
        return guests
    finally:
        conn.close()

# Update an event
def update_event(event_id, event_data):
    try:
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
    finally:
        conn.close()

# Delete an event
def delete_event(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
    finally:
        conn.close()

# Add an RSVP for a user to an event
def add_rsvp(user_id, event_id, guests):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rsvps (user_id, event_id, guests)
            VALUES (?, ?, ?)
        ''', (user_id, event_id, guests))
        conn.commit()
    finally:
        conn.close()

# Remove an RSVP for a user from an event
def remove_rsvp(user_id, event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rsvps WHERE user_id = ? AND event_id = ?', (user_id, event_id))
        conn.commit()
    finally:
        conn.close()

# Search events based on a query
def search_events(query):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        search_term = f'%{query}%'
        cursor.execute('''
            SELECT * FROM events
            WHERE name LIKE ? OR location LIKE ? OR description LIKE ? OR category LIKE ?
        ''', (search_term, search_term, search_term, search_term))  # Add category to search
        events = cursor.fetchall()
        return [Event(*event) for event in events]
    finally:
        conn.close()

# Get event by ID
def get_event_by_id(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        return Event(*event) if event else None
    except sqlite3.DatabaseError as e:
        print(f"Database error occurred: {e}")
        return None
    finally:
        conn.close()


# Delete RSVPs associated with a specific event
def delete_rsvps_for_event(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rsvps WHERE event_id = ?', (event_id,))
        conn.commit()
    finally:
        conn.close()
