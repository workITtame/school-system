/* ==========================================================================
   ENTERPRISE SAAS GRADES MANAGEMENT CONTROLLER (static/js/grades.js)
   ========================================================================== */

let gradesState = {
    referenceData: null,
    studentsData: [],
    performanceChartInstance: null,
    selectedSids: new Set()
};

document.addEventListener('turbo:load', function() {
    initGradesModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initGradesModule();
});

function initGradesModule() {
    const panelEl = document.getElementById('gradesGridPanel');
    if (!panelEl || panelEl.dataset.initialized === 'true') return;
    panelEl.dataset.initialized = 'true';

    // Register global window handlers
    window.loadReferenceData = loadReferenceData;
    window.exportGradesExcel = exportGradesExcel;
    window.toggleSelectAllGrades = toggleSelectAllGrades;
    window.toggleGradeSelection = toggleGradeSelection;
    window.clearGradesBulkSelections = clearGradesBulkSelections;
    window.submitBulkGrades = submitBulkGrades;

    setupGradesEventListeners();
    loadReferenceData();
}

function setupGradesEventListeners() {
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterSubject = document.getElementById('filterSubject');
    const filterSearch = document.getElementById('filterSearch');
    const resetBtn = document.getElementById('resetFiltersBtn');
    const filterForm = document.getElementById('filterForm');

    if (filterClass) {
        filterClass.addEventListener('change', function() {
            const cid = parseInt(this.value);
            if (filterSection) filterSection.innerHTML = '<option value="">اختر الشعبة</option>';
            if (filterSubject) filterSubject.innerHTML = '<option value="">اختر المادة</option>';

            if (!cid || !gradesState.referenceData) {
                if (filterSection) filterSection.disabled = true;
                if (filterSubject) filterSubject.disabled = true;
                return;
            }

            const selectedClass = gradesState.referenceData.classes.find(c => c.CID === cid);
            if (selectedClass) {
                if (filterSection) {
                    selectedClass.sections.forEach(s => {
                        filterSection.innerHTML += `<option value="${s.SectionID}">${s.SectionName}</option>`;
                    });
                    filterSection.disabled = false;
                }
                if (filterSubject) {
                    selectedClass.subjects.forEach(sub => {
                        filterSubject.innerHTML += `<option value="${sub.SubID}">${sub.SubName}</option>`;
                    });
                    filterSubject.disabled = false;
                }
            }
        });
    }

    if (filterSearch) {
        filterSearch.addEventListener('input', applyGradesSearchFilter);
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            const filterTerm = document.getElementById('filterTerm');
            const filterExam = document.getElementById('filterExam');

            if (filterTerm && filterTerm.options.length > 0) filterTerm.selectedIndex = 0;
            if (filterExam && filterExam.options.length > 0) filterExam.selectedIndex = 0;
            if (filterClass) filterClass.value = '';
            if (filterSection) { filterSection.value = ''; filterSection.disabled = true; }
            if (filterSubject) { filterSubject.value = ''; filterSubject.disabled = true; }
            if (filterSearch) filterSearch.value = '';

            const workspace = document.getElementById('workspaceContainer');
            const emptyState = document.getElementById('gradesEmptyState');
            if (workspace) workspace.classList.add('d-none');
            if (emptyState) emptyState.classList.remove('d-none');
        });
    }

    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadStudentsGradeGrid();
        });
    }
}

function getJwtHeaders() {
    const jwtToken = document.querySelector('meta[name="jwt-token"]')?.getAttribute('content');
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (jwtToken || '')
    };
}

function loadReferenceData() {
    const filterTerm = document.getElementById('filterTerm');
    const filterExam = document.getElementById('filterExam');
    const filterClass = document.getElementById('filterClass');
    const btnLoadStudents = document.getElementById('btnLoadStudents');

    fetch('/api/v1/grades/reference', { headers: getJwtHeaders() })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                gradesState.referenceData = data.data;

                if (filterTerm) {
                    filterTerm.innerHTML = '';
                    data.data.terms.forEach(t => filterTerm.innerHTML += `<option value="${t.T_ID}">${t.T_Name}</option>`);
                }
                if (filterExam) {
                    filterExam.innerHTML = '<option value="">اختر الامتحان</option>';
                    data.data.exams.forEach(e => filterExam.innerHTML += `<option value="${e.ExamID}">${e.ExamName}</option>`);
                }
                if (filterClass) {
                    filterClass.innerHTML = '<option value="">اختر الصف</option>';
                    data.data.classes.forEach(c => filterClass.innerHTML += `<option value="${c.CID}">${c.CName}</option>`);
                }
                if (btnLoadStudents) btnLoadStudents.disabled = false;
            } else {
                showToast('خطأ في تحميل بيانات المراجع الحية', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('تعذر الاتصال بخادم بيانات الدرجات', 'error');
        });
}

