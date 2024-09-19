import sqlite3
import bcrypt


def sys_init():
   # Connect to an SQLite database
   conn = sqlite3.connect('users.db')
   cursor = conn.cursor()

   # Create a table if it doesn't exist
   cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT
        )
    ''')

   # Insert some dummy data with hashed passwords
   password1_hash = bcrypt.hashpw(b'secret1', bcrypt.gensalt())
   password2_hash = bcrypt.hashpw(b'secret2', bcrypt.gensalt())
   cursor.execute(
       "INSERT INTO users (username, password, first_name, last_name, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
       ('user1', password1_hash, 'John', 'Doe', 'john@example.com',
        '1234567890'))
   cursor.execute(
       "INSERT INTO users (username, password, first_name, last_name, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
       ('user2', password2_hash, 'Jane', 'Smith', 'jane@example.com',
        '0987654321'))

   # Commit the changes
   conn.commit()

   # Close the connection
   conn.close()
