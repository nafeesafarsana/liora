/* ==========================================================================
   LIORA — Profile Page JS
   Instant inline validation for profile picture upload.
   Checks file type and size immediately when user picks a file,
   before they even click Save Changes.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {

    const fileInput = document.querySelector('.profile-pic-input');
    if (!fileInput) return;

    // Create feedback element to show messages below the input
    const feedback = document.createElement('div');
    feedback.id = 'pic-feedback';
    feedback.style.marginTop = '8px';
    feedback.style.fontSize = '0.82rem';
    feedback.style.fontWeight = '500';
    fileInput.parentElement.appendChild(feedback);

    // Create image preview element
    const preview = document.createElement('img');
    preview.id = 'pic-preview';
    preview.style.cssText = `
        display: none;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #C8A96B;
        margin-top: 12px;
    `;
    fileInput.parentElement.appendChild(preview);

    const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    const MAX_SIZE_MB = 5;
    const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];

        // Reset state
        feedback.textContent = '';
        feedback.style.color = '';
        preview.style.display = 'none';
        preview.src = '';

        // Nothing selected — user cancelled
        if (!file) return;

        // Check 1 — file type
        if (!ALLOWED_TYPES.includes(file.type)) {
            showError(`❌ Invalid file type. Please upload a JPG, PNG, WebP, or GIF image.`);
            fileInput.value = '';
            return;
        }

        // Check 2 — file size
        if (file.size > MAX_SIZE_BYTES) {
            const sizeMB = (file.size / 1024 / 1024).toFixed(1);
            showError(`❌ File too large (${sizeMB}MB). Maximum allowed size is ${MAX_SIZE_MB}MB.`);
            fileInput.value = '';
            return;
        }

        // All checks passed — show preview
        showSuccess(`✓ Looks good! Click Save Changes to update your photo.`);
        showPreview(file);
    });

    function showError(message) {
        feedback.textContent = message;
        feedback.style.color = '#B23A48';
    }

    function showSuccess(message) {
        feedback.textContent = message;
        feedback.style.color = '#4C8C5A';
    }

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = 'block';

            // Also update the main avatar shown at the top of the form
            const currentPic = document.querySelector('.current-profile-pic');
            const defaultPic = document.querySelector('.default-profile-pic');
            if (currentPic) {
                currentPic.src = e.target.result;
            } else if (defaultPic) {
                // Replace initials div with an actual image preview
                const newImg = document.createElement('img');
                newImg.src = e.target.result;
                newImg.className = 'current-profile-pic';
                newImg.alt = 'Preview';
                newImg.style.cssText = `
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 2px solid #C8A96B;
                    flex-shrink: 0;
                `;
                defaultPic.parentElement.replaceChild(newImg, defaultPic);
            }
        };
        reader.readAsDataURL(file);
    }
});