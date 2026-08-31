/* ==========================================================================
   LIORA — Product Detail Page JS
   Inline magnifier zoom + thumbnail switching + quantity controls
   ========================================================================== */
document.addEventListener('DOMContentLoaded', function () {

    const mainImageWrap = document.getElementById('mainImageWrap');
    const mainImage = document.getElementById('mainImage');
    const zoomLens = document.getElementById('zoomLens');

    if (mainImageWrap && mainImage && zoomLens) {

        const ZOOM_LEVEL = 3;
        const LENS_SIZE = 150;

        // Style the lens as the zoom window itself
        zoomLens.style.cssText = `
            position: absolute;
            width: ${LENS_SIZE}px;
            height: ${LENS_SIZE}px;
            border-radius: 50%;
            border: 3px solid #C8A96B;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            cursor: crosshair;
            display: none;
            pointer-events: none;
            z-index: 10;
            background-color: white;
            background-repeat: no-repeat;
        `;

        mainImageWrap.addEventListener('mouseenter', function () {
            zoomLens.style.display = 'block';
        });

        mainImageWrap.addEventListener('mouseleave', function () {
            zoomLens.style.display = 'none';
        });

        mainImageWrap.addEventListener('mousemove', function (e) {
            const rect = mainImageWrap.getBoundingClientRect();
            const wrapW = rect.width;
            const wrapH = rect.height;
            const half = LENS_SIZE / 2;

            // Mouse position relative to image wrap
            let x = e.clientX - rect.left;
            let y = e.clientY - rect.top;

            // Position lens centered on cursor, kept within bounds
            let lensX = x - half;
            let lensY = y - half;

            lensX = Math.max(0, Math.min(lensX, wrapW - LENS_SIZE));
            lensY = Math.max(0, Math.min(lensY, wrapH - LENS_SIZE));

            zoomLens.style.left = lensX + 'px';
            zoomLens.style.top = lensY + 'px';

            // Zoom background inside the lens
            const bgX = -((lensX) * ZOOM_LEVEL) + half;
            const bgY = -((lensY) * ZOOM_LEVEL) + half;

            zoomLens.style.backgroundImage = `url('${mainImage.src}')`;
            zoomLens.style.backgroundSize = `${wrapW * ZOOM_LEVEL}px ${wrapH * ZOOM_LEVEL}px`;
            zoomLens.style.backgroundPosition = `${bgX}px ${bgY}px`;
        });
    }

    // ---- Thumbnail image switcher ----
    window.changeMainImage = function (thumbnail, imageUrl) {
        if (mainImage) {
            mainImage.src = imageUrl;
        }
        document.querySelectorAll('.thumbnail').forEach(function (thumb) {
            thumb.classList.remove('active');
        });
        thumbnail.classList.add('active');
    };

    // ---- Quantity controls ----
    const qtyMinus = document.getElementById('qtyMinus');
    const qtyPlus = document.getElementById('qtyPlus');
    const qtyInput = document.getElementById('quantityInput');
    const cartQuantity = document.getElementById('cartQuantity');

    if (qtyMinus && qtyPlus && qtyInput) {
        const maxStock = parseInt(qtyInput.getAttribute('max')) || 10;

        qtyMinus.addEventListener('click', function () {
            let current = parseInt(qtyInput.value);
            if (current > 1) {
                qtyInput.value = current - 1;
                if (cartQuantity) cartQuantity.value = current - 1;
            }
        });

        qtyPlus.addEventListener('click', function () {
            let current = parseInt(qtyInput.value);
            if (current < maxStock) {
                qtyInput.value = current + 1;
                if (cartQuantity) cartQuantity.value = current + 1;
            } else {
                alert(`Maximum ${maxStock} units allowed.`);
            }
        });
    }




// ---- Color selection ----
window.selectColor = function (btn) {
    // Remove active from all
    document.querySelectorAll('.color-option').forEach(function (b) {
        b.classList.remove('active');
    });

    // Mark this one active
    btn.classList.add('active');

    const colorName = btn.getAttribute('data-color-name');
    const colorStock = parseInt(btn.getAttribute('data-color-stock'));
    const hex = btn.getAttribute('data-hex');

    // Update stock display
    const stockDisplay = document.getElementById('stockDisplay');
    if (stockDisplay) {
        if (colorStock > 10) {
            stockDisplay.innerHTML = `<span class="stock-badge stock-in">In Stock</span>`;
        } else if (colorStock > 0) {
            stockDisplay.innerHTML = `<span class="stock-badge stock-low">Only ${colorStock} left!</span>`;
        } else {
            stockDisplay.innerHTML = `<span class="stock-badge stock-out">Out of Stock</span>`;
        }
    }

    // Update quantity max to color stock
    const qtyInput = document.getElementById('quantityInput');
    if (qtyInput) {
        qtyInput.setAttribute('max', colorStock);
        if (parseInt(qtyInput.value) > colorStock) {
            qtyInput.value = colorStock;
        }
    }

    // Show selected color info
    const info = document.getElementById('selectedColorInfo');
    if (info) {
        info.innerHTML = `
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%;
                         background:${hex}; margin-right:6px; border:1px solid #ccc;"></span>
            <strong>${colorName}</strong> — ${colorStock} available
        `;
    }
};
});