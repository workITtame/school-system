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
    window.viewAttendanceProfile = viewAttendanceProfile;
    window.printAttendanceProfile = printAttendanceProfile;
    window.openBulkAttendanceWizardModal = openBulkAttendanceWizardModal;
    window.goToAttWizardStep = goToAttWizardStep;
    window.nextAttWizardStep = nextAttWizardStep;
    window.prevAttWizardStep = prevAttWizardStep;
    window.setAllWzStatus = setAllWzStatus;
    window.updateWzStudentStatus = updateWzStudentStatus;
    window.openAttendanceAnalyticsModal = openAttendanceAnalyticsModal;
    window.printAttendanceAnalytics = printAttendanceAnalytics;

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

                // Check URL parameter for ?attendance_id=XX or ?sid=XX
                const urlParams = new URLSearchParams(window.location.search);
                const attId = urlParams.get('attendance_id') || urlParams.get('sid');
                if (attId) {
                    const targetSid = parseInt(attId);
                    const targetStudent = attendanceState.students.find(s => s.SID === targetSid);
                    if (targetStudent) {
                        setTimeout(() => viewAttendanceProfile(targetSid), 200);
                    }
                }
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
            <tr class="align-middle cursor-pointer" onclick="viewAttendanceProfile(${s.SID}, event)">
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
                            onclick="event.stopPropagation();"
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
                    <button type="button" onclick="viewAttendanceProfile(${s.SID}, event)" class="btn btn-sm btn-light border rounded-pill px-3 fw-bold font-monospace" title="عرض الملف الشخصي للسجل">
                        <i class="fa-solid fa-eye text-primary me-1"></i> عرض
                    </button>
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

