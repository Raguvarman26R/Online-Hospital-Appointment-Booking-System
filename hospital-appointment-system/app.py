"""
ONLINE HOSPITAL APPOINTMENT SYSTEM
Backend: Python Flask
Database: MySQL (with seamless local SQLite resilience)
Software Engineering & Agile Practices (Scrum Methodology)
"""

import os
from functools import wraps
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config, Database, init_database

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is initialized on startup
with app.app_context():
    init_database()

# -----------------------------------------------------------------------------
# AUTHENTICATION & ACCESS CONTROL DECORATORS
# -----------------------------------------------------------------------------
def login_required(role=None):
    """Decorator to enforce login and optional role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login', next=request.url))
            if role and session.get('role') != role:
                flash(f"Unauthorized access. This area is reserved for {role.capitalize()}s.", "danger")
                if session.get('role') == 'patient':
                    return redirect(url_for('patient_dashboard'))
                elif session.get('role') == 'doctor':
                    return redirect(url_for('doctor_dashboard'))
                elif session.get('role') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -----------------------------------------------------------------------------
# GENERAL & PUBLIC ROUTES
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    """Home Page with featured doctors, specialty showcase, and hospital statistics."""
    featured_doctors = Database.query(
        "SELECT doctor_id, name, specialization, qualification, experience, consultation_fee, available_days "
        "FROM doctors ORDER BY doctor_id ASC LIMIT 3"
    )
    return render_template('index.html', featured_doctors=featured_doctors)


@app.route('/doctors')
def doctors():
    """Doctor Directory page with search by name/keyword and filtering by specialization."""
    search_query = request.args.get('search', '').strip()
    selected_specialty = request.args.get('specialty', '').strip()

    sql = "SELECT * FROM doctors WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (LOWER(name) LIKE %s OR LOWER(specialization) LIKE %s OR LOWER(qualification) LIKE %s)"
        term = f"%{search_query.lower()}%"
        params.extend([term, term, term])

    if selected_specialty:
        sql += " AND LOWER(specialization) = %s"
        params.append(selected_specialty.lower())

    sql += " ORDER BY name ASC"
    doctor_list = Database.query(sql, tuple(params))

    # Retrieve all distinct specializations for filter dropdown
    all_specs = Database.query("SELECT DISTINCT specialization FROM doctors ORDER BY specialization ASC")
    specializations = [row['specialization'] for row in all_specs] if all_specs else []

    return render_template(
        'doctors.html',
        doctors=doctor_list,
        search_query=search_query,
        selected_specialty=selected_specialty,
        specializations=specializations
    )


@app.route('/doctor/<int:doctor_id>')
def doctor_details(doctor_id):
    """Doctor Details page showing qualifications, consultation fee, and available days."""
    doctor = Database.query("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for('doctors'))
    return render_template('doctor_details.html', doctor=doctor)


# -----------------------------------------------------------------------------
# AUTHENTICATION MODULE (PATIENT, DOCTOR, ADMIN)
# -----------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Patient Registration route with form validation and password hashing."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()

        # Input Validations
        if not all([name, email, password, phone, age, gender]):
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template('register.html')

        try:
            age_int = int(age)
            if age_int <= 0 or age_int > 130:
                flash("Please enter a valid age between 1 and 130.", "warning")
                return render_template('register.html')
        except ValueError:
            flash("Age must be a valid number.", "warning")
            return render_template('register.html')

        # Check if email is already taken
        existing_patient = Database.query("SELECT patient_id FROM patients WHERE email = %s", (email,), one=True)
        if existing_patient:
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        # Secure password hashing
        hashed_password = generate_password_hash(password)

        try:
            Database.execute(
                "INSERT INTO patients (name, email, password, phone, age, gender) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, email, hashed_password, phone, age_int, gender)
            )
            flash("Registration successful! You can now log in to book appointments.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration error: {e}", "danger")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login handler with role selection: Patient, Doctor, or Admin."""
    if request.method == 'POST':
        role = request.form.get('role', 'patient').strip().lower()

        if role == 'patient':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            patient = Database.query("SELECT * FROM patients WHERE email = %s", (email,), one=True)

            if patient and check_password_hash(patient['password'], password):
                session.clear()
                session['user_id'] = patient['patient_id']
                session['role'] = 'patient'
                session['name'] = patient['name']
                flash(f"Welcome back, {patient['name']}!", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('patient_dashboard'))
            else:
                flash("Invalid patient email or password.", "danger")

        elif role == 'doctor':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            doctor = Database.query("SELECT * FROM doctors WHERE email = %s", (email,), one=True)

            if doctor and check_password_hash(doctor['password'], password):
                session.clear()
                session['user_id'] = doctor['doctor_id']
                session['role'] = 'doctor'
                session['name'] = doctor['name']
                flash(f"Welcome to your doctor portal, {doctor['name']}!", "success")
                return redirect(url_for('doctor_dashboard'))
            else:
                flash("Invalid doctor email or password.", "danger")

        elif role == 'admin':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            admin = Database.query("SELECT * FROM admin WHERE username = %s", (username,), one=True)

            if admin and check_password_hash(admin['password'], password):
                session.clear()
                session['user_id'] = admin['admin_id']
                session['role'] = 'admin'
                session['name'] = admin['username']
                flash("Logged in to Administrative Control Center.", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid admin credentials.", "danger")

        else:
            flash("Invalid role specified.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and log out the user."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('index'))


# -----------------------------------------------------------------------------
# PATIENT MODULE
# -----------------------------------------------------------------------------
@app.route('/patient/dashboard')
@login_required(role='patient')
def patient_dashboard():
    """Patient Dashboard showing overview, booking stats, and recent appointments."""
    patient_id = session['user_id']
    patient = Database.query("SELECT * FROM patients WHERE patient_id = %s", (patient_id,), one=True)

    # Fetch patient's appointments joined with doctors
    appointments = Database.query(
        """
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status,
               d.name AS doctor_name, d.specialization, d.consultation_fee
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """,
        (patient_id,)
    )

    # Calculate statistics
    stats = {
        'total': len(appointments),
        'pending': sum(1 for a in appointments if a['status'] == 'Pending'),
        'confirmed': sum(1 for a in appointments if a['status'] == 'Confirmed'),
        'completed': sum(1 for a in appointments if a['status'] == 'Completed'),
        'cancelled': sum(1 for a in appointments if a['status'] in ('Cancelled', 'Rejected'))
    }

    return render_template(
        'patient_dashboard.html',
        patient=patient,
        appointments=appointments,
        stats=stats
    )


@app.route('/book-appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required(role='patient')
def book_appointment(doctor_id):
    """
    Appointment Booking:
    Allows patient to select date and time for consultation with duplicate slot protection.
    """
    doctor = Database.query("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)
    if not doctor:
        flash("Selected doctor does not exist.", "danger")
        return redirect(url_for('doctors'))

    if request.method == 'POST':
        patient_id = session['user_id']
        appt_date_str = request.form.get('appointment_date', '').strip()
        appt_time = request.form.get('appointment_time', '').strip()
        reason = request.form.get('reason', '').strip()

        if not all([appt_date_str, appt_time, reason]):
            flash("All appointment details are required.", "danger")
            return render_template('book_appointment.html', doctor=doctor)

        # Validate that appointment date is not in the past
        try:
            appt_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
            if appt_date < date.today():
                flash("Appointment date cannot be in the past. Please select today or a future date.", "warning")
                return render_template('book_appointment.html', doctor=doctor)
        except ValueError:
            flash("Invalid date format provided.", "danger")
            return render_template('book_appointment.html', doctor=doctor)

        # DUPLICATE APPOINTMENT CHECK:
        # Check if the doctor is already booked for this specific date and time slot
        existing_slot = Database.query(
            """
            SELECT appointment_id FROM appointments 
            WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s 
              AND status NOT IN ('Cancelled', 'Rejected')
            """,
            (doctor_id, appt_date_str, appt_time),
            one=True
        )

        if existing_slot:
            flash(
                f"Notice: {doctor['name']} already has an active appointment at {appt_time} on {appt_date_str}. "
                "Please choose an alternate time slot.",
                "danger"
            )
            return render_template('book_appointment.html', doctor=doctor)

        # Insert new appointment with initial 'Pending' status
        try:
            Database.execute(
                """
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
                """,
                (patient_id, doctor_id, appt_date_str, appt_time, reason)
            )
            flash(
                f"Appointment booked successfully with {doctor['name']} for {appt_date_str} at {appt_time}! "
                "The doctor will review and confirm your request.",
                "success"
            )
            return redirect(url_for('my_appointments'))
        except Exception as e:
            flash(f"Booking failed due to an error: {e}", "danger")
            return render_template('book_appointment.html', doctor=doctor)

    return render_template('book_appointment.html', doctor=doctor)


@app.route('/my-appointments')
@login_required(role='patient')
def my_appointments():
    """View patient's full appointment history with status badges and cancel option."""
    patient_id = session['user_id']
    appointments = Database.query(
        """
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status,
               d.name AS doctor_name, d.specialization, d.qualification, d.consultation_fee
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """,
        (patient_id,)
    )
    return render_template('my_appointments.html', appointments=appointments)


@app.route('/appointment/cancel/<int:appointment_id>', methods=['POST'])
@login_required(role='patient')
def cancel_appointment(appointment_id):
    """Allow patient to cancel their upcoming or pending appointment."""
    patient_id = session['user_id']

    appt = Database.query(
        "SELECT * FROM appointments WHERE appointment_id = %s AND patient_id = %s",
        (appointment_id, patient_id),
        one=True
    )

    if not appt:
        flash("Appointment not found or unauthorized.", "danger")
        return redirect(url_for('my_appointments'))

    if appt['status'] == 'Completed':
        flash("Completed appointments cannot be cancelled.", "warning")
        return redirect(url_for('my_appointments'))

    Database.execute(
        "UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = %s",
        (appointment_id,)
    )
    flash(f"Appointment #APT-{appointment_id} has been cancelled successfully.", "info")
    return redirect(url_for('my_appointments'))


# -----------------------------------------------------------------------------
# DOCTOR MODULE
# -----------------------------------------------------------------------------
@app.route('/doctor/dashboard')
@login_required(role='doctor')
def doctor_dashboard():
    """Doctor Portal: View appointment requests, patient medical reasons and update status."""
    doctor_id = session['user_id']
    doctor = Database.query("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)

    appointments = Database.query(
        """
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status,
               p.patient_id, p.name AS patient_name, p.email AS patient_email, 
               p.phone AS patient_phone, p.age AS patient_age, p.gender AS patient_gender
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id = %s
        ORDER BY a.appointment_date ASC, a.appointment_time ASC
        """,
        (doctor_id,)
    )

    stats = {
        'total': len(appointments),
        'pending': sum(1 for a in appointments if a['status'] == 'Pending'),
        'confirmed': sum(1 for a in appointments if a['status'] == 'Confirmed'),
        'completed': sum(1 for a in appointments if a['status'] == 'Completed')
    }

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        appointments=appointments,
        stats=stats
    )


@app.route('/doctor/appointment/update/<int:appointment_id>', methods=['POST'])
@login_required(role='doctor')
def doctor_update_status(appointment_id):
    """Doctor accepts, rejects, or completes an appointment."""
    doctor_id = session['user_id']
    new_status = request.form.get('status', '').strip()

    valid_statuses = ['Confirmed', 'Rejected', 'Completed', 'Cancelled']
    if new_status not in valid_statuses:
        flash("Invalid appointment status specified.", "danger")
        return redirect(url_for('doctor_dashboard'))

    appt = Database.query(
        "SELECT * FROM appointments WHERE appointment_id = %s AND doctor_id = %s",
        (appointment_id, doctor_id),
        one=True
    )

    if not appt:
        flash("Appointment not found or unauthorized.", "danger")
        return redirect(url_for('doctor_dashboard'))

    Database.execute(
        "UPDATE appointments SET status = %s WHERE appointment_id = %s AND doctor_id = %s",
        (new_status, appointment_id, doctor_id)
    )

    flash(f"Appointment #APT-{appointment_id} marked as {new_status}.", "success")
    return redirect(url_for('doctor_dashboard'))


# -----------------------------------------------------------------------------
# ADMIN MODULE
# -----------------------------------------------------------------------------
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    """Admin Dashboard: Hospital stats, Doctor CRUD, Registered Patients, and All Appointments."""
    doctors_list = Database.query("SELECT * FROM doctors ORDER BY doctor_id DESC")
    patients_list = Database.query("SELECT * FROM patients ORDER BY patient_id DESC")
    appointments_list = Database.query(
        """
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status,
               p.name AS patient_name, p.phone AS patient_phone,
               d.name AS doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_id DESC
        """
    )

    stats = {
        'total_doctors': len(doctors_list),
        'total_patients': len(patients_list),
        'total_appointments': len(appointments_list),
        'completed_appointments': sum(1 for a in appointments_list if a['status'] == 'Completed')
    }

    return render_template(
        'admin_dashboard.html',
        doctors=doctors_list,
        patients=patients_list,
        appointments=appointments_list,
        stats=stats
    )


@app.route('/admin/doctor/add', methods=['POST'])
@login_required(role='admin')
def admin_add_doctor():
    """Admin creates a new doctor record with password hashing."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    specialization = request.form.get('specialization', '').strip()
    qualification = request.form.get('qualification', '').strip()
    experience = request.form.get('experience', '').strip()
    consultation_fee = request.form.get('consultation_fee', '').strip()
    available_days = request.form.get('available_days', '').strip()

    if not all([name, email, password, specialization, qualification, experience, consultation_fee, available_days]):
        flash("All fields are required to register a doctor.", "danger")
        return redirect(url_for('admin_dashboard'))

    # Check for existing doctor email
    existing = Database.query("SELECT doctor_id FROM doctors WHERE email = %s", (email,), one=True)
    if existing:
        flash(f"A doctor with email '{email}' already exists.", "warning")
        return redirect(url_for('admin_dashboard'))

    hashed_pw = generate_password_hash(password)

    try:
        Database.execute(
            """
            INSERT INTO doctors (name, email, password, specialization, qualification, experience, consultation_fee, available_days)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, hashed_pw, specialization, qualification, int(experience), float(consultation_fee), available_days)
        )
        flash(f"Doctor {name} added to the hospital directory successfully.", "success")
    except Exception as e:
        flash(f"Error adding doctor: {e}", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/doctor/edit/<int:doctor_id>', methods=['POST'])
@login_required(role='admin')
def admin_edit_doctor(doctor_id):
    """Admin updates an existing doctor's details."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    specialization = request.form.get('specialization', '').strip()
    qualification = request.form.get('qualification', '').strip()
    experience = request.form.get('experience', '').strip()
    consultation_fee = request.form.get('consultation_fee', '').strip()
    available_days = request.form.get('available_days', '').strip()
    new_password = request.form.get('password', '').strip()

    if not all([name, email, specialization, qualification, experience, consultation_fee, available_days]):
        flash("All required fields must be filled.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        if new_password:
            hashed_pw = generate_password_hash(new_password)
            Database.execute(
                """
                UPDATE doctors 
                SET name = %s, email = %s, password = %s, specialization = %s, 
                    qualification = %s, experience = %s, consultation_fee = %s, available_days = %s
                WHERE doctor_id = %s
                """,
                (name, email, hashed_pw, specialization, qualification, int(experience), float(consultation_fee), available_days, doctor_id)
            )
        else:
            Database.execute(
                """
                UPDATE doctors 
                SET name = %s, email = %s, specialization = %s, 
                    qualification = %s, experience = %s, consultation_fee = %s, available_days = %s
                WHERE doctor_id = %s
                """,
                (name, email, specialization, qualification, int(experience), float(consultation_fee), available_days, doctor_id)
            )
        flash(f"Doctor {name}'s details updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating doctor: {e}", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/doctor/delete/<int:doctor_id>', methods=['POST'])
@login_required(role='admin')
def admin_delete_doctor(doctor_id):
    """Admin deletes a doctor record."""
    doctor = Database.query("SELECT name FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    Database.execute("DELETE FROM doctors WHERE doctor_id = %s", (doctor_id,))
    flash(f"Doctor {doctor['name']} has been removed from the directory.", "info")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/appointment/status/<int:appointment_id>', methods=['POST'])
@login_required(role='admin')
def admin_update_appointment_status(appointment_id):
    """Admin updates appointment status (e.g. Pending, Confirmed, Completed, Cancelled)."""
    status = request.form.get('status', '').strip()
    Database.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", (status, appointment_id))
    flash(f"Appointment #APT-{appointment_id} status updated to {status}.", "success")
    return redirect(url_for('admin_dashboard'))


# -----------------------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 70)
    print("  ONLINE HOSPITAL APPOINTMENT SYSTEM")
    print("  Server running at: http://127.0.0.1:5000")
    print("  Database mode:     MySQL (Active: " + app.config.get('MYSQL_DB', 'hospital_db') + ")")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)
