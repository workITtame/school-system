/* ==========================================================================
   ENTERPRISE SAAS HOMEWORK MODULE CONTROLLER (static/js/homework.js)
   ========================================================================== */

let homeworkState = {
    selectedIds: new Set()
};

document.addEventListener('turbo:load', function() {
    initHomeworkModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initHomeworkModule();
});

function initHomeworkModule() {
    const panelEl = document.getElementById('homeworkGridPanel');
    if (!panelEl || panelEl.dataset.initialized === 'true') return;
    panelEl.dataset.initialized = 'true';

    // Register global button handlers
    window.loadHomeworkData = loadHomeworkData;
    window.exportHomeworkExcel = exportHomeworkExcel;
    window.toggleSelectAllHomework = toggleSelectAllHomework;
    window.toggleHomeworkSelection = toggleHomeworkSelection;
    window.clearHomeworkBulkSelections = clearHomeworkBulkSelections;
    window.goToHomeworkWzStep = goToHomeworkWzStep;
    window.nextHomeworkWzStep = nextHomeworkWzStep;
    window.prevHomeworkWzStep = prevHomeworkWzStep;
    window.updateHomeworkWzSummary = updateHomeworkWzSummary;
    window.viewHomeworkProfile = viewHomeworkProfile;
    window.printHomeworkProfile = printHomeworkProfile;
    window.openHomeworkAnalyticsModal = openHomeworkAnalyticsModal;
    window.printHomeworkAnalytics = printHomeworkAnalytics;

    setupHomeworkEventListeners();

    // Check URL parameter for ?homework_id=XX or ?hw_id=XX
    const urlParams = new URLSearchParams(window.location.search);
    const hwId = urlParams.get('homework_id') || urlParams.get('hw_id');
    if (hwId) {
        viewHomeworkProfile(hwId, `واجب أكاديمي #${hwId}`, 'مادة دراسية', 'الصف المستهدف', 'جميع الشعب', '', 'مكتمل', '');
    }
}

function setupHomeworkEventListeners() {
    const filterSearch = document.getElementById('filterSearch');
    const filterSubject = document.getElementById('filterSubject');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterStatus = document.getElementById('filterStatus');
    const resetBtn = document.getElementById('resetFiltersBtn');

    if (filterSearch) filterSearch.addEventListener('input', applyHomeworkFilters);
    if (filterSubject) filterSubject.addEventListener('change', applyHomeworkFilters);
    if (filterClass) filterClass.addEventListener('change', applyHomeworkFilters);
    if (filterSection) filterSection.addEventListener('change', applyHomeworkFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyHomeworkFilters);

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (filterSearch) filterSearch.value = '';
            if (filterSubject) filterSubject.value = '';
            if (filterClass) filterClass.value = '';
            if (filterSection) filterSection.value = '';
            if (filterStatus) filterStatus.value = '';
            applyHomeworkFilters();
        });
    }
}

function applyHomeworkFilters() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const subVal = document.getElementById('filterSubject')?.value || '';
    const classVal = document.getElementById('filterClass')?.value || '';
    const sectionVal = document.getElementById('filterSection')?.value || '';
    const statusVal = document.getElementById('filterStatus')?.value || '';

    const rows = document.querySelectorAll('#homeworkTableBody tr.homework-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const subId = row.dataset.subId || '';
        const classId = row.dataset.classId || '';
        const sectionId = row.dataset.sectionId || '';
        const status = row.dataset.status || '';

        let match = true;

        if (searchVal && !text.includes(searchVal)) match = false;
        if (subVal && subId !== subVal) match = false;
        if (classVal && classId !== classVal) match = false;
        if (sectionVal && sectionId !== sectionVal) match = false;
        if (statusVal && !status.includes(statusVal)) match = false;

        if (match) {
            row.classList.remove('d-none');
            visibleCount++;
        } else {
            row.classList.add('d-none');
        }
    });

    const elTotal = document.getElementById('kpiTotalHomework');
    if (elTotal) elTotal.textContent = visibleCount;
}

