import mysql.connector
from mysql.connector import Error
import bcrypt

# Connect to MySQL database
try:
    connection = mysql.connector.connect(host='localhost',
                                         database='face_recognition1',
                                         user='root',
                                         password='')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)
except Error as e:
    print("Error while connecting to MySQL", e)

# Add admin username and password to the admin table
username = "admin"
password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
try:
    cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))
    connection.commit()  # Commit the transaction
    print("Admin user added successfully.")
except Error as e:
    print("Error while adding admin user to the database:", e)

# Close the connection
if connection.is_connected():
    cursor.close()
    connection.close()
    print("MySQL connection is closed.")
