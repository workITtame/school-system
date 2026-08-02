/**
 * Teacher Form UX Improvements Suite - Enterprise SaaS Edition
 * Handles: Auto Save Draft, Keyboard Navigation, Inline Validation,
 * Phone Formatting, Auto Scroll to Error, SweetAlert2 confirm & loading.
 */

(function () {
    'use strict';

    document.addEventListener("DOMContentLoaded", initTeacherFormUX);
    document.addEventListener("turbo:load", initTeacherFormUX);

    function initTeacherFormUX() {
        const teacherForm = document.getElementById('teacherForm');
        if (!teacherForm) return;

        // 1. Phone Formatting
        const phoneInput = document.getElementById('tPhone') || document.getElementById('inputPhone');
        if (phoneInput) {
            phoneInput.addEventListener('input', function (e) {
                let x = e.target.value.replace(/\D/g, '').match(/(\d{0,4})(\d{0,3})(\d{0,3})/);
                if (x) {
                    e.target.value = !x[2] ? x[1] : x[1] + ' ' + x[2] + (x[3] ? ' ' + x[3] : '');
                }
            });
        }

        // 2. Draft Auto Save to localStorage
        const DRAFT_KEY = 'teacher_form_draft';
        let autoSaveTimer;

        function saveDraft() {
            const formData = new FormData(teacherForm);
            const data = {};
            formData.forEach((value, key) => {
                if (key !== 'photo' && key !== 'tImage' && key !== 'Password') {
                    data[key] = value;
                }
            });
            localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
        }

        teacherForm.addEventListener('input', function () {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(saveDraft, 2000);
        });

        // 3. Unsaved Changes Warning
        let isSubmitted = false;
        teacherForm.addEventListener('submit', function () {
            isSubmitted = true;
            localStorage.removeItem(DRAFT_KEY);
        });

        window.addEventListener('beforeunload', function (e) {
            const hasData = (phoneInput && phoneInput.value.length > 0) || (document.getElementById('tName') && document.getElementById('tName').value.length > 0);
            if (!isSubmitted && hasData) {
                e.preventDefault();
                e.returnValue = '';
            }
        });

        // 4. Keyboard Navigation (Enter to Focus Next / Next Step)
        teacherForm.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.type !== 'submit') {
                e.preventDefault();
                const inputs = Array.from(teacherForm.querySelectorAll('input:not([type="hidden"]), select'));
                const currentIndex = inputs.indexOf(e.target);
                if (currentIndex >= 0 && currentIndex < inputs.length - 1) {
                    inputs[currentIndex + 1].focus();
                } else {
                    const nextBtn = document.getElementById('nextBtn');
                    if (nextBtn && nextBtn.style.display !== 'none') {
                        nextBtn.click();
                    }
                }
            }
        });

        // 5. Auto Scroll to First Error Helper
        window.scrollToFirstError = function (container) {
            const firstError = (container || teacherForm).querySelector('.is-invalid, :invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        };

        // 6. SweetAlert2 Submit Confirmation & Loading Overlay
        teacherForm.addEventListener('submit', function (e) {
            if (!teacherForm.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                teacherForm.classList.add('was-validated');
                window.scrollToFirstError();
                return;
            }

            if (typeof Swal !== 'undefined' && !isSubmitted) {
                e.preventDefault();
                Swal.fire({
                    title: 'تأكيد حفظ بيانات المعلم',
                    text: 'هل أنت متأكد من صحة كافة البيانات والأوراق المرفقة؟',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: '<i class="fa-solid fa-check me-1"></i> نعم، تأكيد الحفظ',
                    cancelButtonText: 'إلغاء وتعديل',
                    customClass: {
                        confirmButton: 'btn btn-primary rounded-pill px-4 fw-bold',
                        cancelButton: 'btn btn-secondary rounded-pill px-4 fw-bold me-2'
                    },
                    buttonsStyling: false
                }).then((result) => {
                    if (result.isConfirmed) {
                        isSubmitted = true;
                        Swal.fire({
                            title: 'جاري حفظ بيانات المعلم...',
                            text: 'يرجى الانتظار لحين معالجة وتخزين البيانات بالمستودع',
                            allowOutsideClick: false,
                            didOpen: () => {
                                Swal.showLoading();
                            }
                        });
                        teacherForm.submit();
                    }
                });
            }
        });
    }
})();
