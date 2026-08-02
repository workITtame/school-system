/**
 * Student Form UX Enhancements (Enterprise SaaS Edition)
 * Features: Draft Auto-Save, Unsaved Warning, Inline Validation, Enter Key Navigation,
 * Progress Indicator, Phone Formatting, Scroll to Error, SweetAlert2 Confirmation & Loading.
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', initStudentFormUX);
    document.addEventListener('turbo:load', initStudentFormUX);

    function initStudentFormUX() {
        const form = document.getElementById('studentForm');
        if (!form) return;

        const DRAFT_KEY = 'school_system_student_form_draft_' + (form.action.includes('edit') ? 'edit' : 'add');
        let isDirty = false;

        const progressPercentEl = document.getElementById('wizardProgressPercent');
        const progressBarEl = document.getElementById('wizardProgressBar');
        const phoneInput = document.getElementById('inputParentPhone');
        const classSelect = document.getElementById('inputClass');
        const sectionSelect = document.getElementById('inputSection');

        // -------------------------------------------------------------
        // 1. Auto Save Draft to LocalStorage & Restore
        // -------------------------------------------------------------
        function saveDraft() {
            const formData = {};
            const inputs = form.querySelectorAll('input:not([type="file"]):not([type="password"]), select, textarea');
            inputs.forEach(input => {
                if (input.name) formData[input.name] = input.value;
            });
            localStorage.setItem(DRAFT_KEY, JSON.stringify(formData));
            showToast('تم حفظ مسودة البيانات تلقائياً', 'info');
        }

        function restoreDraft() {
            if (form.action.includes('edit')) return; // Don't restore draft on Edit mode to preserve loaded DB values
            const saved = localStorage.getItem(DRAFT_KEY);
            if (!saved) return;

            try {
                const data = JSON.parse(saved);
                let restoredCount = 0;
                Object.keys(data).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input && data[key]) {
                        input.value = data[key];
                        restoredCount++;
                    }
                });

                if (restoredCount > 0) {
                    showToast('تم استعادة المسودة المسجلة سابقاً', 'success');
                }
            } catch (e) {
                console.error('Draft restore error:', e);
            }
        }

        // Trigger draft saving on input/change (debounced)
        let saveTimeout;
        form.addEventListener('input', () => {
            isDirty = true;
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(saveDraft, 1200);
        });
        form.addEventListener('change', () => {
            isDirty = true;
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(saveDraft, 800);
        });

        // -------------------------------------------------------------
        // 2. Unsaved Changes Warning
        // -------------------------------------------------------------
        window.addEventListener('beforeunload', (e) => {
            if (isDirty) {
                e.preventDefault();
                e.returnValue = 'لديك تعديلات غير محفوظة، هل أنت تأكد من مغادرة الصفحة؟';
            }
        });

        // -------------------------------------------------------------
        // 3. Inline Live Validation & Feedback
        // -------------------------------------------------------------
        const allInputs = form.querySelectorAll('input, select');
        allInputs.forEach(input => {
            input.addEventListener('blur', () => validateInput(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    validateInput(input);
                }
            });
        });

        function validateInput(input) {
            if (input.checkValidity()) {
                input.classList.remove('is-invalid');
                if (input.value.trim() !== '') {
                    input.classList.add('is-valid');
                }
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        }

        // -------------------------------------------------------------
        // 4. Keyboard Navigation (Enter key advances to next field/step)
        // -------------------------------------------------------------
        form.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.type !== 'submit') {
                e.preventDefault();
                const visibleInputs = Array.from(form.querySelectorAll('.form-step-pane.active input, .form-step-pane.active select'));
                const currentIndex = visibleInputs.indexOf(e.target);

                if (currentIndex >= 0 && currentIndex < visibleInputs.length - 1) {
                    visibleInputs[currentIndex + 1].focus();
                } else {
                    const nextBtn = document.getElementById('nextBtn');
                    if (nextBtn && nextBtn.style.display !== 'none') {
                        nextBtn.click();
                    }
                }
            }
        });

        // -------------------------------------------------------------
        // 5. Phone Number Formatting
        // -------------------------------------------------------------
        if (phoneInput) {
            phoneInput.addEventListener('input', function (e) {
                let x = e.target.value.replace(/\D/g, '').match(/(\d{0,4})(\d{0,3})(\d{0,3})/);
                if (x) {
                    e.target.value = !x[2] ? x[1] : `${x[1]} ${x[2]}` + (x[3] ? ` ${x[3]}` : '');
                }
            });
        }

        // -------------------------------------------------------------
        // 6. Dependent Dropdowns (Class -> Section Filter)
        // -------------------------------------------------------------
        if (classSelect && sectionSelect) {
            classSelect.addEventListener('change', function () {
                const selectedClass = this.value;
                const options = sectionSelect.querySelectorAll('option');
                options.forEach(opt => {
                    if (!opt.value) return;
                    const optClass = opt.getAttribute('data-class-id');
                    if (optClass && selectedClass) {
                        opt.style.display = optClass === selectedClass ? 'block' : 'none';
                    } else {
                        opt.style.display = 'block';
                    }
                });
            });
        }

        // -------------------------------------------------------------
        // 7. Auto Scroll to First Invalid Error
        // -------------------------------------------------------------
        window.scrollToFirstError = function (pane) {
            const firstInvalid = pane.querySelector('.is-invalid, :invalid');
            if (firstInvalid) {
                firstInvalid.focus();
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        };

        // -------------------------------------------------------------
        // 8. Confirmation Dialog & Loading Overlay on Submit
        // -------------------------------------------------------------
        form.addEventListener('submit', function (e) {
            isDirty = false;
            localStorage.removeItem(DRAFT_KEY);

            if (typeof Swal !== 'undefined') {
                e.preventDefault();
                Swal.fire({
                    title: 'تأكيد حفظ البيانات',
                    text: 'هل أنت تأكد من صحة كافة البيانات المدخلة ورغبتك بالتحفظ؟',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: 'نعم، حفظ وتسجيل',
                    cancelButtonText: 'مراجعة مرة أخرى',
                    confirmButtonColor: '#2563eb',
                    cancelButtonColor: '#64748b'
                }).then((result) => {
                    if (result.isConfirmed) {
                        Swal.fire({
                            title: 'جاري الحفظ والتسجيل...',
                            text: 'يرجى الانتظار لحين معالجة البيانات',
                            allowOutsideClick: false,
                            didOpen: () => {
                                Swal.showLoading();
                            }
                        });
                        form.submit();
                    }
                });
            }
        });

        // -------------------------------------------------------------
        // 9. Toast Notification Helper
        // -------------------------------------------------------------
        function showToast(message, type = 'info') {
            if (typeof Swal !== 'undefined' && Swal.mixin) {
                const Toast = Swal.mixin({
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 2000,
                    timerProgressBar: true
                });
                Toast.fire({
                    icon: type,
                    title: message
                });
            }
        }

        // Restore draft on load
        restoreDraft();
    }
})();
