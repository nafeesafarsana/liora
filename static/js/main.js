/* ==========================================================================
   LIORA — Global JavaScript
   Mobile menu toggle + auto-dismiss messages, loaded on every page.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    // ---- Mobile menu toggle ----
    const menuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function () {
            mobileMenu.classList.toggle('open');
            menuToggle.classList.toggle('active');
        });
    }

    // ---- Auto-dismiss success/info messages after 5 seconds ----
    const messages = document.querySelectorAll('.message-alert');
    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-8px)';
            setTimeout(function () {
                msg.remove();
            }, 400);
        }, 5000);
    });

    // ---- Navbar shadow on scroll ----
    const navbar = document.getElementById('lioraNavbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 10) {
                navbar.style.boxShadow = '0 4px 20px rgba(74, 24, 54, 0.1)';
            } else {
                navbar.style.boxShadow = '0 2px 12px rgba(74, 24, 54, 0.04)';
            }
        });
    }
});