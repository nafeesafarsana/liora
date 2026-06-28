document.addEventListener('DOMContentLoaded', function () {

    const confirmModal = document.getElementById('confirmActionModal');

    if (confirmModal) {
        confirmModal.addEventListener('show.bs.modal', function (event) {
            const triggerBtn = event.relatedTarget;
            if (!triggerBtn) return;

            const userId = triggerBtn.getAttribute('data-user-id');
            const userName = triggerBtn.getAttribute('data-user-name');
            const action = triggerBtn.getAttribute('data-action');

            const titleEl = confirmModal.querySelector('#confirmModalTitle');
            const messageEl = confirmModal.querySelector('#confirmModalMessage');
            const submitBtn = confirmModal.querySelector('#confirmModalSubmit');
            const form = confirmModal.querySelector('#confirmActionForm');

            if (action === 'block') {
                titleEl.textContent = 'Block User';
                messageEl.textContent = `Are you sure you want to block ${userName.trim()}? They will be immediately signed out and unable to log in.`;
                submitBtn.textContent = 'Block User';
                submitBtn.classList.remove('admin-btn-gold');
                submitBtn.classList.add('admin-btn-danger');
            } else {
                titleEl.textContent = 'Unblock User';
                messageEl.textContent = `Are you sure you want to unblock ${userName.trim()}? They will regain access to their account.`;
                submitBtn.textContent = 'Unblock User';
                submitBtn.classList.remove('admin-btn-danger');
                submitBtn.classList.add('admin-btn-gold');
            }

            const baseUrl = form.getAttribute('data-base-url');
            const targetUrl = baseUrl.replace('/0/', `/${userId}/`);
            form.setAttribute('action', targetUrl);
        });
    }

    const searchInput = document.querySelector('.admin-search-input');
    if (searchInput) {
        searchInput.addEventListener('focus', function () {
            searchInput.parentElement.classList.add('focused');
        });
        searchInput.addEventListener('blur', function () {
            searchInput.parentElement.classList.remove('focused');
        });
    }

    document.querySelectorAll('.admin-alert').forEach(function (alertEl) {
        setTimeout(function () {
            alertEl.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alertEl.style.opacity = '0';
            alertEl.style.transform = 'translateY(-8px)';
            setTimeout(function () { alertEl.remove(); }, 400);
        }, 5000);
    });
});