function loadHomeworkData() {
    window.location.reload();
}

function toggleSelectAllHomework(masterCheckbox) {
    homeworkState.selectedIds.clear();
    const rows = document.querySelectorAll('#homeworkTableBody tr.homework-row:not(.d-none)');

    rows.forEach(row => {
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.checked = masterCheckbox.checked;
            if (masterCheckbox.checked) {
                homeworkState.selectedIds.add(row);
            }
        }
    });

    updateHomeworkBulkBar();
}

function toggleHomeworkSelection(id, event) {
    if (event) event.stopPropagation();
    const cb = event.target;

    if (cb.checked) {
        homeworkState.selectedIds.add(id);
    } else {
        homeworkState.selectedIds.delete(id);
    }

    updateHomeworkBulkBar();
}

function clearHomeworkBulkSelections() {
    homeworkState.selectedIds.clear();
    const master = document.getElementById('selectAllHomework');
    if (master) master.checked = false;

    const checkboxes = document.querySelectorAll('#homeworkTableBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    updateHomeworkBulkBar();
}

function updateHomeworkBulkBar() {
    const bulkBar = document.getElementById('homeworkBulkBar');
    const countBadge = document.getElementById('bulkSelectedHomeworkCount');
    const count = homeworkState.selectedIds.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (countBadge) countBadge.textContent = `${count} محدد`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function exportHomeworkExcel() {
    const rows = document.querySelectorAll('#homeworkTableBody tr.homework-row');
    if (!rows || rows.length === 0) {
        showToast('لا توجد بيانات واجبات لتصديرها', 'warning');
        return;
    }

    let excelHTML = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="content-type" content="text/plain; charset=UTF-8"/>
        <style>
            table { border-collapse: collapse; width: 100%; direction: rtl; }
            th { background-color: #1e40af; color: #ffffff; font-weight: bold; text-align: center; padding: 10px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; }
            td { text-align: center; padding: 8px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; font-size: 13px; }
            tr:nth-child(even) { background-color: #f8fafc; }
            .title-cell { text-align: right; font-weight: bold; }
        </style>
    </head>
    <body dir="rtl">
        <h2 style="text-align: center; font-family: Cairo, Arial; color: #1e40af;">تقرير إدارة الواجبات والمهام الأكاديمية</h2>
        <p style="text-align: center; font-family: Cairo, Arial; color: #64748b;">تاريخ التصدير: ${new Date().toLocaleDateString('ar-EG')}</p>
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;">#</th>
                    <th>عنوان الواجب</th>
                    <th>الملاحظات والتفاصيل</th>
                    <th>المادة الدراسية</th>
                    <th>الصف الدراسي</th>
                    <th>الشعبة</th>
                    <th>تاريخ التسليم</th>
                    <th>الحالة</th>
                </tr>
            </thead>
            <tbody>`;

    let count = 0;
    rows.forEach((row) => {
        if (row.classList.contains('d-none')) return;
        count++;

        const titleEl = row.querySelector('strong.text-dark');
        const descEl  = row.querySelector('small.text-muted');
        const subEl   = row.querySelector('td:nth-child(4) .badge');
        const classTd = row.querySelector('td:nth-child(5)');
        const dueTd   = row.querySelector('td:nth-child(6)');
        const statusEl= row.querySelector('td:nth-child(7) .badge');

        const title = titleEl ? titleEl.textContent.trim() : '';
        const desc  = descEl  ? descEl.textContent.trim()  : '';
        const sub   = subEl   ? subEl.textContent.trim()   : '';

        let className = '';
        let secName   = '';
        if (classTd) {
            const secBadge = classTd.querySelector('.badge');
            secName = secBadge ? secBadge.textContent.trim() : 'جميع الشعب';
            className = classTd.childNodes[0] ? classTd.childNodes[0].textContent.trim() : classTd.textContent.trim();
            className = className.replace(secName, '').trim();
        }

        const due = dueTd ? dueTd.textContent.trim() : '';
        const status = statusEl ? statusEl.textContent.trim() : '';

        excelHTML += `
            <tr>
                <td>${count}</td>
                <td class="title-cell">${title}</td>
                <td style="text-align: right;">${desc}</td>
                <td>${sub}</td>
                <td>${className}</td>
                <td>${secName}</td>
                <td>${due}</td>
                <td>${status}</td>
            </tr>`;
    });

    excelHTML += `
            </tbody>
        </table>
    </body>
    </html>`;

    const blob = new Blob(['\ufeff' + excelHTML], { type: 'application/vnd.ms-excel;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `جدول_الواجبات_الدراسية_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('تم تصدير ملف Excel للواجبات بنجاح', 'success');
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
   ADD HOMEWORK 5-STEP ENTERPRISE WIZARD CONTROLLER
   ========================================================================== */

let currentHomeworkWzStep = 1;

function goToHomeworkWzStep(step) {
    if (step < 1 || step > 5) return;

    if (step > currentHomeworkWzStep) {
        if (!validateHomeworkWzStep(currentHomeworkWzStep)) return;
    }

    currentHomeworkWzStep = step;
    updateHomeworkWzStepUI();
}

function nextHomeworkWzStep() {
    if (currentHomeworkWzStep === 5) {
        const form = document.getElementById('addHomeworkWizardForm');
        if (form) form.submit();
        return;
    }

    if (!validateHomeworkWzStep(currentHomeworkWzStep)) return;

    currentHomeworkWzStep++;
    updateHomeworkWzStepUI();
}

function prevHomeworkWzStep() {
    if (currentHomeworkWzStep > 1) {
        currentHomeworkWzStep--;
        updateHomeworkWzStepUI();
    }
}

function validateHomeworkWzStep(step) {
    if (step === 1) {
        const title = document.getElementById('hw-wz-title');
        const sub = document.getElementById('hw-wz-sub');
        const cls = document.getElementById('hw-wz-class');

        if (!title || !title.value.trim()) {
            showToast('الرجاء كتابة عنوان الواجب قبل الانتقال للخطوة التالية', 'warning');
            if (title) title.focus();
            return false;
        }
        if (!sub || !sub.value) {
            showToast('الرجاء اختيار المادة الدراسية', 'warning');
            if (sub) sub.focus();
            return false;
        }
        if (!cls || !cls.value) {
            showToast('الرجاء اختيار الصف الدراسي', 'warning');
            if (cls) cls.focus();
            return false;
        }
    } else if (step === 3) {
        const dateEl = document.getElementById('hw-wz-date');
        if (!dateEl || !dateEl.value) {
            showToast('الرجاء تحديد تاريخ التسليم النهائي للواجب', 'warning');
            if (dateEl) dateEl.focus();
            return false;
        }
    }
    return true;
}

function updateHomeworkWzStepUI() {
    for (let i = 1; i <= 5; i++) {
        const pane = document.getElementById(`hw-wz-step-${i}`);
        const btn = document.getElementById(`hw-wz-step-btn-${i}`);

        if (pane) {
            if (i === currentHomeworkWzStep) pane.classList.remove('d-none');
            else pane.classList.add('d-none');
        }

        if (btn) {
            if (i === currentHomeworkWzStep) {
                btn.className = 'hw-wz-step-item text-center active';
            } else if (i < currentHomeworkWzStep) {
                btn.className = 'hw-wz-step-item text-center completed';
            } else {
                btn.className = 'hw-wz-step-item text-center';
            }
        }
    }

    const btnPrev = document.getElementById('hw-wz-btn-prev');
    const btnNext = document.getElementById('hw-wz-btn-next');

    if (btnPrev) btnPrev.disabled = (currentHomeworkWzStep === 1);

    if (btnNext) {
        if (currentHomeworkWzStep === 5) {
            btnNext.innerHTML = '<i class="fa-solid fa-check-double me-1"></i> حفظ وتوثيق الواجب النهائي';
            btnNext.className = 'btn btn-success rounded-pill px-5 fw-bold shadow-sm';
        } else {
            btnNext.innerHTML = 'التالي <i class="fa-solid fa-arrow-left ms-1"></i>';
            btnNext.className = 'btn btn-primary rounded-pill px-5 fw-bold shadow-sm';
        }
    }

    updateHomeworkWzSummary();
}

function updateHomeworkWzSummary() {
    const title = document.getElementById('hw-wz-title');
    const sub = document.getElementById('hw-wz-sub');
    const cls = document.getElementById('hw-wz-class');
    const dateEl = document.getElementById('hw-wz-date');
    const status = document.getElementById('hw-wz-status');

    const sumTitle = document.getElementById('hw-sum-title');
    const sumSub = document.getElementById('hw-sum-sub');
    const sumDate = document.getElementById('hw-sum-date');
    const sumStatus = document.getElementById('hw-sum-status');

    if (sumTitle && title) {
        sumTitle.textContent = title.value || 'لم يتحدد بعد';
    }
    if (sumSub && sub && cls) {
        const subTxt = sub.options[sub.selectedIndex]?.text || 'المادة';
        const clsTxt = cls.options[cls.selectedIndex]?.text || 'الصف';
        sumSub.textContent = `${subTxt} - ${clsTxt}`;
    }
    if (sumDate && dateEl) {
        sumDate.textContent = dateEl.value || new Date().toISOString().split('T')[0];
    }
    if (sumStatus && status) {
        sumStatus.textContent = status.value || 'معلق';
    }
}

/* ==========================================================================
   HOMEWORK PROFILE MODAL CONTROLLER (10-SECTION ENTERPRISE PROFILE)
   ========================================================================== */

let hwpSubmissionChartInstance = null;

function viewHomeworkProfile(id, title, subjectName, className, sectionName, dueDate, status, description) {
    const modalEl = document.getElementById('viewHomeworkProfileModal');
    if (!modalEl) return;

    // Header & Badges
    const headerBadge  = document.getElementById('hwp-header-badge');
    const headerTitle  = document.getElementById('hwp-header-title');
    const codeBadge    = document.getElementById('hwp-code-badge');
    const statusBadge  = document.getElementById('hwp-status-badge');
    const heroTitle    = document.getElementById('hwp-hero-title');
    const heroSubtitle = document.getElementById('hwp-hero-subtitle');

    if (headerBadge)  headerBadge.textContent  = `HW-${id}`;
    if (headerTitle)  headerTitle.textContent  = `الملف الشخصي للواجب | ${title || 'واجب دراسي'}`;
    if (codeBadge)    codeBadge.textContent    = `HW-${id}`;
    if (statusBadge)  statusBadge.textContent  = status || 'مكتمل';
    if (heroTitle)    heroTitle.textContent    = title || 'عنوان الواجب الدراسـي';
    if (heroSubtitle) heroSubtitle.textContent = `${subjectName} | ${className} (${sectionName}) | التسليم: ${dueDate || '—'}`;

    // Status badge color
    if (statusBadge) {
        statusBadge.className = 'badge rounded-pill px-3 py-1 font-monospace';
        if (status === 'مكتمل')   statusBadge.classList.add('bg-success');
        else if (status === 'معلق') statusBadge.classList.add('bg-warning', 'text-dark');
        else                          statusBadge.classList.add('bg-danger');
    }

    // Basic Info Grid
    const infoSubject = document.getElementById('hwp-info-subject');
    const infoClass   = document.getElementById('hwp-info-class');
    const infoDueDate = document.getElementById('hwp-info-duedate');
    const infoStatus  = document.getElementById('hwp-info-status');
    const infoDesc    = document.getElementById('hwp-info-desc');

    if (infoSubject) infoSubject.textContent = subjectName || 'مادة عامة';
    if (infoClass)   infoClass.textContent   = `${className} (${sectionName})`;
    if (infoDueDate) infoDueDate.textContent  = dueDate || 'غير محدد';
    if (infoStatus)  infoStatus.textContent  = status || 'مكتمل';
    if (infoDesc)    infoDesc.textContent    = description || 'لا توجد ملاحظات أو تعليمات إضافية لهذا التكليف الدراسي.';

    // Assigned Class Card
    const assignCname = document.getElementById('hwp-assign-cname');
    const assignSec   = document.getElementById('hwp-assign-sec');
    if (assignCname) assignCname.textContent = className || 'الصف المستهدف';
    if (assignSec)   assignSec.textContent   = `الشعبة (${sectionName})`;

    // Timeline — real DB fields: show due date only (no submission table exists)
    const timelineCreated = document.getElementById('hwp-timeline-created');
    const timelineDue     = document.getElementById('hwp-timeline-due');
    if (timelineCreated) timelineCreated.textContent = 'تاريخ الإنشاء غير متاح هنا';
    if (timelineDue)     timelineDue.textContent     = dueDate || 'غير محدد';

    // Profile status KPI
    const kpiStatusText = document.getElementById('hwp-kpi-status-text');
    if (kpiStatusText) kpiStatusText.textContent = status || '—';

    // Initialize Doughnut Chart
    initHomeworkProfileChart();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initHomeworkProfileChart() {
    // Profile chart is a simple status overview using page-level Jinja data (not hardcoded)
    // The actual chart is decorative — status totals come from the page KPI counts
    const ctx = document.getElementById('hwpSubmissionChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (hwpSubmissionChartInstance) {
        hwpSubmissionChartInstance.destroy();
    }

    // Read real counts from the page DOM (populated by Jinja2, not hardcoded)
    const completedEl = document.querySelector('[id="kpiCompletedHomework"]');
    const pendingEl   = document.querySelector('[id="kpiPendingHomework"]');
    const lateEl      = document.querySelector('[id="kpiLateHomework"]');

    const completed = parseInt(completedEl?.textContent || '0', 10) || 0;
    const pending   = parseInt(pendingEl?.textContent   || '0', 10) || 0;
    const late      = parseInt(lateEl?.textContent      || '0', 10) || 0;

    hwpSubmissionChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['واجبات مكتملة', 'واجبات معلقة', 'واجبات متأخرة'],
            datasets: [{
                data: [completed, pending, late],
                backgroundColor: ['#22c55e', '#eab308', '#ef4444'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
        }
    });
}

function printHomeworkProfile() {
    window.print();
}

/*
 * initHomeworkModalCharts — initializes charts in the analytics modal
 * using data-attributes populated by Jinja2 from real DB data.
 * No hardcoded arrays.
 */
let homeworkModalSubjectChartInstance = null;
let homeworkModalStatusChartInstance  = null;

function initHomeworkModalCharts() {
    // Status chart — reads data-attributes from canvas (set by Jinja2)
    const ctx2 = document.getElementById('anHomeworkStatusChart');
    if (ctx2 && typeof Chart !== 'undefined') {
        if (homeworkModalStatusChartInstance) homeworkModalStatusChartInstance.destroy();

        const completed = parseInt(ctx2.dataset.completed || '0', 10);
        const pending   = parseInt(ctx2.dataset.pending   || '0', 10);
        const late      = parseInt(ctx2.dataset.late      || '0', 10);

        homeworkModalStatusChartInstance = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['واجبات مكتملة', 'واجبات معلقة', 'واجبات متأخرة'],
                datasets: [{
                    data: [completed, pending, late],
                    backgroundColor: ['#22c55e', '#eab308', '#ef4444'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                cutout: '60%',
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
            }
        });
    }
}

/* Keep openHomeworkAnalyticsModal as a redirect for backward compat */
function openHomeworkAnalyticsModal() {
    window.location.href = '/homework/analytics';
}

function printHomeworkAnalytics() {
    window.location.href = '/homework/analytics';
}
