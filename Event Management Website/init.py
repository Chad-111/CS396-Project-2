import sqlite3

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')  # Ensure 'users.db' is the correct path to your database
    conn.row_factory = sqlite3.Row  # This allows you to treat the rows as dictionaries
    return conn

def sys_init():
    """Initialize the database schema and perform any required migrations."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Alter table to add 'hashed_password' if not already exists
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN hashed_password TEXT')
    except sqlite3.OperationalError:
        # Ignore the error if the column already exists
        pass

    # Create users table with the correct schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT
        )
    ''')

    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            capacity INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            category TEXT,
            FOREIGN KEY(host_id) REFERENCES users(id)
        )
    ''')

    # Create rsvps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            guests INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    ''')

    conn.commit()  # Commit any changes
    conn.close()  # Close the connection
