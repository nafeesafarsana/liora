/* ==========================================================================
   LIORA — Reset Password Page JS
   Password strength indicator + show/hide toggle.
   ========================================================================== */
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.toggle-password').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;

            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = 'Hide';
            } else {
                input.type = 'password';
                btn.textContent = 'Show';
            }
        });
    });

    const passwordInput = document.getElementById('newPassword');
    const strengthBar = document.getElementById('strengthBar');
    const strengthLabel = document.getElementById('strengthLabel');

    if (passwordInput && strengthBar && strengthLabel) {
        passwordInput.addEventListener('input', function () {
            const value = passwordInput.value;
            let score = 0;

            if (value.length >= 8) score++;
            if (/[A-Z]/.test(value)) score++;
            if (/[0-9]/.test(value)) score++;
            if (/[^A-Za-z0-9]/.test(value)) score++;

            strengthBar.className = 'strength-bar';

            if (value.length === 0) {
                strengthLabel.textContent = 'Password strength';
                return;
            }

            if (score <= 1) {
                strengthBar.classList.add('weak');
                strengthLabel.textContent = 'Weak password';
            } else if (score === 2) {
                strengthBar.classList.add('fair');
                strengthLabel.textContent = 'Fair password';
            } else if (score === 3) {
                strengthBar.classList.add('good');
                strengthLabel.textContent = 'Good password';
            } else {
                strengthBar.classList.add('strong');
                strengthLabel.textContent = 'Strong password';
            }
        });
    }
});