import os
import sys
import sqlite3
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hospital-appointment-system-secret-key-2026')
    
    # MySQL Database Configurations
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'hospital_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    
    # SQLite Fallback File (for testing without local MySQL service)
    SQLITE_DB = os.environ.get('SQLITE_DB', str(BASE_DIR / 'hospital.db'))

# Global flag to track active database backend
ACTIVE_BACKEND = 'mysql'

import socket

def check_mysql_availability():
    """Check if MySQL server is reachable with instantaneous socket probe."""
    try:
        # Fast socket test to check if port 3306 is listening
        with socket.create_connection((Config.MYSQL_HOST, Config.MYSQL_PORT), timeout=0.3):
            pass
    except Exception as e:
        return False, f"Port {Config.MYSQL_PORT} unreachable: {e}"

    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            connection_timeout=2
        )
        conn.close()
        return True, "mysql.connector"
    except Exception:
        pass
        
    try:
        import pymysql
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            connect_timeout=2
        )
        conn.close()
        return True, "pymysql"
    except Exception as e:
        return False, str(e)

def init_database():
    """
    Initializes the database with schema and sample seed records.
    Connects to MySQL if available; otherwise initializes SQLite fallback.
    """
    global ACTIVE_BACKEND
    mysql_ok, driver_or_err = check_mysql_availability()
    
    if mysql_ok:
        ACTIVE_BACKEND = 'mysql'
        try:
            if driver_or_err == "mysql.connector":
                import mysql.connector
                conn = mysql.connector.connect(
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    port=Config.MYSQL_PORT
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
                conn.database = Config.MYSQL_DB
            else:
                import pymysql
                conn = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    port=Config.MYSQL_PORT
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
                conn.select_db(Config.MYSQL_DB)
            
            # Check if tables exist
            cursor.execute("SHOW TABLES LIKE 'doctors'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                sql_path = BASE_DIR / 'database.sql'
                if sql_path.exists():
                    with open(sql_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # Split statements
                    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
                    for stmt in statements:
                        if stmt.upper().startswith('CREATE DATABASE') or stmt.upper().startswith('USE '):
                            continue
                        cursor.execute(stmt)
                    conn.commit()
            cursor.close()
            conn.close()
            print("[Database] Successfully connected and verified MySQL database:", Config.MYSQL_DB)
            return True
        except Exception as e:
            print(f"[Database Warning] MySQL connection encountered error: {e}. Falling back to SQLite.")
            ACTIVE_BACKEND = 'sqlite'
    else:
        ACTIVE_BACKEND = 'sqlite'
        print(f"[Database Notice] MySQL server is not running on localhost:3306 ({driver_or_err}).")
        print("[Database Notice] Seamlessly activated local SQLite fallback for immediate testing & demo.")

    # Initialize SQLite schema if active
    if ACTIVE_BACKEND == 'sqlite':
        _init_sqlite_db()
    return True

def _init_sqlite_db():
    """Initializes local SQLite database with identical schema and sample seed records."""
    db_file = Config.SQLITE_DB
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors'")
    if not cursor.fetchone():
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            specialization TEXT NOT NULL,
            qualification TEXT NOT NULL,
            experience INTEGER NOT NULL,
            consultation_fee REAL NOT NULL,
            available_days TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
            UNIQUE (doctor_id, appointment_date, appointment_time)
        );

        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Seed Default Admin
        INSERT OR IGNORE INTO admin (username, password) VALUES
        ('admin', 'scrypt:32768:8:1$fdAsZFjQCpvvwE5k$998872ba700047e48dd7b16eddd538e96aa371f843a620df7a4cdc3a3f23d8a94282d288d3894f3322bf2f66e8a8b209f66db1998f1084e9172b28b46de6896e');

        -- Seed Sample Doctors
        INSERT OR IGNORE INTO doctors (name, email, password, specialization, qualification, experience, consultation_fee, available_days) VALUES
        ('Dr. Aravind Kumar', 'dr.sarah@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Cardiology', 'MD, FACC - Harvard Medical', 12, 1000.00, 'Monday, Wednesday, Friday'),
        ('Dr. Meenakshi Sundaram', 'dr.robert@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Neurology', 'MD, DM Neurology - Johns Hopkins', 15, 1000.00, 'Tuesday, Thursday, Saturday'),
        ('Dr. Kavya Priya', 'dr.emily@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Pediatrics', 'MBBS, DCH, FAAP - Oxford University', 9, 1000.00, 'Monday, Tuesday, Wednesday, Friday'),
        ('Dr. Suresh Babu', 'dr.michael@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Orthopedics', 'MS Ortho, MCh - Stanford University', 14, 1000.00, 'Wednesday, Thursday, Saturday'),
        ('Dr. Nandhini Raj', 'dr.olivia@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Dermatology', 'MD Dermatology - Yale Medicine', 8, 1000.00, 'Monday, Thursday, Friday'),
        ('Dr. Vigneshwaran', 'dr.david@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'General Medicine', 'MBBS, MD Internal Medicine', 10, 1000.00, 'Monday, Tuesday, Wednesday, Thursday, Friday');

        -- Seed Sample Patients
        INSERT OR IGNORE INTO patients (name, email, password, phone, age, gender) VALUES
        ('John Doe', 'john.doe@example.com', 'scrypt:32768:8:1$c5sxnnkccmx2kyTD$5eb0fb0ec22b6f66de0a3eba19279db2aff6a9f838a73277fc7d37c319bdca830f5d6cf0e9483503376f19abfe5e3e27dfe2e3bd0259b9c54f78527bd71a53f9', '555-019-2834', 34, 'Male'),
        ('Jane Smith', 'jane.smith@example.com', 'scrypt:32768:8:1$c5sxnnkccmx2kyTD$5eb0fb0ec22b6f66de0a3eba19279db2aff6a9f838a73277fc7d37c319bdca830f5d6cf0e9483503376f19abfe5e3e27dfe2e3bd0259b9c54f78527bd71a53f9', '555-014-9921', 28, 'Female');

        -- Seed Sample Appointments
        INSERT OR IGNORE INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES
        (1, 1, '2026-11-05', '10:00 AM', 'Routine cardiovascular health checkup and blood pressure monitoring.', 'Confirmed'),
        (1, 3, '2026-11-12', '02:30 PM', 'Consultation for child fever and cough symptoms.', 'Pending'),
        (2, 2, '2026-11-08', '11:30 AM', 'Severe migraine headaches recurring weekly.', 'Confirmed');
        ''')
        conn.commit()
    conn.close()

class Database:
    """Unified Database Client that provides dictionary-like records for MySQL and SQLite."""
    
    @staticmethod
    def get_connection():
        global ACTIVE_BACKEND
        if ACTIVE_BACKEND == 'mysql':
            try:
                import mysql.connector
                conn = mysql.connector.connect(
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    port=Config.MYSQL_PORT
                )
                return conn, 'mysql'
            except Exception:
                pass
            try:
                import pymysql
                conn = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    port=Config.MYSQL_PORT,
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn, 'pymysql'
            except Exception:
                ACTIVE_BACKEND = 'sqlite'
                
        # SQLite connection
        conn = sqlite3.connect(Config.SQLITE_DB)
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

    @classmethod
    def query(cls, sql, params=(), one=False):
        """Execute a SELECT query and return list of dictionaries or single dictionary."""
        conn, backend = cls.get_connection()
        try:
            if backend == 'mysql':
                # mysql.connector with dictionary cursor
                cursor = conn.cursor(dictionary=True)
                cursor.execute(sql, params)
                res = cursor.fetchone() if one else cursor.fetchall()
                cursor.close()
                return res
            elif backend == 'pymysql':
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    res = cursor.fetchone() if one else cursor.fetchall()
                    return res
            else:
                # Convert %s to ? for SQLite compatibility
                sqlite_sql = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, params)
                rows = cursor.fetchall()
                cursor.close()
                if one:
                    return dict(rows[0]) if rows else None
                return [dict(row) for row in rows]
        finally:
            conn.close()

    @classmethod
    def execute(cls, sql, params=()):
        """Execute INSERT, UPDATE, DELETE query and return lastrowid / affected rows."""
        conn, backend = cls.get_connection()
        try:
            if backend == 'mysql':
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                cursor.close()
                return last_id if last_id else row_count
            elif backend == 'pymysql':
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            else:
                sqlite_sql = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sqlite_sql, params)
                conn.commit()
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                cursor.close()
                return last_id if last_id else row_count
        finally:
            conn.close()
