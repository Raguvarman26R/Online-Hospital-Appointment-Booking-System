/**
 * Online Hospital Appointment System - Client JavaScript
 * Interactive functionality, form validations, and UX enhancements
 */

document.addEventListener('DOMContentLoaded', function () {
    // Keep Bootstrap modals outside transformed/overflow-hidden containers.
    document.querySelectorAll('.modal').forEach(function (modal) {
        document.body.appendChild(modal);
    });

    // 1. Auto-dismiss bootstrap alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Set Minimum Date for Appointment Booking to Today
    const dateInput = document.getElementById('appointment_date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
    }

    // 3. Password Confirmation Check on Registration
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const errorDiv = document.getElementById('passwordMismatchError');

            if (password !== confirmPassword) {
                e.preventDefault();
                if (errorDiv) {
                    errorDiv.classList.remove('d-none');
                } else {
                    alert('Passwords do not match. Please verify your input.');
                }
            } else {
                if (errorDiv) errorDiv.classList.add('d-none');
            }
        });
    }

    // 4. Client-side Doctor Search Filter (Instant Filtering)
    const doctorSearchInput = document.getElementById('doctorSearchInput');
    const specialtyFilter = document.getElementById('specialtyFilter');
    if (doctorSearchInput && specialtyFilter) {
        function filterDoctors() {
            const query = doctorSearchInput.value.toLowerCase().trim();
            const selectedSpec = specialtyFilter.value.toLowerCase().trim();
            const doctorCards = document.querySelectorAll('.doctor-card-item');

            let visibleCount = 0;
            doctorCards.forEach(function (card) {
                const name = card.getAttribute('data-name').toLowerCase();
                const spec = card.getAttribute('data-specialty').toLowerCase();

                const matchesQuery = !query || name.includes(query) || spec.includes(query);
                const matchesSpec = !selectedSpec || spec === selectedSpec || spec.includes(selectedSpec);

                if (matchesQuery && matchesSpec) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            const noResultsNotice = document.getElementById('noDoctorsNotice');
            if (noResultsNotice) {
                noResultsNotice.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        }

        doctorSearchInput.addEventListener('input', filterDoctors);
        specialtyFilter.addEventListener('change', filterDoctors);
    }
});

// Demo Credential Quick-Filler for Evaluation
function fillCredentials(role) {
    if (role === 'patient') {
        const emailInput = document.getElementById('patient_email');
        const passInput = document.getElementById('patient_password');
        if (emailInput && passInput) {
            emailInput.value = 'john.doe@example.com';
            passInput.value = 'patient123';
        }
    } else if (role === 'doctor') {
        const emailInput = document.getElementById('doctor_email');
        const passInput = document.getElementById('doctor_password');
        if (emailInput && passInput) {
            emailInput.value = 'dr.sarah@hospital.com';
            passInput.value = 'doctor123';
        }
    } else if (role === 'admin') {
        const userInput = document.getElementById('admin_username');
        const passInput = document.getElementById('admin_password');
        if (userInput && passInput) {
            userInput.value = 'admin';
            passInput.value = 'admin123';
        }
    }
}
