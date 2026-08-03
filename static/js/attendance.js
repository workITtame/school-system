/* ==========================================================================
   ENTERPRISE SAAS ATTENDANCE MODULE CONTROLLER (static/js/attendance.js)
   ========================================================================== */

let attendanceState = {
    students: [],
    filteredStudents: [],
    selectedSIDs: new Set(),
    chartInstance: null
};

document.addEventListener('turbo:load', function() {
    initAttendanceModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initAttendanceModule();
});

function initAttendanceModule() {
    const panelEl = document.getElementById('attendanceGridPanel');
    if (!panelEl || panelEl.dataset.initialized === 'true') return;
    panelEl.dataset.initialized = 'true';

    // Register global button handlers
    window.loadAttendanceData = loadAttendanceData;
    window.updateAttendance = updateAttendance;
    window.bulkMarkAttendance = bulkMarkAttendance;
    window.exportAttendanceReport = exportAttendanceReport;
    window.toggleSelectAllAttendance = toggleSelectAllAttendance;
    window.toggleStudentSelection = toggleStudentSelection;
    window.clearBulkSelections = clearBulkSelections;
    window.submitQuickMark = submitQuickMark;

    setupAttendanceEventListeners();

    // Auto-select first class & section if available for immediate dashboard population
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');

    if (filterClass && filterClass.options.length > 1) {
        filterClass.selectedIndex = 1;
    }
    if (filterSection && filterSection.options.length > 1) {
        filterSection.selectedIndex = 1;
    }

    loadAttendanceData();
}

function setupAttendanceEventListeners() {
    const filterDate = document.getElementById('filterDate');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterStatus = document.getElementById('filterStatus');
    const filterSearch = document.getElementById('filterSearch');
    const resetBtn = document.getElementById('resetFiltersBtn');

    if (filterDate) filterDate.addEventListener('change', loadAttendanceData);
    if (filterClass) filterClass.addEventListener('change', loadAttendanceData);
    if (filterSection) filterSection.addEventListener('change', loadAttendanceData);
    if (filterStatus) filterStatus.addEventListener('change', applyAttendanceFilters);
    if (filterSearch) filterSearch.addEventListener('input', applyAttendanceFilters);

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (filterSearch) filterSearch.value = '';
            if (filterStatus) filterStatus.value = '';
            applyAttendanceFilters();
        });
    }
}

function loadAttendanceData() {
    const filterDate = document.getElementById('filterDate');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');

    if (!filterClass || !filterSection || !filterDate) return;

    const classId = filterClass.value;
    const sectionId = filterSection.value;
    const dateVal = filterDate.value;

    if (!classId || !sectionId) {
        showEmptyAttendanceState(true, 'الرجاء تحديد الصف والشعبة لعرض كشف الحضور', 'اختر الصف الدراسي والشعبة التابعة له من شريط الفلاتر أعلى الصفحة للجلب والتسجيل.');
        return;
    }

    showAttendanceLoading(true);

    fetch(`/attendance/api/students?class_id=${classId}&section_id=${sectionId}&date=${dateVal}`)
        .then(res => res.json())
        .then(data => {
            showAttendanceLoading(false);
            if (data.success) {
                attendanceState.students = data.data || [];
                applyAttendanceFilters();
            } else {
                showToast(data.message || 'تعذر جلب بيانات الحضور', 'error');
                showEmptyAttendanceState(true);
            }
        })
        .catch(err => {
            showAttendanceLoading(false);
            console.error(err);
            showToast('حدث خطأ في الاتصال بالخادم أثناء جلب بيانات الحضور', 'error');
        });
}

function applyAttendanceFilters() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const statusVal = document.getElementById('filterStatus')?.value || '';

    let list = [...attendanceState.students];

    if (searchVal) {
        list = list.filter(s => 
            (s.SName && s.SName.toLowerCase().includes(searchVal)) ||
            (s.SID && s.SID.toString().includes(searchVal))
        );
    }

    if (statusVal) {
        list = list.filter(s => {
            if (statusVal === 'Present') return s.Status === 'Present' || s.Status === 'حاضر';
            if (statusVal === 'Absent') return s.Status === 'Absent' || s.Status === 'غائب';
            if (statusVal === 'Late') return s.Status === 'Late' || s.Status === 'متأخر';
            if (statusVal === 'غير مسجل') return s.Status === 'غير مسجل';
            return true;
        });
    }

    attendanceState.filteredStudents = list;
    updateAttendanceKPICards();
    renderAttendanceTable();
    initAttendanceChart();
}