function loadStudentsGradeGrid() {
    const filterTerm = document.getElementById('filterTerm');
    const filterExam = document.getElementById('filterExam');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterSubject = document.getElementById('filterSubject');

    const term_id = filterTerm?.value;
    const exam_id = filterExam?.value;
    const class_id = filterClass?.value;
    const section_id = filterSection?.value;
    const subject_id = filterSubject?.value;

    if (!term_id || !exam_id || !class_id || !section_id || !subject_id) {
        showToast('الرجاء اختيار جميع الفلاتر الأساسية لعرض كشف الدرجات', 'warning');
        return;
    }

    const loadingState = document.getElementById('loadingState');
    const workspaceContainer = document.getElementById('workspaceContainer');
    const emptyState = document.getElementById('gradesEmptyState');

    if (loadingState) loadingState.classList.remove('d-none');
    if (workspaceContainer) workspaceContainer.classList.add('d-none');
    if (emptyState) emptyState.classList.add('d-none');

    const url = `/api/v1/grades/class?term_id=${term_id}&exam_id=${exam_id}&class_id=${class_id}&section_id=${section_id}&subject_id=${subject_id}`;

    fetch(url, { headers: getJwtHeaders() })
        .then(res => res.json())
        .then(data => {
            if (loadingState) loadingState.classList.add('d-none');
            if (data.success) {
                gradesState.studentsData = data.data || [];
                renderStudentsGradeGrid();
                if (workspaceContainer) workspaceContainer.classList.remove('d-none');
                updateGradesKPICards();
                updateGradesChart();
            } else {
                showToast(data.message || 'حدث خطأ أثناء جلب الطلاب', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            if (loadingState) loadingState.classList.add('d-none');
            showToast('فشل جلب بيانات الطلاب والدرجات', 'error');
        });
}

function calculateLetter(score) {
    if (score === null || score === '' || isNaN(score)) return '-';
    const s = parseFloat(score);
    if (s >= 90) return 'A';
    if (s >= 80) return 'B';
    if (s >= 70) return 'C';
    if (s >= 60) return 'D';
    return 'F';
}

function getGradeLetterBadgeClass(letter) {
    switch (letter) {
        case 'A': return 'bg-success text-white';
        case 'B': return 'bg-primary text-white';
        case 'C': return 'bg-warning text-dark';
        case 'D': return 'bg-info text-dark';
        case 'F': return 'bg-danger text-white';
        default: return 'bg-secondary bg-opacity-10 text-muted';
    }
}

function renderStudentsGradeGrid() {
    const studentsBody = document.getElementById('studentsBody');
    if (!studentsBody) return;

    studentsBody.innerHTML = '';

    if (gradesState.studentsData.length === 0) {
        studentsBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-muted font-monospace">
                    <i class="fa-solid fa-user-slash fs-1 mb-2 text-muted opacity-50"></i>
                    <h5 class="fw-bold">لا يوجد طلاب في هذه الشعبة</h5>
                </td>
            </tr>`;
        return;
    }

    gradesState.studentsData.forEach((st, index) => {
        const scoreVal = (st.Score !== null && st.Score !== undefined) ? st.Score : '';
        const letter = calculateLetter(scoreVal);
        const badgeClass = getGradeLetterBadgeClass(letter);
        const percentStr = scoreVal !== '' ? `${parseFloat(scoreVal).toFixed(1)}%` : '—';
        
        let statusBadge = '<span class="badge bg-secondary-subtle text-secondary rounded-pill px-3 py-1 font-monospace">غير مرصود</span>';
        if (letter === 'A' || letter === 'B' || letter === 'C' || letter === 'D') {
            statusBadge = '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-check me-1"></i> ناجح</span>';
        } else if (letter === 'F') {
            statusBadge = '<span class="badge bg-danger-subtle text-danger rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-xmark me-1"></i> راسب</span>';
        }

        const tr = document.createElement('tr');
        tr.className = 'align-middle grade-student-row';
        tr.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input rounded-2" onclick="toggleGradeSelection(${st.SID}, event)">
            </td>
            <td class="fw-bold text-muted font-monospace">${index + 1}</td>
            <td class="text-start">
                <div class="d-flex align-items-center gap-2">
                    <div class="p-2 rounded-circle bg-primary bg-opacity-10 text-primary">
                        <i class="fa-solid fa-user-graduate"></i>
                    </div>
                    <div>
                        <strong class="d-block text-dark font-monospace">${st.StudentName}</strong>
                        <small class="text-muted extra-small">الرقم الأكاديمي: ${st.SID}</small>
                    </div>
                </div>
            </td>
            <td>
                <div class="input-group mx-auto shadow-sm rounded-pill overflow-hidden" style="width: 140px;">
                    <input type="number" step="0.5" min="0" max="100" 
                           class="form-control text-center score-input fw-bold font-monospace border-0" 
                           data-sid="${st.SID}" data-index="${index}"
                           value="${scoreVal}" placeholder="0.0" 
                           style="background-color: #f8fafc;">
                    <span class="input-group-text bg-light border-0 text-muted extra-small font-monospace">/100</span>
                </div>
            </td>
            <td>
                <span class="badge rounded-pill ${badgeClass} px-3 py-2 font-monospace fw-bold grade-letter-badge" id="badge_${st.SID}">
                    ${letter}
                </span>
            </td>
            <td class="font-monospace fw-bold text-primary" id="percent_${st.SID}">${percentStr}</td>
            <td id="status_${st.SID}">${statusBadge}</td>
            <td class="extra-small text-muted font-monospace">آلي مباشر</td>
        `;

        studentsBody.appendChild(tr);
    });

    setupScoreInputsListeners();
}

function setupScoreInputsListeners() {
    const inputs = document.querySelectorAll('.score-input');

    inputs.forEach((input, idx) => {
        // Keyboard navigation (Enter / Down Arrow move to next score input)
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === 'ArrowDown') {
                e.preventDefault();
                if (idx + 1 < inputs.length) {
                    inputs[idx + 1].focus();
                    inputs[idx + 1].select();
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (idx - 1 >= 0) {
                    inputs[idx - 1].focus();
                    inputs[idx - 1].select();
                }
            }
        });

        // Live Validation & Calculation
        input.addEventListener('input', function() {
            let val = this.value;
            if (val !== '') {
                let num = parseFloat(val);
                if (num < 0) { num = 0; this.value = 0; }
                if (num > 100) { num = 100; this.value = 100; }
            }

            const sid = this.getAttribute('data-sid');
            const letter = calculateLetter(this.value);
            const badge = document.getElementById(`badge_${sid}`);
            const percentEl = document.getElementById(`percent_${sid}`);
            const statusEl = document.getElementById(`status_${sid}`);

            // Update local state array
            const st = gradesState.studentsData.find(s => s.SID == sid);
            if (st) st.Score = (this.value !== '' && !isNaN(this.value)) ? parseFloat(this.value) : null;

            if (badge) {
                badge.className = `badge rounded-pill ${getGradeLetterBadgeClass(letter)} px-3 py-2 font-monospace fw-bold grade-letter-badge`;
                badge.textContent = letter;
            }

            if (percentEl) {
                percentEl.textContent = this.value !== '' ? `${parseFloat(this.value).toFixed(1)}%` : '—';
            }

            if (statusEl) {
                if (letter === 'A' || letter === 'B' || letter === 'C' || letter === 'D') {
                    statusEl.innerHTML = '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-check me-1"></i> ناجح</span>';
                } else if (letter === 'F') {
                    statusEl.innerHTML = '<span class="badge bg-danger-subtle text-danger rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-xmark me-1"></i> راسب</span>';
                } else {
                    statusEl.innerHTML = '<span class="badge bg-secondary-subtle text-secondary rounded-pill px-3 py-1 font-monospace">غير مرصود</span>';
                }
            }

            updateGradesKPICards();
            updateGradesChart();
        });
    });
}

