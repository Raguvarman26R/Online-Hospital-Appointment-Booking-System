"""
ONLINE HOSPITAL APPOINTMENT SYSTEM - AUTOMATED TEST SUITE
Covers Sprint 1 - Sprint 4 Agile Verification:
1. Registration testing
2. Login testing
3. Invalid input testing
4. Doctor search testing
5. Appointment booking testing
6. Duplicate appointment testing
7. Appointment cancellation testing
8. Database connectivity testing
9. Role-based authentication testing
"""

import unittest
from datetime import date, timedelta
from app import app
from config import Database, init_database

class HospitalSystemTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            init_database()
        cls.client = app.test_client()

    # -------------------------------------------------------------------------
    # TEST 1: Database Connectivity Testing
    # -------------------------------------------------------------------------
    def test_01_database_connectivity(self):
        """Test database connection and verify core tables exist."""
        doctors = Database.query("SELECT COUNT(*) AS count FROM doctors", one=True)
        self.assertIsNotNone(doctors)
        self.assertGreaterEqual(doctors['count'], 1)

        admin = Database.query("SELECT * FROM admin WHERE username = 'admin'", one=True)
        self.assertIsNotNone(admin)
        self.assertEqual(admin['username'], 'admin')

    # -------------------------------------------------------------------------
    # TEST 2: Patient Registration Testing (Valid Data)
    # -------------------------------------------------------------------------
    def test_02_patient_registration(self):
        """Test registering a new patient with valid details."""
        test_email = "alex.rivera@example.com"
        # Cleanup in case of previous run
        Database.execute("DELETE FROM patients WHERE email = %s", (test_email,))

        response = self.client.post('/register', data={
            'name': 'Alex Rivera',
            'email': test_email,
            'password': 'password123',
            'confirm_password': 'password123',
            'phone': '555-019-9988',
            'age': '29',
            'gender': 'Male'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registration successful", response.data)

        # Verify record in database
        patient = Database.query("SELECT * FROM patients WHERE email = %s", (test_email,), one=True)
        self.assertIsNotNone(patient)
        self.assertEqual(patient['name'], 'Alex Rivera')

    # -------------------------------------------------------------------------
    # TEST 3: Invalid Input Testing (Duplicate email, password mismatch)
    # -------------------------------------------------------------------------
    def test_03_invalid_input_testing(self):
        """Test registration errors on password mismatch and duplicate email."""
        # 1. Password mismatch
        response = self.client.post('/register', data={
            'name': 'Test User',
            'email': 'unique1@example.com',
            'password': 'password123',
            'confirm_password': 'different_password',
            'phone': '555-010-0000',
            'age': '25',
            'gender': 'Female'
        }, follow_redirects=True)
        self.assertIn(b"Passwords do not match", response.data)

        # 2. Duplicate email
        response2 = self.client.post('/register', data={
            'name': 'Duplicate User',
            'email': 'john.doe@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'phone': '555-010-0000',
            'age': '30',
            'gender': 'Male'
        }, follow_redirects=True)
        self.assertIn(b"already exists", response2.data)

    # -------------------------------------------------------------------------
    # TEST 4: Login Testing (Patient, Doctor, Admin)
    # -------------------------------------------------------------------------
    def test_04_login_testing(self):
        """Test authenticating Patient, Doctor, and Admin roles."""
        # 1. Patient Login
        resp_patient = self.client.post('/login', data={
            'role': 'patient',
            'email': 'john.doe@example.com',
            'password': 'patient123'
        }, follow_redirects=True)
        self.assertEqual(resp_patient.status_code, 200)
        self.assertIn(b"Welcome back, John Doe", resp_patient.data)

        # 2. Doctor Login
        resp_doc = self.client.post('/login', data={
            'role': 'doctor',
            'email': 'dr.sarah@hospital.com',
            'password': 'doctor123'
        }, follow_redirects=True)
        self.assertEqual(resp_doc.status_code, 200)
        self.assertIn(b"Dr. Aravind Kumar", resp_doc.data)

        # 3. Admin Login
        resp_admin = self.client.post('/login', data={
            'role': 'admin',
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(resp_admin.status_code, 200)
        self.assertIn(b"Hospital Management Dashboard", resp_admin.data)

    # -------------------------------------------------------------------------
    # TEST 5: Doctor Search Testing
    # -------------------------------------------------------------------------
    def test_05_doctor_search_testing(self):
        """Test searching doctors by name and filtering by specialization."""
        # Search by doctor name
        resp = self.client.get('/doctors?search=Aravind')
        self.assertIn(b"Dr. Aravind Kumar", resp.data)

        # Filter by Cardiology specialization
        resp_spec = self.client.get('/doctors?specialty=Cardiology')
        self.assertIn(b"Cardiology", resp_spec.data)
        self.assertIn(b"Dr. Aravind Kumar", resp_spec.data)

        # Doctor Details page
        resp_details = self.client.get('/doctor/1')
        self.assertEqual(resp_details.status_code, 200)
        self.assertIn(b"Dr. Aravind Kumar", resp_details.data)

    # -------------------------------------------------------------------------
    # TEST 6: Appointment Booking Testing
    # -------------------------------------------------------------------------
    def test_06_appointment_booking_testing(self):
        """Test patient scheduling a new appointment."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'patient'
            sess['name'] = 'John Doe'

        target_date = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
        target_time = '09:00 AM'

        # Cleanup slot if exists
        Database.execute(
            "DELETE FROM appointments WHERE doctor_id = 1 AND appointment_date = %s AND appointment_time = %s",
            (target_date, target_time)
        )

        resp = self.client.post('/book-appointment/1', data={
            'appointment_date': target_date,
            'appointment_time': target_time,
            'reason': 'Cardiac checkup and ECG reading'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Appointment booked successfully", resp.data)

        # Verify DB entry
        booked = Database.query(
            "SELECT * FROM appointments WHERE doctor_id = 1 AND appointment_date = %s AND appointment_time = %s",
            (target_date, target_time),
            one=True
        )
        self.assertIsNotNone(booked)
        self.assertEqual(booked['status'], 'Pending')

    # -------------------------------------------------------------------------
    # TEST 7: Duplicate Appointment Testing
    # -------------------------------------------------------------------------
    def test_07_duplicate_appointment_testing(self):
        """Test that booking the same doctor for identical date and time is rejected."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'patient'
            sess['name'] = 'John Doe'

        target_date = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')
        target_time = '11:00 AM'

        # Clean up slot if already exists from prior test runs
        Database.execute(
            "DELETE FROM appointments WHERE doctor_id = 1 AND appointment_date = %s AND appointment_time = %s",
            (target_date, target_time)
        )

        # Initial booking
        self.client.post('/book-appointment/1', data={
            'appointment_date': target_date,
            'appointment_time': target_time,
            'reason': 'First booking request'
        })

        # Second booking for SAME doctor, date, time
        dup_resp = self.client.post('/book-appointment/1', data={
            'appointment_date': target_date,
            'appointment_time': target_time,
            'reason': 'Duplicate booking attempt'
        }, follow_redirects=True)

        self.assertIn(b"already has an active appointment", dup_resp.data)

    # -------------------------------------------------------------------------
    # TEST 8: Appointment Cancellation Testing
    # -------------------------------------------------------------------------
    def test_08_appointment_cancellation_testing(self):
        """Test patient cancelling an active appointment."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'patient'
            sess['name'] = 'John Doe'

        target_date = (date.today() + timedelta(days=25)).strftime('%Y-%m-%d')
        target_time = '03:00 PM'

        # Clean up slot if already exists from prior test runs
        Database.execute(
            "DELETE FROM appointments WHERE doctor_id = 1 AND appointment_date = %s AND appointment_time = %s",
            (target_date, target_time)
        )

        Database.execute(
            "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) "
            "VALUES (1, 1, %s, %s, 'To be cancelled', 'Pending')",
            (target_date, target_time)
        )

        appt = Database.query(
            "SELECT appointment_id FROM appointments WHERE patient_id = 1 AND appointment_date = %s AND appointment_time = %s",
            (target_date, target_time),
            one=True
        )
        appt_id = appt['appointment_id']

        resp = self.client.post(f'/appointment/cancel/{appt_id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"cancelled successfully", resp.data)

        updated_appt = Database.query("SELECT status FROM appointments WHERE appointment_id = %s", (appt_id,), one=True)
        self.assertEqual(updated_appt['status'], 'Cancelled')

    # -------------------------------------------------------------------------
    # TEST 9: Role-Based Access Control Testing
    # -------------------------------------------------------------------------
    def test_09_role_based_authentication_testing(self):
        """Test that unauthenticated or unauthorized users are blocked from protected areas."""
        # 1. Guest trying to access patient dashboard
        with self.client.session_transaction() as sess:
            sess.clear()

        resp_guest = self.client.get('/patient/dashboard', follow_redirects=True)
        self.assertIn(b"Please log in to access this page", resp_guest.data)

        # 2. Patient trying to access admin dashboard
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'patient'
            sess['name'] = 'John Doe'

        resp_unauth = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"Unauthorized access", resp_unauth.data)

        # 3. Doctor trying to access admin dashboard
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'doctor'
            sess['name'] = 'Dr. Sarah'

        resp_unauth2 = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"Unauthorized access", resp_unauth2.data)

if __name__ == '__main__':
    unittest.main()
