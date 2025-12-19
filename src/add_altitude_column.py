import sqlite3

# Path to your SQLite database file
db_path = 'db.sqlite3'

# Connect to the SQLite database
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Add the altitude column to the myapp_location table
cursor.execute("ALTER TABLE myapp_location ADD COLUMN altitude REAL")

# Commit the changes and close the connection
connection.commit()
cursor.close()
connection.close()

print("Altitude column added to myapp_location table.")