function updateGradesKPICards() {
    const total = gradesState.studentsData.length;
    let entered = 0, missing = 0, sumScore = 0, passCount = 0;

    gradesState.studentsData.forEach(st => {
        if (st.Score !== null && st.Score !== undefined && !isNaN(st.Score)) {
            entered++;
            sumScore += st.Score;
            if (st.Score >= 60) passCount++;
        } else {
            missing++;
        }
    });

    const avgScore = entered > 0 ? (sumScore / entered).toFixed(1) : '0.0';
    const passRate = entered > 0 ? ((passCount / entered) * 100).toFixed(1) : '0.0';

    const elTotal = document.getElementById('kpiTotalStudents');
    const elEntered = document.getElementById('kpiEnteredGrades');
    const elMissing = document.getElementById('kpiMissingGrades');
    const elAvg = document.getElementById('kpiAverageScore');
    const elPassRate = document.getElementById('kpiPassRate');

    if (elTotal) elTotal.textContent = total;
    if (elEntered) elEntered.textContent = entered;
    if (elMissing) elMissing.textContent = missing;
    if (elAvg) elAvg.textContent = `${avgScore}%`;
    if (elPassRate) elPassRate.textContent = `${passRate}%`;
}

function updateGradesChart() {
    const counts = { 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0 };
    let hasData = false;

    gradesState.studentsData.forEach(st => {
        if (st.Score !== null && st.Score !== undefined && !isNaN(st.Score)) {
            counts[calculateLetter(st.Score)]++;
            hasData = true;
        }
    });

    const chartEmptyState = document.getElementById('chartEmptyState');
    const canvas = document.getElementById('performanceChart');
    if (!canvas) return;

    if (!hasData) {
        if (chartEmptyState) chartEmptyState.classList.remove('d-none');
        if (gradesState.performanceChartInstance) gradesState.performanceChartInstance.destroy();
        return;
    }

    if (chartEmptyState) chartEmptyState.classList.add('d-none');
    const ctx = canvas.getContext('2d');

    if (gradesState.performanceChartInstance) {
        gradesState.performanceChartInstance.data.datasets[0].data = [counts.A, counts.B, counts.C, counts.D, counts.F];
        gradesState.performanceChartInstance.update();
    } else {
        gradesState.performanceChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['ممتاز (A)', 'جيد جداً (B)', 'جيد (C)', 'مقبول (D)', 'راسب (F)'],
                datasets: [{
                    data: [counts.A, counts.B, counts.C, counts.D, counts.F],
                    backgroundColor: ['#22c55e', '#3b82f6', '#eab308', '#06b6d4', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                cutout: '70%'
            }
        });
    }
}