function exportAttendanceReport(exportType = 'excel', mode = 'all') {
    const filterClass = document.getElementById('filterClass') || document.getElementById('attendanceClassSelect');
    const filterSection = document.getElementById('filterSection') || document.getElementById('attendanceSectionSelect');
    const filterSubject = document.getElementById('filterSubject') || document.getElementById('attendanceSubjectSelect');
    const filterDate = document.getElementById('filterDate') || document.getElementById('attendanceDateSelect');

    const urlParams = new URLSearchParams(window.location.search);
    const classId = (filterClass && filterClass.value) ? filterClass.value : (urlParams.get('class_id') || '');
    const sectionId = (filterSection && filterSection.value) ? filterSection.value : (urlParams.get('section_id') || '');
    const subjectId = (filterSubject && filterSubject.value) ? filterSubject.value : (urlParams.get('subject_id') || '');
    const dateVal = (filterDate && filterDate.value) ? filterDate.value : (urlParams.get('date') || '');

    let statusParam = '';
    let onlyRecorded = 0;

    if (mode === 'recorded' || mode === 'محضرين') {
        onlyRecorded = 1;
    } else if (mode === 'present' || mode === 'حاضر') {
        statusParam = 'حاضر';
    } else if (mode === 'absent' || mode === 'غائب') {
        statusParam = 'غائب';
    } else if (mode === 'late' || mode === 'متأخر') {
        statusParam = 'متأخر';
    } else if (mode === 'excused' || mode === 'مستأذن') {
        statusParam = 'مستأذن';
    } else {
        const statusFilterEl = document.getElementById('attendanceStatusFilter') || document.getElementById('filterStatus');
        if (statusFilterEl && statusFilterEl.value) {
            statusParam = statusFilterEl.value;
        }
    }

    const selectedSids = [];
    if (mode === 'selected') {
        const checkedBoxes = document.querySelectorAll('.student-select-cb:checked, .attendance-cb:checked');
        checkedBoxes.forEach(cb => {
            if (cb.value) selectedSids.push(cb.value);
        });
    }

    const params = new URLSearchParams();
    if (exportType === 'pdf') params.append('type', 'pdf');
    if (classId) params.append('class_id', classId);
    if (sectionId) params.append('section_id', sectionId);
    if (subjectId) params.append('subject_id', subjectId);
    if (dateVal) params.append('date', dateVal);
    if (statusParam) params.append('status', statusParam);
    if (onlyRecorded) params.append('only_recorded', '1');
    if (selectedSids.length > 0) params.append('sids', selectedSids.join(','));

    window.location.href = `/attendance/export?${params.toString()}`;
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

/* ==========================================================================
   ATTENDANCE RECORD PROFILE MODAL CONTROLLER (10 SECTIONS)
   ========================================================================== */

let profilePerfChartInstance = null;

function viewAttendanceProfile(sid, event) {
    if (event) event.stopPropagation();
    const student = attendanceState.students.find(s => s.SID === sid);
    if (!student) return;

    const modalEl = document.getElementById('viewAttendanceProfileModal');
    if (!modalEl) return;

    // Header Badges & Titles
    const headerBadge = document.getElementById('atp-header-badge');
    const sidBadge = document.getElementById('atp-sid-badge');
    const statusBadge = document.getElementById('atp-status-badge');
    const heroTitle = document.getElementById('atp-hero-title');
    const heroSubtitle = document.getElementById('atp-hero-subtitle');
    const heroAvatar = document.getElementById('atp-student-avatar');
    const btnStudent = document.getElementById('atp-btn-student');

    const codeStr = `ATT-${student.SID}`;
    if (headerBadge) headerBadge.textContent = codeStr;
    if (sidBadge) sidBadge.textContent = `SID-${student.SID}`;
    if (heroTitle) heroTitle.textContent = student.SName || 'طالب مقيد';
    
    const filterDate = document.getElementById('filterDate');
    const dateVal = filterDate ? filterDate.value : '2026-08-03';
    if (heroSubtitle) heroSubtitle.textContent = `السجل بتاريخ ${dateVal} | توثيق المنظومة الأكاديمية`;
    if (heroAvatar) heroAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(student.SName || 'Student')}&background=fff&color=2563eb`;

    if (btnStudent) btnStudent.href = `/students/view/${student.SID}`;

    const qaStudent = document.getElementById('atp-qa-student');
    if (qaStudent) qaStudent.href = `/students/view/${student.SID}`;

    // Status Badge
    if (statusBadge) {
        statusBadge.textContent = student.Status || 'حاضر';
        if (student.Status === 'Absent' || student.Status === 'غائب') {
            statusBadge.className = 'badge bg-danger rounded-pill px-3 py-1 font-monospace';
        } else if (student.Status === 'Late' || student.Status === 'متأخر') {
            statusBadge.className = 'badge bg-warning text-dark rounded-pill px-3 py-1 font-monospace';
        } else {
            statusBadge.className = 'badge bg-success rounded-pill px-3 py-1 font-monospace';
        }
    }

    // Student Card Details
    const cardAvatar = document.getElementById('atp-card-student-avatar');
    const cardName = document.getElementById('atp-card-student-name');
    const cardSid = document.getElementById('atp-card-student-sid');

    if (cardAvatar) cardAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(student.SName || 'Student')}&background=2563eb&color=fff`;
    if (cardName) cardName.textContent = student.SName || 'اسم الطالب';
    if (cardSid) cardSid.textContent = `الرقم الأكاديمي: SID-${student.SID}`;

    // Attendance Info
    const infoDateDay = document.getElementById('atp-info-date-day');
    const infoStatus = document.getElementById('atp-info-status');
    const infoTime = document.getElementById('atp-info-time');
    const infoNote = document.getElementById('atp-info-note');

    if (infoDateDay) infoDateDay.textContent = `تاريخ التوثيق: ${dateVal}`;
    if (infoStatus) infoStatus.textContent = student.Status || 'حاضر';
    if (infoTime) infoTime.textContent = student.Time ? new Date(student.Time).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' }) : '08:00 ص';
    if (infoNote) infoNote.textContent = student.Note || 'لا توجد ملاحظات';

    // Render Analytics Chart
    initProfilePerfChart();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initProfilePerfChart() {
    const ctx = document.getElementById('attendancePerfChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (profilePerfChartInstance) {
        profilePerfChartInstance.destroy();
    }

    profilePerfChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['الأسبوع 1', 'الأسبوع 2', 'الأسبوع 3', 'الأسبوع 4'],
            datasets: [{
                label: 'نسبة الحضور الأسبوعية %',
                data: [100, 95, 98, 100],
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                borderColor: '#22c55e',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
}

function printAttendanceProfile() {
    window.print();
}

/* ==========================================================================
   ENTERPRISE BULK ATTENDANCE WIZARD CONTROLLER (5-STEP WIZARD)
   ========================================================================== */

let attWizardState = {
    currentStep: 1,
    classId: '',
    sectionId: '',
    date: '',
    defaultStatus: 'Present',
    students: []
};

function openBulkAttendanceWizardModal() {
    attWizardState.currentStep = 1;
    
    // Sync class and section from filters if available
    const fClass = document.getElementById('filterClass');
    const fSec = document.getElementById('filterSection');
    const fDate = document.getElementById('filterDate');

    const wzClass = document.getElementById('wzClass');
    const wzSec = document.getElementById('wzSection');
    const wzDate = document.getElementById('wzDate');

    if (wzClass && fClass && fClass.value) wzClass.value = fClass.value;
    if (wzSec && fSec && fSec.value) wzSec.value = fSec.value;
    if (wzDate && fDate && fDate.value) wzDate.value = fDate.value;

    updateAttWizardUI();

    const modalEl = document.getElementById('bulkAttendanceWizardModal');
    if (modalEl) {
        const bsModal = new bootstrap.Modal(modalEl);
        bsModal.show();
    }
}

function goToAttWizardStep(step) {
    if (step > attWizardState.currentStep && !validateAttWizardStep(attWizardState.currentStep)) {
        return;
    }
    attWizardState.currentStep = step;
    updateAttWizardUI();
}

function nextAttWizardStep() {
    if (!validateAttWizardStep(attWizardState.currentStep)) return;

    if (attWizardState.currentStep === 3) {
        // Moving to step 4: populate review screen
        populateAttWizardReview();
        attWizardState.currentStep = 4;
        updateAttWizardUI();
    } else if (attWizardState.currentStep === 4) {
        // Step 4 -> 5: Save data
        saveBulkAttWizardData();
    } else {
        attWizardState.currentStep++;
        updateAttWizardUI();
    }
}

function prevAttWizardStep() {
    if (attWizardState.currentStep > 1) {
        attWizardState.currentStep--;
        updateAttWizardUI();
    }
}

function validateAttWizardStep(step) {
    if (step === 1) {
        const cVal = document.getElementById('wzClass')?.value;
        const sVal = document.getElementById('wzSection')?.value;
        if (!cVal || !sVal) {
            showToast('يرجى اختيار الصف والشعبة للمتابعة', 'warning');
            return false;
        }
        attWizardState.classId = cVal;
        attWizardState.sectionId = sVal;
    } else if (step === 2) {
        const dVal = document.getElementById('wzDate')?.value;
        if (!dVal) {
            showToast('يرجى تحديد تاريخ التوثيق للمتابعة', 'warning');
            return false;
        }
        attWizardState.date = dVal;
        attWizardState.defaultStatus = document.getElementById('wzDefaultStatus')?.value || 'Present';
        loadAttWizardStudents();
    }
    return true;
}

function loadAttWizardStudents() {
    fetch(`/attendance/api/students?class_id=${attWizardState.classId}&section_id=${attWizardState.sectionId}&date=${attWizardState.date}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                attWizardState.students = (data.data || []).map(s => {
                    let status = s.Status;
                    if (!status || status === 'غير مسجل') {
                        if (attWizardState.defaultStatus === 'Present') status = 'Present';
                        else if (attWizardState.defaultStatus === 'Absent') status = 'Absent';
                    }
                    return { ...s, Status: status, Note: s.Note || '' };
                });
                renderAttWizardTable();
            }
        });
}

function renderAttWizardTable() {
    const tbody = document.getElementById('wzStudentsTableBody');
    if (!tbody) return;

    let html = '';
    let present = 0, absent = 0, late = 0;

    attWizardState.students.forEach((s, idx) => {
        if (s.Status === 'Present' || s.Status === 'حاضر') present++;
        else if (s.Status === 'Absent' || s.Status === 'غائب') absent++;
        else if (s.Status === 'Late' || s.Status === 'متأخر') late++;

        html += `
            <tr class="align-middle">
                <td class="fw-bold text-muted">${idx + 1}</td>
                <td class="text-start font-monospace fw-bold text-dark">${s.SName}</td>
                <td class="font-monospace text-primary fw-bold">${s.SID}</td>
                <td>
                    <select class="form-select form-select-sm rounded-pill fw-bold font-monospace text-center mx-auto" style="width:130px;" onchange="updateWzStudentStatus(${s.SID}, this.value)">
                        <option value="Present" ${s.Status === 'Present' || s.Status === 'حاضر' ? 'selected' : ''}>حاضر</option>
                        <option value="Absent" ${s.Status === 'Absent' || s.Status === 'غائب' ? 'selected' : ''}>غائب</option>
                        <option value="Late" ${s.Status === 'Late' || s.Status === 'متأخر' ? 'selected' : ''}>متأخر</option>
                    </select>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm rounded-pill font-monospace" placeholder="ملاحظة..." value="${s.Note || ''}" onchange="updateWzStudentNote(${s.SID}, this.value)">
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    const elTotal = document.getElementById('wzCountTotal');
    const elPres = document.getElementById('wzCountPresent');
    const elLate = document.getElementById('wzCountLate');
    const elAbs = document.getElementById('wzCountAbsent');

    if (elTotal) elTotal.textContent = attWizardState.students.length;
    if (elPres) elPres.textContent = present;
    if (elLate) elLate.textContent = late;
    if (elAbs) elAbs.textContent = absent;
}

function updateWzStudentStatus(sid, status) {
    const student = attWizardState.students.find(s => s.SID === sid);
    if (student) {
        student.Status = status;
        renderAttWizardTable();
    }
}

function updateWzStudentNote(sid, note) {
    const student = attWizardState.students.find(s => s.SID === sid);
    if (student) {
        student.Note = note;
    }
}

function setAllWzStatus(status) {
    attWizardState.students.forEach(s => s.Status = status);
    renderAttWizardTable();
}

function populateAttWizardReview() {
    const wzRevDate = document.getElementById('wzRevDate');
    const wzRevClassSec = document.getElementById('wzRevClassSec');
    const wzRevPresent = document.getElementById('wzRevPresent');
    const wzRevLate = document.getElementById('wzRevLate');
    const wzRevAbsent = document.getElementById('wzRevAbsent');

    if (wzRevDate) wzRevDate.textContent = attWizardState.date;
    
    const cEl = document.getElementById('wzClass');
    const sEl = document.getElementById('wzSection');
    const cText = cEl ? cEl.options[cEl.selectedIndex]?.text : '';
    const sText = sEl ? sEl.options[sEl.selectedIndex]?.text : '';
    if (wzRevClassSec) wzRevClassSec.textContent = `${cText} - ${sText}`;

    let present = 0, absent = 0, late = 0;
    attWizardState.students.forEach(s => {
        if (s.Status === 'Present' || s.Status === 'حاضر') present++;
        else if (s.Status === 'Absent' || s.Status === 'غائب') absent++;
        else if (s.Status === 'Late' || s.Status === 'متأخر') late++;
    });

    if (wzRevPresent) wzRevPresent.textContent = present;
    if (wzRevLate) wzRevLate.textContent = late;
    if (wzRevAbsent) wzRevAbsent.textContent = absent;
}

function saveBulkAttWizardData() {
    const dateVal = attWizardState.date;
    const students = attWizardState.students;

    let completed = 0;
    students.forEach(s => {
        fetch('/attendance/api/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sid: s.SID, date: dateVal, status: s.Status })
        })
        .then(res => res.json())
        .then(() => {
            completed++;
            if (completed === students.length) {
                // Show success report step 5
                attWizardState.currentStep = 5;
                updateAttWizardUI();

                const elSucTotal = document.getElementById('wzSucTotal');
                const elSucUpdated = document.getElementById('wzSucUpdated');
                if (elSucTotal) elSucTotal.textContent = students.length;
                if (elSucUpdated) elSucUpdated.textContent = students.length;
            }
        });
    });
}

function updateAttWizardUI() {
    const step = attWizardState.currentStep;

    // Toggle panes
    for (let i = 1; i <= 5; i++) {
        const pane = document.getElementById(`att-pane-${i}`);
        const dot = document.getElementById(`att-step-dot-${i}`);

        if (pane) {
            if (i === step) pane.classList.remove('d-none');
            else pane.classList.add('d-none');
        }

        if (dot) {
            if (i < step) {
                dot.className = 'btn btn-sm rounded-circle fw-bold position-relative z-2 btn-success';
            } else if (i === step) {
                dot.className = 'btn btn-sm rounded-circle fw-bold position-relative z-2 btn-primary';
            } else {
                dot.className = 'btn btn-sm rounded-circle fw-bold position-relative z-2 btn-light border';
            }
        }
    }

    // Step badge & progress bar
    const stepBadge = document.getElementById('att-wizard-step-badge');
    const progressBar = document.getElementById('att-wizard-progress');
    if (stepBadge) stepBadge.textContent = `الخطوة ${step} من 5`;
    if (progressBar) progressBar.style.width = `${step * 20}%`;

    // Footer buttons
    const btnPrev = document.getElementById('att-btn-prev');
    const btnNext = document.getElementById('att-btn-next');
    const footer = document.getElementById('att-wizard-footer');

    if (btnPrev) btnPrev.disabled = (step === 1 || step === 5);

    if (step === 5) {
        if (footer) footer.classList.add('d-none');
    } else {
        if (footer) footer.classList.remove('d-none');
        if (btnNext) {
            if (step === 4) {
                btnNext.innerHTML = '<i class="fa-solid fa-check-double me-1"></i> حفظ وتأثير الكشف النهائي';
                btnNext.className = 'btn btn-success rounded-pill px-5 fw-bold shadow-sm';
            } else {
                btnNext.innerHTML = 'التالي <i class="fa-solid fa-arrow-left ms-1"></i>';
                btnNext.className = 'btn btn-primary rounded-pill px-5 fw-bold shadow-sm';
            }
        }
    }
}

/* ==========================================================================
   ATTENDANCE ANALYTICS & REPORTS CONTROLLER (POWER BI & M365 INSIGHTS)
   ========================================================================== */

let analyticsTrendChartInstance = null;

function openAttendanceAnalyticsModal() {
    const modalEl = document.getElementById('attendanceAnalyticsModal');
    if (!modalEl) return;

    initAttendanceAnalyticsChart();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initAttendanceAnalyticsChart() {
    const ctx = document.getElementById('anAttTrendChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (analyticsTrendChartInstance) {
        analyticsTrendChartInstance.destroy();
    }

    analyticsTrendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس'],
            datasets: [
                {
                    label: 'نسبة الحضور %',
                    data: [99.1, 98.5, 97.8, 95.2, 92.4],
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'نسبة الغياب %',
                    data: [0.9, 1.5, 2.2, 4.8, 7.6],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            }
        }
    });
}

function printAttendanceAnalytics() {
    window.print();
}
