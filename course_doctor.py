import bcrypt
import mysql.connector

# Establishing a connection to the database
connection = mysql.connector.connect(
    host='localhost',
    database='face_recognition1',
    user='root',
    password=''
)

# Creating a cursor object
cursor = connection.cursor()

# Hash the password
hashed_password = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()

# Insert data into the database
try:
    # Insert courses
    cursor.execute("INSERT INTO courses (name) VALUES ('CSCI300')")
    cursor.execute("INSERT INTO courses (name) VALUES ('CSCI250')")
    
    # Get the course_id for 'Computer Science' and 'Mathematics'
    cursor.execute("SELECT id FROM courses WHERE name = 'CSCI300'")
    computer_science_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM courses WHERE name = 'CSCI250'")
    mathematics_id = cursor.fetchone()[0]

    # Insert a doctor
    cursor.execute("INSERT INTO doctors (username, password) VALUES ('MohamadBahja', %s)", (hashed_password,))
    doctor_id = cursor.lastrowid

    # Associate the doctor with the courses
    cursor.execute("INSERT INTO doctor_courses (doctor_id, course_id) VALUES (%s, %s)", (doctor_id, computer_science_id))
    cursor.execute("INSERT INTO doctor_courses (doctor_id, course_id) VALUES (%s, %s)", (doctor_id, mathematics_id))

    connection.commit()
    print("Data inserted successfully!")
except Exception as e:
    print(str(e))
finally:
    # Closing the cursor and the connection
    cursor.close()
    connection.close()