function applyGradesSearchFilter() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const rows = document.querySelectorAll('#studentsBody tr.grade-student-row');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (!searchVal || text.includes(searchVal)) {
            row.classList.remove('d-none');
        } else {
            row.classList.add('d-none');
        }
    });
}

function submitBulkGrades() {
    const filterTerm = document.getElementById('filterTerm');
    const filterExam = document.getElementById('filterExam');
    const filterSubject = document.getElementById('filterSubject');
    const btnSaveBulk = document.getElementById('btnSaveBulk');

    const payload = {
        term_id: filterTerm?.value,
        exam_id: filterExam?.value,
        subject_id: filterSubject?.value,
        grades: []
    };

    document.querySelectorAll('.score-input').forEach(input => {
        if (input.value.trim() !== '' && !isNaN(input.value)) {
            payload.grades.push({
                sid: input.getAttribute('data-sid'),
                score: parseFloat(input.value)
            });
        }
    });

    if (payload.grades.length === 0) {
        showToast('لا توجد درجات مدخلة للحفظ', 'warning');
        return;
    }

    const originalBtnText = btnSaveBulk ? btnSaveBulk.innerHTML : '';
    if (btnSaveBulk) {
        btnSaveBulk.disabled = true;
        btnSaveBulk.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> جاري الحفظ...';
    }

    fetch('/api/v1/grades/bulk', {
        method: 'POST',
        headers: getJwtHeaders(),
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (btnSaveBulk) {
                btnSaveBulk.disabled = false;
                btnSaveBulk.innerHTML = originalBtnText;
            }
            if (data.success) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: 'تم الحفظ بنجاح!',
                        text: 'تم حفظ واعتماد درجات الطلاب بنجاح في قاعدة البيانات.',
                        confirmButtonText: 'حسناً',
                        confirmButtonColor: '#2563eb'
                    });
                } else {
                    showToast('تم حفظ درجات الطلاب بنجاح!', 'success');
                }
            } else {
                showToast(data.message || 'خطأ أثناء حفظ الدرجات', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            if (btnSaveBulk) {
                btnSaveBulk.disabled = false;
                btnSaveBulk.innerHTML = originalBtnText;
            }
            showToast('تعذر الاتصال بالخادم لحفظ الدرجات', 'error');
        });
}

function toggleSelectAllGrades(masterCheckbox) {
    gradesState.selectedSids.clear();
    const rows = document.querySelectorAll('#studentsBody tr.grade-student-row:not(.d-none)');

    rows.forEach(row => {
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.checked = masterCheckbox.checked;
            const input = row.querySelector('.score-input');
            const sid = input ? input.getAttribute('data-sid') : null;
            if (masterCheckbox.checked && sid) {
                gradesState.selectedSids.add(sid);
            }
        }
    });

    updateGradesBulkBar();
}

function toggleGradeSelection(sid, event) {
    if (event) event.stopPropagation();
    const cb = event.target;

    if (cb.checked) {
        gradesState.selectedSids.add(sid);
    } else {
        gradesState.selectedSids.delete(sid);
    }

    updateGradesBulkBar();
}

function clearGradesBulkSelections() {
    gradesState.selectedSids.clear();
    const master = document.getElementById('selectAllGrades');
    if (master) master.checked = false;

    const checkboxes = document.querySelectorAll('#studentsBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    updateGradesBulkBar();
}

function updateGradesBulkBar() {
    const bulkBar = document.getElementById('gradesBulkBar');
    const countBadge = document.getElementById('bulkSelectedGradesCount');
    const count = gradesState.selectedSids.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (countBadge) countBadge.textContent = `${count} محدد`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function exportGradesExcel() {
    window.location.href = '/reports/excel?type=grades';
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
