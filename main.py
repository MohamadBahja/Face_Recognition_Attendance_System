from flask import Flask, Response, render_template, request, redirect, session, url_for
import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
import face_recognition
import bcrypt
import datetime
import secrets

# Initialize Flask application
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

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

# Function to load images and labels from the database
def load_images_and_labels():
    images = []
    labels = []
    try:
        cursor.execute("SELECT id, username, image_data FROM students_basic_info")
        records = cursor.fetchall()
        for record in records:
            label = record[1]
            image_data = record[2]
            nparr = np.frombuffer(image_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            images.append(img_np)
            labels.append(label)
    except Error as e:
        print("Error while loading images and labels from database:", e)
    return images, labels

# Load images and labels for training
images, labels = load_images_and_labels()

def findEncodeings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

encodeListKnown = findEncodeings(images)
print('Encoding Complete.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        # Get username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Query the database to get the hashed password for the given username
        cursor.execute("SELECT id, password FROM doctors WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            doctor_id, hashed_password = result
            # Verify the password using bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                # Password is correct, store doctor_id in the session and redirect to user dashboard
                session['doctor_id'] = doctor_id
                return redirect('/user-dashboard')

        # Invalid credentials, render login form with an error message
        return render_template('user_login.html', error="Invalid username or password")

    # Render the user login form template
    return render_template('user_login.html')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Handle admin login form submission
        username = request.form['username']
        password = request.form['password']
        try:
            cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result:
                hashed_password = result[2]  # Assuming the hashed password is stored in the second column
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    return redirect('/admin-dashboard')  # Redirect to admin dashboard page after successful login
                else:
                    return render_template('admin_login.html', error="Invalid username or password")
            else:
                return render_template('admin_login.html', error="Invalid username or password")
        except Error as e:
            print("Error while validating admin credentials:", e)
            return render_template('admin_login.html', error="An error occurred while validating credentials. Please try again.")
    else:
        # Render the admin login form template
        return render_template('admin_login.html')


# Admin dashboard route
@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        name = request.form['name']
        # Insert course data into the database
        try:
            cursor.execute("INSERT INTO courses (name) VALUES (%s)", (name,))
            connection.commit()
            # Use JavaScript to show an alert
            return """
                <script>
                    alert('Course added successfully!');
                    window.location.href = '/'; // Redirect to home page or any other page
                </script>
            """
        except Exception as e:
            return str(e)
    return render_template('add_course.html')


from flask import render_template  # Import render_template

@app.route('/add-student-basic-info', methods=['GET', 'POST'])
def add_student_basic_info():
    if request.method == 'POST':
        username = request.form['username']
        image_data = request.files['image'].read()

        try:
            # Insert into students_basic_info table
            cursor.execute("INSERT INTO students_basic_info (username, image_data) VALUES (%s, %s)", (username, image_data))
            connection.commit()
            return redirect('/add-student-course')  # Redirect to course info form
        except Error as e:
            print("Error while adding student basic info:", e)
            return "Error occurred while adding student basic info."

    # Render the add-student-basic-info.html template for GET requests
    return render_template('add_student_basic_info.html')

@app.route('/add-student-course', methods=['GET', 'POST'])
def add_student_course():
    if request.method == 'POST':
        username = request.form['username']
        course_id = request.form['course']

        try:
            # Fetch student ID based on the username
            cursor.execute("SELECT id FROM students_basic_info WHERE username = %s", (username,))
            student = cursor.fetchone()

            if student:
                # Insert into students_courses table
                cursor.execute("INSERT INTO students_courses (student_id, course_id) VALUES (%s, %s)", (student[0], course_id))
                connection.commit()
                # Use JavaScript to show an alert
                return """
                    <script>
                        alert('Student added successfully!');
                        window.location.href = '/'; // Redirect to home page or any other page
                    </script>
                """
            else:
                return "Student not found!"
        except Error as e:
            print("Error while adding student course:", e)
            return "Error occurred while adding student course."

    # Fetch courses from the database
    try:
        cursor.execute("SELECT id, name FROM courses")
        courses = cursor.fetchall()
    except Error as e:
        print("Error while fetching courses:", e)
        courses = []

    # Render the add_student_course.html template with the courses
    return render_template('add_student_course.html', courses=courses)



@app.route('/add-doctor-account', methods=['GET', 'POST'])
def add_doctor_account():
    cursor = connection.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode()  # Convert password to bytes

        # Hash the password
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            # Insert doctor data into the database
            cursor.execute("INSERT INTO doctors (username, password) VALUES (%s, %s)", (username, hashed_password))
            connection.commit()
            # Use JavaScript to show an alert
            return """
                <script>
                    alert('Doctor account added successfully!');
                    window.location.href = '/'; // Redirect to home page or any other page
                </script>
            """
        except Exception as e:
            return str(e)

    return render_template('add_doctor_account.html')


@app.route('/add-course-for-doctor', methods=['GET', 'POST'])
def add_course_for_doctor():
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        course_id = request.form['course']

        try:
            # Fetch the doctor's ID based on the username
            cursor.execute("SELECT id FROM doctors WHERE username = %s", (username,))
            doctor = cursor.fetchone()

            if doctor:
                # Insert doctor-course relationship into the database
                cursor.execute("INSERT INTO doctor_courses (doctor_id, course_id) VALUES (%s, %s)", (doctor['id'], course_id))
                connection.commit()
                # Use JavaScript to show an alert
                return """
                    <script>
                        alert('Course added for doctor successfully!');
                        window.location.href = '/'; // Redirect to home page or any other page
                    </script>
                """
            else:
                return "Doctor not found!"
        except Exception as e:
            return str(e)

    # Fetch courses from the database to populate the select box
    cursor.execute("SELECT id, name FROM courses")
    courses = cursor.fetchall()

    return render_template('add_course_doctor.html', courses=courses)


# Updated Flask application

last_recorded_time = {}
recognized_students = {}
video_feed_running = False

# Assume you have imported the necessary libraries and defined the Flask app and routes as before

def get_student_id_from_name(name, course_id):
    try:
        cursor.execute("SELECT id FROM students_basic_info WHERE username = %s", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
    except mysql.connector.Error as e:
        print("Error while getting student ID from name:", e)
    return None



@app.route('/video-feed/<int:course_id>')
def video_feed(course_id):
    cap = cv2.VideoCapture(0)

    def generate_frames():
        global recognized_students

        while True:
            success, frame = cap.read()
            if not success:
                break
            else:
                frame_resized = cv2.resize(frame, (800, 600))
                imgS = cv2.resize(frame_resized, (0, 0), None, 0.5, 0.5)
                imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

                faceCurentFrame = face_recognition.face_locations(imgS)
                encodeCurentFrame = face_recognition.face_encodings(imgS, faceCurentFrame)

                for encodeface, faceLoc in zip(encodeCurentFrame, faceCurentFrame):
                    matches = face_recognition.compare_faces(encodeListKnown, encodeface)
                    faceDis = face_recognition.face_distance(encodeListKnown, encodeface)
                    matchIndex = np.argmin(faceDis)

                    if matches[matchIndex]:
                        name = labels[matchIndex].upper()
                        print(f"Match found: {name}")  # Debug statement
                        student_id = get_student_id_from_name(name, course_id)

                        if student_id is not None:
                            y1, x2, y2, x1 = faceLoc
                            y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
                            print(f"Drawing rectangle at: {(x1, y1, x2, y2)}")  # Debug statement
                            cv2.rectangle(frame_resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame_resized, name, (x1 + 6, y2 + 20), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                            # Mark attendance if not already recorded
                            try:
                                cursor.execute("SELECT COUNT(*) FROM attendance_status WHERE student_id = %s AND course_id = %s AND date = CURDATE()", (student_id, course_id))
                                count = cursor.fetchone()[0]

                                if count == 0:
                                    cursor.execute("INSERT INTO attendance_status (student_id, course_id, status, date, time) VALUES (%s, %s, 'present', CURDATE(), CURTIME())", (student_id, course_id))
                                    connection.commit()
                                    recognized_students[name] = True
                                else:
                                    print(f"Attendance already recorded for {name}")
                            except Error as e:
                                print("Error while adding attendance record:", e)

                # Create a new image for student names and attendance status
                names_image = np.zeros((frame_resized.shape[0], 400, 3), dtype=np.uint8)
                names_image[:, :] = (255,255,255)  # Dark gray background
                y_offset = 30
                for label in labels:
                    cv2.putText(names_image, label.upper(), (10, y_offset), cv2.FONT_HERSHEY_COMPLEX, 0.75, (0, 0, 0), 2)

                    # Add a green circle beside the student's name if their attendance is marked
                    if recognized_students.get(label.upper(), False):
                        cv2.circle(names_image, (350, y_offset - 10), 10, (0, 255, 0), cv2.FILLED)

                    y_offset += 40

                # Add borders and title
                
                cv2.rectangle(names_image, (0, 0), (names_image.shape[1], names_image.shape[0]), (255, 255, 255), 3)
                

                # Combine the video frame and the names_image
                combined_frame = np.hstack((frame_resized, names_image))

                ret, buffer = cv2.imencode('.jpg', combined_frame)
                combined_frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + combined_frame_bytes + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stop-video-feed/<int:course_id>')
def stop_video_feed(course_id):
    global video_feed_running

    # Reset recognition status for students who have not been recognized again
    for label in recognized_students.keys():
        if not recognized_students[label]:
            recognized_students[label] = False

    video_feed_running = False
    return redirect('/user-dashboard')

@app.route('/user-dashboard')
def user_dashboard():
    # Retrieve doctor_id from the session
    doctor_id = session.get('doctor_id')

    if doctor_id:
        try:
            # Connect to the database
            connection = mysql.connector.connect(host='localhost',
                                                 database='face_recognition1',
                                                 user='root',
                                                 password='')
            if connection.is_connected():
                cursor = connection.cursor()
                # Fetch courses taught by the logged-in doctor
                query = "SELECT courses.id, courses.name FROM courses INNER JOIN doctor_courses ON courses.id = doctor_courses.course_id WHERE doctor_courses.doctor_id = %s"
                cursor.execute(query, (doctor_id,))
                courses = cursor.fetchall()
                print("Courses:", courses)  # Debug statement to check if courses are fetched

                # Pass recognized_students dictionary to the template
                return render_template('user_dashboard.html', courses=courses, recognized_students=recognized_students)
        except mysql.connector.Error as e:
            print("Error connecting to database:", e)
            courses = []
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    else:
        # Handle case where doctor_id is not found in session (not logged in)
        courses = []

    return render_template('user_dashboard.html', courses=courses, recognized_students={})

@app.route('/video-feed-with-button/<int:course_id>')
def video_feed_with_button(course_id):
    return render_template('video_feed.html', course_id=course_id)

import mysql.connector.pooling
import time

# Create a connection pool
dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "face_recognition1"
}
pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)

# Function to get a connection from the pool
def get_connection():
    return pool.get_connection()

def reconnect():
    global connection, cursor
    while True:
        try:
            connection = get_connection()
            cursor = connection.cursor()
            print("Reconnected to MySQL")
            break
        except mysql.connector.Error as e:
            print("Error reconnecting to MySQL:", e)
            time.sleep(5)  # Wait for 5 seconds before retrying

@app.route('/see-attendance/<int:course_id>')
def see_attendance(course_id):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        SELECT as1.id, c.name as course_name, as1.date
        FROM attendance_status as1
        INNER JOIN courses c ON as1.course_id = c.id
        WHERE as1.course_id = %s
        GROUP BY as1.date
        """
        cursor.execute(query, (course_id,))
        attendance_data = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template('see_attendance.html', attendance_data=attendance_data)
    except mysql.connector.Error as e:
        print("Error while fetching attendance data:", e)
        return "Error occurred while fetching attendance data: " + str(e), 500

@app.route('/attendance-details/<int:attendance_id>')
def attendance_details(attendance_id):
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # First, get the course_id from the attendance_id
        course_query = "SELECT course_id FROM attendance_status WHERE id = %s"
        cursor.execute(course_query, (attendance_id,))
        course_result = cursor.fetchone()

        if not course_result:
            cursor.close()
            connection.close()
            return "Attendance record not found.", 404

        course_id = course_result[0]

        # Fetch attendance details for all students in the course for the date of the given attendance_id
        query = """
        SELECT sbi.username, IFNULL(as1.status, 'absent') as status
        FROM students_basic_info sbi
        LEFT JOIN (
            SELECT student_id, status
            FROM attendance_status
            WHERE course_id = %s AND date = (
                SELECT date FROM attendance_status WHERE id = %s
            )
        ) as1 ON sbi.id = as1.student_id
        WHERE sbi.id IN (
            SELECT student_id FROM students_courses WHERE course_id = %s
        )
        """
        cursor.execute(query, (course_id, attendance_id, course_id))
        attendance_records = cursor.fetchall()

        # Consume the result set
        while cursor.nextset():
            pass

        cursor.close()
        connection.close()

        return render_template('attendance_details.html', attendance_records=attendance_records, course_id=course_id)
    except mysql.connector.Error as e:
        print("Error while fetching attendance details:", e)
        return "Error occurred while fetching attendance details.", 500


if __name__ == '__main__':
    app.run(debug=True)