function renderAttendanceTable() {
    const tbody = document.getElementById('attendanceTableBody');
    const students = attendanceState.filteredStudents;

    if (!tbody) return;

    if (attendanceState.students.length === 0) {
        showEmptyAttendanceState(true, 'لا يوجد طلاب في هذه الشعبة', 'لم يتم العثور على أي حسابات طلاب نشطة في الصف والشعبة المحددين.');
        return;
    }

    if (students.length === 0) {
        showEmptyAttendanceState(true, 'لا توجد نتائج تطابق خيارات البحث', 'جرب مسح شريط البحث أو تغيير فلتر الحالة للوصول للنتائج المطلوب.');
        return;
    }

    showEmptyAttendanceState(false);

    let html = '';
    students.forEach((s, idx) => {
        const isSelected = attendanceState.selectedSIDs.has(s.SID);
        const statusBadgeClass = getAttendanceStatusBadgeClass(s.Status);
        const timeStr = s.Time ? new Date(s.Time).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' }) : '—';

        html += `
            <tr class="align-middle">
                <td>
                    <input type="checkbox" class="form-check-input rounded-2" ${isSelected ? 'checked' : ''} onclick="toggleStudentSelection(${s.SID}, event)">
                </td>
                <td class="fw-bold text-muted font-monospace">${idx + 1}</td>
                <td class="text-start">
                    <div class="d-flex align-items-center gap-3">
                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(s.SName || 'Student')}&background=2563eb&color=fff" class="rounded-circle border" style="width:38px; height:38px;">
                        <div>
                            <strong class="d-block text-dark font-monospace">${s.SName || 'اسم غير معروف'}</strong>
                            <small class="text-muted extra-small">طالب مقيد بالمؤسسة</small>
                        </div>
                    </div>
                </td>
                <td class="font-monospace fw-bold text-primary">${s.SID}</td>
                <td>
                    <select class="form-select form-select-sm rounded-pill fw-bold border-0 font-monospace text-center mx-auto ${statusBadgeClass}" 
                            style="width: 130px; cursor: pointer;" 
                            onchange="updateAttendance(${s.SID}, this.value)">
                        <option value="Present" ${s.Status === 'Present' || s.Status === 'حاضر' ? 'selected' : ''}>حاضر</option>
                        <option value="Absent" ${s.Status === 'Absent' || s.Status === 'غائب' ? 'selected' : ''}>غائب</option>
                        <option value="Late" ${s.Status === 'Late' || s.Status === 'متأخر' ? 'selected' : ''}>متأخر</option>
                        <option value="غير مسجل" ${s.Status === 'غير مسجل' ? 'selected' : ''}>-- تسجيل --</option>
                    </select>
                </td>
                <td class="font-monospace text-muted small">${timeStr}</td>
                <td class="font-monospace text-muted small">${s.Note || '—'}</td>
                <td>
                    <a href="/students/view/${s.SID}" data-turbo="false" class="btn btn-sm btn-light border rounded-pill px-3 fw-bold font-monospace" title="عرض ملف الطالب">
                        <i class="fa-solid fa-eye text-primary me-1"></i> عرض
                    </a>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function getAttendanceStatusBadgeClass(status) {
    if (status === 'Present' || status === 'حاضر') return 'bg-success bg-opacity-10 text-success';
    if (status === 'Absent' || status === 'غائب') return 'bg-danger bg-opacity-10 text-danger';
    if (status === 'Late' || status === 'متأخر') return 'bg-warning bg-opacity-10 text-warning';
    return 'bg-secondary bg-opacity-10 text-secondary';
}

function updateAttendance(sid, status) {
    const filterDate = document.getElementById('filterDate');
    const dateVal = filterDate ? filterDate.value : new Date().toISOString().split('T')[0];

    fetch('/attendance/api/mark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sid, date: dateVal, status })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast('تم التوثيق وتحديث حالة الحضور بنجاح!', 'success');
            loadAttendanceData();
        } else {
            showToast(data.message || 'حدث خطأ أثناء تحديث حالة الحضور', 'error');
        }
    })
    .catch(err => {
        console.error(err);
        showToast('تعذر الاتصال بالخادم للتحديث', 'error');
    });
}

function bulkMarkAttendance(status) {
    const sids = Array.from(attendanceState.selectedSIDs);
    if (sids.length === 0) {
        showToast('يرجى تحديد طلاب من الكشف أولاً', 'warning');
        return;
    }

    const filterDate = document.getElementById('filterDate');
    const dateVal = filterDate ? filterDate.value : new Date().toISOString().split('T')[0];

    let completed = 0;
    sids.forEach(sid => {
        fetch('/attendance/api/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sid, date: dateVal, status })
        })
        .then(res => res.json())
        .then(() => {
            completed++;
            if (completed === sids.length) {
                showToast(`تم تحديث حالة ${sids.length} طلاب بنجاح!`, 'success');
                clearBulkSelections();
                loadAttendanceData();
            }
        });
    });
}

function updateAttendanceKPICards() {
    const students = attendanceState.students || [];
    const total = students.length;

    let present = 0, absent = 0, late = 0;
    students.forEach(s => {
        if (s.Status === 'Present' || s.Status === 'حاضر') present++;
        if (s.Status === 'Absent' || s.Status === 'غائب') absent++;
        if (s.Status === 'Late' || s.Status === 'متأخر') late++;
    });

    const attRate = total > 0 ? roundOneDecimal((present / total) * 100) : 0;
    const absRate = total > 0 ? roundOneDecimal((absent / total) * 100) : 0;

    const elTotal = document.getElementById('kpiTotalStudents');
    const elPresent = document.getElementById('kpiPresent');
    const elAbsent = document.getElementById('kpiAbsent');
    const elLate = document.getElementById('kpiLate');
    const elAttRate = document.getElementById('kpiAttendanceRate');
    const elAbsRate = document.getElementById('kpiAbsenceRate');
    const elProgress = document.getElementById('kpiAttendanceProgress');

    if (elTotal) elTotal.textContent = total;
    if (elPresent) elPresent.textContent = present;
    if (elAbsent) elAbsent.textContent = absent;
    if (elLate) elLate.textContent = late;
    if (elAttRate) elAttRate.textContent = `${attRate}%`;
    if (elAbsRate) elAbsRate.textContent = `${absRate}%`;
    if (elProgress) elProgress.style.width = `${attRate}%`;
}

function initAttendanceChart() {
    const ctx = document.getElementById('attendanceStatsChart');
    if (!ctx || typeof Chart === 'undefined') return;

    const students = attendanceState.students || [];
    let present = 0, absent = 0, late = 0, unrecorded = 0;

    students.forEach(s => {
        if (s.Status === 'Present' || s.Status === 'حاضر') present++;
        else if (s.Status === 'Absent' || s.Status === 'غائب') absent++;
        else if (s.Status === 'Late' || s.Status === 'متأخر') late++;
        else unrecorded++;
    });

    if (attendanceState.chartInstance) {
        attendanceState.chartInstance.destroy();
    }

    attendanceState.chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['حاضر', 'متأخر', 'غائب', 'غير مسجل'],
            datasets: [{
                data: [present, late, absent, unrecorded],
                backgroundColor: ['#22c55e', '#eab308', '#ef4444', '#94a3b8'],
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

function toggleSelectAllAttendance(masterCheckbox) {
    attendanceState.selectedSIDs.clear();
    if (masterCheckbox.checked) {
        attendanceState.filteredStudents.forEach(s => attendanceState.selectedSIDs.add(s.SID));
    }
    renderAttendanceTable();
    updateBulkBar();
}

function toggleStudentSelection(sid, event) {
    if (event) event.stopPropagation();
    if (attendanceState.selectedSIDs.has(sid)) {
        attendanceState.selectedSIDs.delete(sid);
    } else {
        attendanceState.selectedSIDs.add(sid);
    }
    updateBulkBar();
}

function clearBulkSelections() {
    attendanceState.selectedSIDs.clear();
    const master = document.getElementById('selectAllAttendance');
    if (master) master.checked = false;
    renderAttendanceTable();
    updateBulkBar();
}

function updateBulkBar() {
    const bulkBar = document.getElementById('attendanceBulkBar');
    const countBadge = document.getElementById('bulkSelectedCount');
    const count = attendanceState.selectedSIDs.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (countBadge) countBadge.textContent = `${count} محدد`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function exportAttendanceReport() {
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterDate = document.getElementById('filterDate');

    const classId = filterClass ? filterClass.value : '';
    const sectionId = filterSection ? filterSection.value : '';
    const dateVal = filterDate ? filterDate.value : '';

    window.location.href = `/attendance/export?class_id=${classId}&section_id=${sectionId}&date=${dateVal}`;
}

function submitQuickMark() {
    const sidEl = document.getElementById('quickMarkSID');
    const statusEl = document.getElementById('quickMarkStatus');

    if (!sidEl || !statusEl || !sidEl.value) {
        showToast('يرجى كتابة الرقم الأكاديمي للطالب للمتابعة', 'warning');
        return;
    }

    const sid = parseInt(sidEl.value);
    const status = statusEl.value;

    updateAttendance(sid, status);

    const modalEl = document.getElementById('quickMarkModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }
}

function showAttendanceLoading(show) {
    const spinner = document.getElementById('attendanceLoadingSpinner');
    if (spinner) {
        if (show) spinner.classList.remove('d-none');
        else spinner.classList.add('d-none');
    }
}

function showEmptyAttendanceState(show, title = '', message = '') {
    const emptyContainer = document.getElementById('attendanceEmptyState');
    const tableWrapper = document.getElementById('attendanceTableContainer');
    const titleEl = document.getElementById('emptyStateTitle');
    const messageEl = document.getElementById('emptyStateMessage');

    if (show) {
        if (emptyContainer) emptyContainer.classList.remove('d-none');
        if (tableWrapper) tableWrapper.classList.add('d-none');
        if (titleEl && title) titleEl.textContent = title;
        if (messageEl && message) messageEl.textContent = message;
    } else {
        if (emptyContainer) emptyContainer.classList.add('d-none');
        if (tableWrapper) tableWrapper.classList.remove('d-none');
    }
}

function roundOneDecimal(num) {
    return Math.round(num * 10) / 10;
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
