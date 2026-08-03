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

    setupHomeworkEventListeners();
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
    window.location.href = '/reports/excel?type=homework';
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
