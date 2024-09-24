import re
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import escape

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
    return sqlite3.connect('users.db')

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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Sanitize the username before using it in the query
        username = sanitize_input(username)

        # Retrieve the user from the database by username
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            print(f"User found: {user[1]}")
            if check_password_hash(user[2], password):
                print("Password matched!")
                phone = user[6] if len(user) > 6 else None
                return User(user[0], user[1], user[2], user[3], user[4], user[5], phone)
            else:
                print("Password did not match!")
                return None
        else:
            print("User not found!")
            return None

    except Exception as e:
        print(f"Login error: {e}")
        return None

# User registration function
def register_user(username, password, email, first_name, last_name, phone=None):
    """Registers a new user by inserting the user data into the database."""
    try:
        # Sanitize all inputs
        username = sanitize_input(username)
        email = sanitize_input(email)
        first_name = sanitize_input(first_name)
        last_name = sanitize_input(last_name)
        phone = sanitize_input(phone) if phone else None

        # Validate email and password
        if not is_valid_email(email):
            return False, "Invalid email format"
        if not is_valid_password(password):
            return False, "Password must be at least 8 characters long"

        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Insert user data into the database
        cursor.execute('''
            INSERT INTO users (username, hashed_password, email, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, email, first_name, last_name, phone))

        conn.commit()
        conn.close()

        return True, None  # Registration successful

    except sqlite3.IntegrityError as e:
        # Handle unique constraint errors (e.g., username or email already exists)
        print(f"Integrity error: {e}")
        return False, 'Username or email already exists'

    except Exception as e:
        print(f"Registration error: {e}")
        return False, str(e)
