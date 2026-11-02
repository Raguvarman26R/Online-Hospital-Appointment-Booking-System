-- ====================================================================
-- ONLINE HOSPITAL APPOINTMENT SYSTEM - DATABASE SCRIPT
-- Database: MySQL
-- ====================================================================

CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- --------------------------------------------------------------------
-- 1. Table structure for table: patients
-- --------------------------------------------------------------------
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS patients;
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 2. Table structure for table: doctors
-- --------------------------------------------------------------------
DROP TABLE IF EXISTS doctors;
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    qualification VARCHAR(100) NOT NULL,
    experience INT NOT NULL,
    consultation_fee DECIMAL(10,2) NOT NULL,
    available_days VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 3. Table structure for table: appointments
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    UNIQUE KEY unique_booking (doctor_id, appointment_date, appointment_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------------
-- 4. Table structure for table: admin
-- --------------------------------------------------------------------
DROP TABLE IF EXISTS admin;
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- SEED DATA FOR TESTING AND EVALUATION
-- ====================================================================

-- Default Admin Account (Username: admin | Password: admin123)
INSERT INTO admin (username, password) VALUES
('admin', 'scrypt:32768:8:1$fdAsZFjQCpvvwE5k$998872ba700047e48dd7b16eddd538e96aa371f843a620df7a4cdc3a3f23d8a94282d288d3894f3322bf2f66e8a8b209f66db1998f1084e9172b28b46de6896e');

-- Seed Doctors across multiple specializations (Password for all: doctor123)
INSERT INTO doctors (name, email, password, specialization, qualification, experience, consultation_fee, available_days) VALUES
('Dr. Aravind Kumar', 'dr.sarah@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Cardiology', 'MD, FACC - Harvard Medical', 12, 1000.00, 'Monday, Wednesday, Friday'),
('Dr. Meenakshi Sundaram', 'dr.robert@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Neurology', 'MD, DM Neurology - Johns Hopkins', 15, 1000.00, 'Tuesday, Thursday, Saturday'),
('Dr. Kavya Priya', 'dr.emily@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Pediatrics', 'MBBS, DCH, FAAP - Oxford University', 9, 1000.00, 'Monday, Tuesday, Wednesday, Friday'),
('Dr. Suresh Babu', 'dr.michael@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Orthopedics', 'MS Ortho, MCh - Stanford University', 14, 1000.00, 'Wednesday, Thursday, Saturday'),
('Dr. Nandhini Raj', 'dr.olivia@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'Dermatology', 'MD Dermatology - Yale Medicine', 8, 1000.00, 'Monday, Thursday, Friday'),
('Dr. Vigneshwaran', 'dr.david@hospital.com', 'scrypt:32768:8:1$JJH5yEHcFz7r7s2j$86d7ca35800d56a51a8e7e35161649b7d45ffea76535e1779177a072a7eec351f70a15330431398e1ad4b9977a8f7dc84f0d39223aa845b5cc6b033b6f85efe4', 'General Medicine', 'MBBS, MD Internal Medicine', 10, 1000.00, 'Monday, Tuesday, Wednesday, Thursday, Friday');

-- Seed Sample Patient (Email: john.doe@example.com | Password: patient123)
INSERT INTO patients (name, email, password, phone, age, gender) VALUES
('John Doe', 'john.doe@example.com', 'scrypt:32768:8:1$c5sxnnkccmx2kyTD$5eb0fb0ec22b6f66de0a3eba19279db2aff6a9f838a73277fc7d37c319bdca830f5d6cf0e9483503376f19abfe5e3e27dfe2e3bd0259b9c54f78527bd71a53f9', '555-019-2834', 34, 'Male'),
('Jane Smith', 'jane.smith@example.com', 'scrypt:32768:8:1$c5sxnnkccmx2kyTD$5eb0fb0ec22b6f66de0a3eba19279db2aff6a9f838a73277fc7d37c319bdca830f5d6cf0e9483503376f19abfe5e3e27dfe2e3bd0259b9c54f78527bd71a53f9', '555-014-9921', 28, 'Female');

-- Seed Sample Appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES
(1, 1, '2026-11-05', '10:00 AM', 'Routine cardiovascular health checkup and blood pressure monitoring.', 'Confirmed'),
(1, 3, '2026-11-12', '02:30 PM', 'Consultation for child fever and cough symptoms.', 'Pending'),
(2, 2, '2026-11-08', '11:30 AM', 'Severe migraine headaches recurring weekly.', 'Confirmed');
