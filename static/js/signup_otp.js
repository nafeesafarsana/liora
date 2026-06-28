/* ==========================================================================
   LIORA — Signup OTP Page JS
   Handles: digit auto-advance/backspace, paste support, countdown timer,
   and resend button cooldown.
   ========================================================================== */
document.addEventListener('DOMContentLoaded', function () {
    const otpBoxes = document.querySelectorAll('.otp-box');

    otpBoxes.forEach(function (box, index) {
        box.addEventListener('input', function () {
            box.value = box.value.replace(/[^0-9]/g, '');
            if (box.value.length === 1 && index < otpBoxes.length - 1) {
                otpBoxes[index + 1].focus();
            }
        });

        box.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && box.value === '' && index > 0) {
                otpBoxes[index - 1].focus();
            }
        });

        box.addEventListener('paste', function (e) {
            e.preventDefault();
            const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '');
            pasted.split('').slice(0, otpBoxes.length).forEach(function (char, i) {
                if (otpBoxes[i]) {
                    otpBoxes[i].value = char;
                }
            });
            const nextIndex = Math.min(pasted.length, otpBoxes.length - 1);
            otpBoxes[nextIndex].focus();
        });
    });

    // ---- Countdown timer (5 minutes = OTP expiry) ----
    let secondsLeft = 5 * 60;
    const countdownEl = document.getElementById('countdown');

    function updateCountdown() {
        if (!countdownEl) return;
        const minutes = Math.floor(secondsLeft / 60);
        const seconds = secondsLeft % 60;
        countdownEl.textContent =
            String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');

        if (secondsLeft <= 30) {
            countdownEl.classList.add('expiring');
        }

        if (secondsLeft <= 0) {
            clearInterval(countdownTimer);
            countdownEl.textContent = '00:00';
        } else {
            secondsLeft--;
        }
    }

    updateCountdown();
    const countdownTimer = setInterval(updateCountdown, 1000);

    // ---- Resend button cooldown (30 seconds) ----
    let cooldown = 30;
    const resendBtn = document.getElementById('resendBtn');
    const resendCooldownEl = document.getElementById('resendCooldown');

    function updateResendCooldown() {
        if (!resendBtn || !resendCooldownEl) return;
        if (cooldown <= 0) {
            resendBtn.disabled = false;
            resendBtn.textContent = 'Resend Code';
            clearInterval(resendTimer);
        } else {
            resendCooldownEl.textContent = cooldown;
            cooldown--;
        }
    }

    updateResendCooldown();
    const resendTimer = setInterval(updateResendCooldown, 1000);
});