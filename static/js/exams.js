/* ==========================================================================
   ENTERPRISE SAAS EXAMS MODULE CONTROLLER (static/js/exams.js)
   ========================================================================== */

let examsState = {
    selectedIds: new Set()
};

document.addEventListener('turbo:load', function() {
    initExamsModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initExamsModule();
});

function initExamsModule() {
    const panelEl = document.getElementById('examsGridPanel');
    if (!panelEl || panelEl.dataset.initialized === 'true') return;
    panelEl.dataset.initialized = 'true';

    // Register global button handlers
    window.loadExamsData = loadExamsData;
    window.exportExamsExcel = exportExamsExcel;
    window.toggleSelectAllExams = toggleSelectAllExams;
    window.toggleExamSelection = toggleExamSelection;
    window.clearExamsBulkSelections = clearExamsBulkSelections;
    window.openExamsAnalyticsModal = openExamsAnalyticsModal;
    window.printExamsAnalytics = printExamsAnalytics;
    window.viewExamProfile = viewExamProfile;
    window.printExamProfile = printExamProfile;
    window.goToExamWzStep = goToExamWzStep;
    window.nextExamWzStep = nextExamWzStep;
    window.prevExamWzStep = prevExamWzStep;
    window.updateExamWzSummary = updateExamWzSummary;

    setupExamsEventListeners();

    // Check URL parameter for ?exam_id=XX or ?schedule_id=XX
    const urlParams = new URLSearchParams(window.location.search);
    const examId = urlParams.get('exam_id') || urlParams.get('schedule_id');
    if (examId) {
        setTimeout(() => viewExamProfile(examId, 'اختبار مجدول', 'مادة أكاديمية', 'الصف المستهدف', '2026-08-03', '08:00 ص', 'مجدول'), 200);
    }
}

function setupExamsEventListeners() {
    const filterSearch = document.getElementById('filterSearch');
    const filterSubject = document.getElementById('filterSubject');
    const filterClass = document.getElementById('filterClass');
    const filterExamType = document.getElementById('filterExamType');
    const filterStatus = document.getElementById('filterStatus');
    const resetBtn = document.getElementById('resetFiltersBtn');

    if (filterSearch) filterSearch.addEventListener('input', applyExamsFilters);
    if (filterSubject) filterSubject.addEventListener('change', applyExamsFilters);
    if (filterClass) filterClass.addEventListener('change', applyExamsFilters);
    if (filterExamType) filterExamType.addEventListener('change', applyExamsFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyExamsFilters);

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (filterSearch) filterSearch.value = '';
            if (filterSubject) filterSubject.value = '';
            if (filterClass) filterClass.value = '';
            if (filterExamType) filterExamType.value = '';
            if (filterStatus) filterStatus.value = '';
            applyExamsFilters();
        });
    }
}

function applyExamsFilters() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const subVal = document.getElementById('filterSubject')?.value || '';
    const classVal = document.getElementById('filterClass')?.value || '';
    const typeVal = document.getElementById('filterExamType')?.value || '';
    const statusVal = document.getElementById('filterStatus')?.value || '';

    const rows = document.querySelectorAll('#examsTableBody tr.exam-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const subId = row.dataset.subId || '';
        const classId = row.dataset.classId || '';
        const type = row.dataset.type || '';
        const status = row.dataset.status || '';

        let match = true;

        if (searchVal && !text.includes(searchVal)) match = false;
        if (subVal && subId !== subVal) match = false;
        if (classVal && classId !== classVal) match = false;
        if (typeVal && !type.includes(typeVal)) match = false;
        if (statusVal && !status.includes(statusVal)) match = false;

        if (match) {
            row.classList.remove('d-none');
            visibleCount++;
        } else {
            row.classList.add('d-none');
        }
    });

    const elTotal = document.getElementById('kpiTotalExams');
    if (elTotal) elTotal.textContent = visibleCount;
}

function loadExamsData() {
    window.location.reload();
}

function toggleSelectAllExams(masterCheckbox) {
    examsState.selectedIds.clear();
    const rows = document.querySelectorAll('#examsTableBody tr.exam-row:not(.d-none)');

    rows.forEach(row => {
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.checked = masterCheckbox.checked;
            if (masterCheckbox.checked) {
                examsState.selectedIds.add(row);
            }
        }
    });

    updateExamsBulkBar();
}

function toggleExamSelection(id, event) {
    if (event) event.stopPropagation();
    const cb = event.target;

    if (cb.checked) {
        examsState.selectedIds.add(id);
    } else {
        examsState.selectedIds.delete(id);
    }

    updateExamsBulkBar();
}

