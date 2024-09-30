import re
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import escape

class User:
    def __init__(self, id, username, hashed_password, first_name, last_name, email, phone=None):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone  # Optional, defaults to None

    def to_dict(self):
        """Convert the User object into a dictionary format."""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone
        }

# Helper function to manage database connection
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Fetch results as dictionaries
    return conn

# Input validation helper functions
def is_valid_email(email):
    """Validates if the email has the correct format."""
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None

def is_valid_password(password):
    """Ensures the password meets the criteria (e.g., length)."""
    return len(password) >= 8  # Enforces minimum password length of 8 characters

def sanitize_input(input_data):
    """Sanitize inputs to prevent script injection."""
    return escape(input_data.strip())

# User login function
def user_login(username, password):
    """Handles user login by verifying username and password."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sanitize and retrieve user
    username = sanitize_input(username)
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['hashed_password'], password):
        phone = user['phone'] if 'phone' in user else None
        return User(user['id'], user['username'], user['hashed_password'], user['first_name'], user['last_name'], user['email'], phone)
    
    return None

# User registration function
def register_user(username, password, email, first_name, last_name, phone=None):
    """Registers a new user by inserting the user data into the database."""
    try:
        # Sanitize inputs
        username = sanitize_input(username)
        password = sanitize_input(password)
        email = sanitize_input(email)
        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)
        phone = sanitize_input(phone)

        # Validate email and password
        if not is_valid_email(email):
            return False, "Invalid email format"
        if not is_valid_password(password):
            return False, "Password must be at least 8 characters long"

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Insert user data into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, hashed_password, email, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, email, first_name, last_name, phone))
        conn.commit()
        conn.close()

        return True, None  # Registration successful

    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, str(e)

