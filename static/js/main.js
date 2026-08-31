// main.js - Custom JavaScript for System Enhancements

document.addEventListener("turbo:load", function () {
    'use strict'

    // ==========================================
    // 1. Form Validation & UX (Loading State)
    // ==========================================
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            // Check HTML5 validity
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show a generic toast error for invalid forms
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'error',
                    title: 'يرجى التأكد من إدخال جميع الحقول المطلوبة بشكل صحيح',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true
                });
            } else {
                // If valid, show loading state on submit button
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.classList.contains('ajax-form')) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...`;
                    // Allow the form to submit normally
                }
            }
            form.classList.add('was-validated');
        }, false);
    });

    // ==========================================
    // 2. AJAX Form Submissions (Optional for future)
    // ==========================================
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري المعالجة...`;

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: form.method,
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const result = await response.json();
                
                if (response.ok) {
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: 'success',
                        title: result.message || 'تمت العملية بنجاح',
                        showConfirmButton: false,
                        timer: 3000
                    });
                    if (result.redirect) {
                        setTimeout(() => window.location.href = result.redirect, 1000);
                    } else {
                        form.reset();
                        form.classList.remove('was-validated');
                    }
                } else {
                    throw new Error(result.error || 'حدث خطأ أثناء العملية');
                }
            } catch (error) {
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'error',
                    title: error.message,
                    showConfirmButton: false,
                    timer: 3000
                });
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    });

    // ==========================================
    // 3. AJAX Deletions with Confirmation (UX)
    // ==========================================
    const deleteButtons = document.querySelectorAll('.ajax-delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url || this.closest('form').action;
            const row = this.closest('tr'); // Assuming the delete button is in a table row
            
            Swal.fire({
                title: 'هل أنت متأكد؟',
                text: "لن تتمكن من التراجع عن هذا الإجراء!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'نعم، احذف!',
                cancelButtonText: 'إلغاء'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Send AJAX Delete request
                    fetch(url, {
                        method: 'POST', // or DELETE if your API supports it, using POST for standard Flask forms
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded'
                        },
                        body: '_method=DELETE' // Simulate delete method if needed
                    })
                    .then(response => {
                        if (response.ok || response.redirected) {
                            // Also handles case where flask redirects after successful delete
                            Swal.fire(
                                'تم الحذف!',
                                'تم حذف السجل بنجاح.',
                                'success'
                            );
                            if (row) {
                                // Smooth fade out
                                row.style.transition = "opacity 0.5s ease";
                                row.style.opacity = 0;
                                setTimeout(() => row.remove(), 500);
                            } else {
                                setTimeout(() => window.location.reload(), 1000);
                            }
                        } else {
                            throw new Error('فشل الحذف');
                        }
                    })
                    .catch(error => {
                        Swal.fire(
                            'خطأ!',
                            'حدث خطأ أثناء محاولة الحذف.',
                            'error'
                        );
                    });
                }
            });
        });
    });
});

// ==========================================
// 4. Responsive Mobile Sidebar & Dropdown Manager
// ==========================================
function setupResponsiveSidebar() {
    const sidebarBtn = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    let overlay = document.getElementById('sidebarOverlay');

    if (!overlay && document.body) {
        overlay = document.createElement('div');
        overlay.id = 'sidebarOverlay';
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    function toggleSidebar(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        if (!sidebar) return;
        const isActive = sidebar.classList.contains('active');
        if (isActive) {
            sidebar.classList.remove('active');
            if (overlay) overlay.classList.remove('active');
        } else {
            sidebar.classList.add('active');
            if (overlay) overlay.classList.add('active');
        }
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
    }

    if (sidebarBtn) {
        sidebarBtn.removeEventListener('click', toggleSidebar);
        sidebarBtn.addEventListener('click', toggleSidebar);
    }

    if (overlay) {
        overlay.removeEventListener('click', closeSidebar);
        overlay.addEventListener('click', closeSidebar);
    }

    // Auto-close sidebar when clicking links on mobile (< 992px)
    if (sidebar) {
        const sidebarLinks = sidebar.querySelectorAll('a:not(.dropdown-toggle)');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    closeSidebar();
                }
            });
        });
    }

    // Ensure all Bootstrap Dropdowns are properly initialized
    if (window.bootstrap && window.bootstrap.Dropdown) {
        const dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
        dropdownElementList.map(function (dropdownToggleEl) {
            return bootstrap.Dropdown.getOrCreateInstance(dropdownToggleEl);
        });
    }
}

document.addEventListener("DOMContentLoaded", setupResponsiveSidebar);
document.addEventListener("turbo:load", setupResponsiveSidebar);