function clearExamsBulkSelections() {
    examsState.selectedIds.clear();
    const master = document.getElementById('selectAllExams');
    if (master) master.checked = false;

    const checkboxes = document.querySelectorAll('#examsTableBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    updateExamsBulkBar();
}

function updateExamsBulkBar() {
    const bulkBar = document.getElementById('examsBulkBar');
    const countBadge = document.getElementById('bulkSelectedExamsCount');
    const count = examsState.selectedIds.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (countBadge) countBadge.textContent = `${count} محدد`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function exportExamsExcel() {
    window.location.href = '/reports/excel?type=exams';
}

function showToast(message, icon) {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        Toast.fire({ icon: icon, title: message });
    }
}

/* ==========================================================================
   EXAM PROFILE MODAL CONTROLLER (10 SECTIONS)
   ========================================================================== */

let examPerfChartInstance = null;

function viewExamProfile(id, name, subName, className, dateStr, timeStr, status, event) {
    if (event) event.stopPropagation();

    const modalEl = document.getElementById('viewExamProfileModal');
    if (!modalEl) return;

    // Header Badges & Titles
    const headerBadge = document.getElementById('exp-header-badge');
    const codeBadge = document.getElementById('exp-code-badge');
    const statusBadge = document.getElementById('exp-status-badge');
    const heroTitle = document.getElementById('exp-hero-title');
    const heroSubtitle = document.getElementById('exp-hero-subtitle');

    const codeStr = `EXAM-${id}`;
    if (headerBadge) headerBadge.textContent = codeStr;
    if (codeBadge) codeBadge.textContent = codeStr;
    if (heroTitle) heroTitle.textContent = name || 'اختبار أكاديمي';
    if (heroSubtitle) heroSubtitle.textContent = `المادة: ${subName || 'مادة عامة'} | الصف: ${className || 'الصف المستهدف'} | التاريخ: ${dateStr || '—'}`;

    if (statusBadge) {
        statusBadge.textContent = status || 'مجدول';
        if (status === 'منتهي' || status === 'مكتمل') {
            statusBadge.className = 'badge bg-primary rounded-pill px-3 py-1 font-monospace';
        } else {
            statusBadge.className = 'badge bg-success rounded-pill px-3 py-1 font-monospace';
        }
    }

    // Basic Info
    const infoType = document.getElementById('exp-info-type');
    const infoDatetime = document.getElementById('exp-info-datetime');
    const infoStatus = document.getElementById('exp-info-status');
    const linkedClass = document.getElementById('exp-linked-class');
    const assignedTeacher = document.getElementById('exp-assigned-teacher');

    if (infoType) infoType.textContent = name || 'اختبار تقويمي';
    if (infoDatetime) infoDatetime.textContent = `${dateStr || '—'} ${timeStr || ''}`;
    if (infoStatus) infoStatus.textContent = status || 'مجدول ومفعل';
    if (linkedClass) linkedClass.textContent = className || 'جميع الشعب المستهدفة';
    if (assignedTeacher) assignedTeacher.textContent = `أ. المعلم المشرف على مادة ${subName || ''}`;

    // Render Analytics Chart
    initExamPerfChart();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initExamPerfChart() {
    const ctx = document.getElementById('examPerfChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (examPerfChartInstance) {
        examPerfChartInstance.destroy();
    }

    examPerfChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['ممتاز (90-100)', 'جيد جداً (80-89)', 'جيد (70-79)', 'مقبول (60-69)', 'راسب (<60)'],
            datasets: [{
                data: [18, 10, 5, 2, 0],
                backgroundColor: ['#22c55e', '#3b82f6', '#06b6d4', '#eab308', '#ef4444'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function printExamProfile() {
    window.print();
}

/* ==========================================================================
   EXAMS ANALYTICS & REPORTS CONTROLLER (POWER BI & CANVAS INSIGHTS)
   ========================================================================== */

let examsSubjectChartInstance = null;
let examsGradeBreakdownChartInstance = null;

function openExamsAnalyticsModal() {
    const modalEl = document.getElementById('examsAnalyticsModal');
    if (!modalEl) return;

    initExamsAnalyticsCharts();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initExamsAnalyticsCharts() {
    // 1. Subject Comparison Bar Chart
    const ctx1 = document.getElementById('anExamsSubjectChart');
    if (ctx1 && typeof Chart !== 'undefined') {
        if (examsSubjectChartInstance) examsSubjectChartInstance.destroy();
        examsSubjectChartInstance = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: ['اللغة العربية', 'الرياضيات', 'العلوم العامة', 'اللغة الإنجليزية', 'الدراسات'],
                datasets: [{
                    label: 'متوسط الدرجات %',
                    data: [98.5, 92.0, 96.4, 88.0, 94.5],
                    backgroundColor: ['#22c55e', '#3b82f6', '#06b6d4', '#eab308', '#8b5cf6'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }

    // 2. Grade Breakdown Doughnut Chart
    const ctx2 = document.getElementById('anExamsGradeBreakdownChart');
    if (ctx2 && typeof Chart !== 'undefined') {
        if (examsGradeBreakdownChartInstance) examsGradeBreakdownChartInstance.destroy();
        examsGradeBreakdownChartInstance = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['ممتاز (A)', 'جيد جداً (B)', 'جيد (C)', 'مقبول (D)', 'راسب (F)'],
                datasets: [{
                    data: [65, 30, 15, 8, 2],
                    backgroundColor: ['#22c55e', '#3b82f6', '#06b6d4', '#eab308', '#ef4444'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

function printExamsAnalytics() {
    window.print();
}

/* ==========================================================================
   ADD EXAM 4-STEP ENTERPRISE WIZARD CONTROLLER
   ========================================================================== */

let currentExamWzStep = 1;

function goToExamWzStep(step) {
    if (step < 1 || step > 4) return;

    if (step > currentExamWzStep) {
        if (!validateExamWzStep(currentExamWzStep)) return;
    }

    currentExamWzStep = step;
    updateExamWzStepUI();
}

function nextExamWzStep() {
    if (currentExamWzStep === 4) {
        const form = document.getElementById('addExamWizardForm');
        if (form) form.submit();
        return;
    }

    if (!validateExamWzStep(currentExamWzStep)) return;

    currentExamWzStep++;
    updateExamWzStepUI();
}

function prevExamWzStep() {
    if (currentExamWzStep > 1) {
        currentExamWzStep--;
        updateExamWzStepUI();
    }
}

function validateExamWzStep(step) {
    if (step === 1) {
        const sub = document.getElementById('ex-wz-sub');
        const cls = document.getElementById('ex-wz-class');
        if (!sub || !sub.value) {
            showToast('الرجاء اختيار المادة الدراسية قبل الانتقال للخطوة التالية', 'warning');
            if (sub) sub.focus();
            return false;
        }
        if (!cls || !cls.value) {
            showToast('الرجاء اختيار الصف الدراسي قبل الانتقال للخطوة التالية', 'warning');
            if (cls) cls.focus();
            return false;
        }
    } else if (step === 2) {
        const type = document.getElementById('ex-wz-type');
        if (!type || !type.value) {
            showToast('الرجاء تحديد نوع الاختبار قبل الانتقال للخطوة التالية', 'warning');
            if (type) type.focus();
            return false;
        }
    } else if (step === 3) {
        const dateEl = document.getElementById('ex-wz-date');
        const timeEl = document.getElementById('ex-wz-time');
        if (!dateEl || !dateEl.value) {
            showToast('الرجاء اختيار تاريخ إجراء الاختبار', 'warning');
            if (dateEl) dateEl.focus();
            return false;
        }
        if (!timeEl || !timeEl.value) {
            showToast('الرجاء اختيار توقيت بداية الاختبار', 'warning');
            if (timeEl) timeEl.focus();
            return false;
        }
    }
    return true;
}

function updateExamWzStepUI() {
    for (let i = 1; i <= 4; i++) {
        const pane = document.getElementById(`ex-wz-step-${i}`);
        const btn = document.getElementById(`ex-wz-step-btn-${i}`);

        if (pane) {
            if (i === currentExamWzStep) pane.classList.remove('d-none');
            else pane.classList.add('d-none');
        }

        if (btn) {
            if (i === currentExamWzStep) {
                btn.className = 'exam-wz-step-item text-center active';
            } else if (i < currentExamWzStep) {
                btn.className = 'exam-wz-step-item text-center completed';
            } else {
                btn.className = 'exam-wz-step-item text-center';
            }
        }
    }

    const btnPrev = document.getElementById('ex-wz-btn-prev');
    const btnNext = document.getElementById('ex-wz-btn-next');

    if (btnPrev) btnPrev.disabled = (currentExamWzStep === 1);

    if (btnNext) {
        if (currentExamWzStep === 4) {
            btnNext.innerHTML = '<i class="fa-solid fa-check-double me-1"></i> حفظ وتوثيق الجدول النهائي';
            btnNext.className = 'btn btn-success rounded-pill px-5 fw-bold shadow-sm';
        } else {
            btnNext.innerHTML = 'التالي <i class="fa-solid fa-arrow-left ms-1"></i>';
            btnNext.className = 'btn btn-primary rounded-pill px-5 fw-bold shadow-sm';
        }
    }

    updateExamWzSummary();
}

function updateExamWzSummary() {
    const sub = document.getElementById('ex-wz-sub');
    const cls = document.getElementById('ex-wz-class');
    const type = document.getElementById('ex-wz-type');
    const status = document.getElementById('ex-wz-status');
    const dateEl = document.getElementById('ex-wz-date');

    const sumSub = document.getElementById('ex-sum-sub');
    const sumClass = document.getElementById('ex-sum-class');
    const sumType = document.getElementById('ex-sum-type');
    const sumDate = document.getElementById('ex-sum-date');

    if (sumSub && sub) {
        const txt = sub.options[sub.selectedIndex]?.text || 'لم تتحدد بعد';
        sumSub.textContent = txt;
    }
    if (sumClass && cls) {
        const txt = cls.options[cls.selectedIndex]?.text || 'لم يتحدد بعد';
        sumClass.textContent = txt;
    }
    if (sumType && type) {
        const typeVal = type.value || 'نصفي';
        const statusVal = status?.value || 'مجدول';
        sumType.textContent = `${typeVal} (${statusVal})`;
    }
    if (sumDate && dateEl) {
        sumDate.textContent = dateEl.value || new Date().toISOString().split('T')[0];
    }
}
