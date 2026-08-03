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

    setupExamsEventListeners();
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
