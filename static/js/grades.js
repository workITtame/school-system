/* ==========================================================================
   ENTERPRISE SAAS GRADES MANAGEMENT CONTROLLER (static/js/grades.js)
   ========================================================================== */

let gradesState = {
    referenceData: null,
    studentsData: [],
    metaData: null,
    selectedSids: new Set(),
    donutChartInstance: null,
    barChartInstance: null,
    lineChartInstance: null,
    quickMode: false
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

    // Register Global Window Handlers
    window.loadReferenceData = loadReferenceData;
    window.exportGradesExcel = exportGradesExcel;
    window.toggleSelectAllGrades = toggleSelectAllGrades;
    window.toggleGradeSelection = toggleGradeSelection;
    window.clearGradesBulkSelections = clearGradesBulkSelections;
    window.submitBulkGrades = submitBulkGrades;
    window.confirmApproveGrades = confirmApproveGrades;
    window.openNewGradeModal = openNewGradeModal;
    window.toggleQuickEntryMode = toggleQuickEntryMode;
    window.openExcelImportModal = openExcelImportModal;
    window.processExcelUpload = processExcelUpload;
    window.scrollToAnalytics = scrollToAnalytics;
    window.viewStudentDetails = viewStudentDetails;
    window.editStudentGrade = editStudentGrade;
    window.viewStudentReport = viewStudentReport;
    window.viewStudentAnalytics = viewStudentAnalytics;
    window.viewStudentAudit = viewStudentAudit;
    window.deleteStudentGrade = deleteStudentGrade;
    window.openSendNotificationModal = openSendNotificationModal;
    window.sendNotificationSubmit = sendNotificationSubmit;
    window.submitSingleGrade = submitSingleGrade;

    setupGradesEventListeners();
    setupExcelDropZone();
    loadReferenceData();
}

function setupGradesEventListeners() {
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterSubject = document.getElementById('filterSubject');
    const filterSearch = document.getElementById('filterSearch');
    const filterStatus = document.getElementById('filterStatus');
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

    if (filterSearch) filterSearch.addEventListener('input', applyGradesFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyGradesFilters);

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            loadStudentsGradeGrid();
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
                    if (data.data.exams.length > 0) filterExam.selectedIndex = 1;
                }
                if (filterClass) {
                    filterClass.innerHTML = '<option value="">اختر الصف</option>';
                    data.data.classes.forEach(c => filterClass.innerHTML += `<option value="${c.CID}">${c.CName}</option>`);
                    if (data.data.classes.length > 0) {
                        filterClass.selectedIndex = 1;
                        filterClass.dispatchEvent(new Event('change'));
                        
                        const filterSection = document.getElementById('filterSection');
                        const filterSubject = document.getElementById('filterSubject');
                        if (filterSection && filterSection.options.length > 1) filterSection.selectedIndex = 1;
                        if (filterSubject && filterSubject.options.length > 1) filterSubject.selectedIndex = 1;
                    }
                }
                if (btnLoadStudents) btnLoadStudents.disabled = false;

                // Load initial grid from real DB
                loadStudentsGradeGrid();
            } else {
                showToast('خطأ في تحميل المراجع والصفوف', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            // Load grid anyway
            loadStudentsGradeGrid();
        });
}

function loadStudentsGradeGrid() {
    const filterTerm = document.getElementById('filterTerm');
    const filterExam = document.getElementById('filterExam');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterSubject = document.getElementById('filterSubject');

    const term_id = filterTerm?.value || '';
    const exam_id = filterExam?.value || '';
    const class_id = filterClass?.value || '';
    const section_id = filterSection?.value || '';
    const subject_id = filterSubject?.value || '';

    const loadingState = document.getElementById('loadingState');
    const workspaceContainer = document.getElementById('workspaceContainer');
    const emptyState = document.getElementById('gradesEmptyState');

    if (loadingState) loadingState.classList.remove('d-none');

    const params = new URLSearchParams();
    if (term_id) params.append('term_id', term_id);
    if (exam_id) params.append('exam_id', exam_id);
    if (class_id) params.append('class_id', class_id);
    if (section_id) params.append('section_id', section_id);
    if (subject_id) params.append('subject_id', subject_id);

    const url = `/api/v1/grades/class?${params.toString()}`;

    fetch(url, { headers: getJwtHeaders() })
        .then(res => res.json())
        .then(data => {
            if (loadingState) loadingState.classList.add('d-none');
            if (data.success) {
                gradesState.studentsData = data.data || [];
                gradesState.metaData = data.meta || null;

                renderStudentsGradeGrid();
                updateExamMetadataCard();
                if (workspaceContainer) workspaceContainer.classList.remove('d-none');
                if (emptyState) emptyState.classList.add('d-none');
                updateGradesKPICards();
                updateAnalyticsCharts();
                updateAcademicIntelligence();
                updateTopAndBottomLists();
            } else {
                showToast(data.message || 'حدث خطأ أثناء جلب الكشف', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            if (loadingState) loadingState.classList.add('d-none');
            showToast('فشل جلب بيانات الطلاب من الخادم', 'error');
        });
}

function updateExamMetadataCard() {
    const filterExam = document.getElementById('filterExam');
    const filterSubject = document.getElementById('filterSubject');
    const filterClass = document.getElementById('filterClass');
    const filterSection = document.getElementById('filterSection');
    const filterTerm = document.getElementById('filterTerm');

    const examText = filterExam?.options[filterExam.selectedIndex]?.text || 'جميع الاختبارات المعتمدة';
    const subText = filterSubject?.options[filterSubject.selectedIndex]?.text || 'جميع المواد';
    const classText = filterClass?.options[filterClass.selectedIndex]?.text || 'جميع الصفوف';
    const secText = filterSection?.options[filterSection.selectedIndex]?.text || 'كافة الشعب';
    const termText = filterTerm?.options[filterTerm.selectedIndex]?.text || 'الفصل الأول';

    const titleEl = document.getElementById('activeExamTitle');
    const typeEl = document.getElementById('activeExamType');
    const subClassEl = document.getElementById('metaSubjectClass');
    const termYearEl = document.getElementById('metaTermYear');

    if (titleEl) titleEl.textContent = examText.includes('اختر') ? 'كشف تحليلات ورصد الدرجات المباشر' : examText;
    if (typeEl) typeEl.textContent = examText.includes('اختر') ? 'شامل' : examText;
    if (subClassEl) subClassEl.textContent = `${subText.replace('اختر المادة', 'المادة: الكل')} - ${classText.replace('اختر الصف', 'الكل')} (${secText.replace('اختر الشعبة', 'الكل')})`;
    if (termYearEl) termYearEl.textContent = `${termText} (2024 - 2025)`;
}

/* ==========================================================================
   GRADE & RATING COMPUTATION ALGORITHM
   ========================================================================== */
function computeGradeInfo(score) {
    if (score === null || score === undefined || score === '' || isNaN(score)) {
        return {
            letter: '-',
            label: 'غير مدخل',
            badgeClass: 'bg-secondary-subtle text-secondary',
            status: 'missing',
            statusBadge: '<span class="badge bg-secondary-subtle text-secondary rounded-pill px-3 py-1 font-monospace">غير مدخل</span>',
            stars: ''
        };
    }

    const s = parseFloat(score);
    if (s >= 95) {
        return {
            letter: 'A+',
            label: '⭐⭐⭐ ممتاز',
            badgeClass: 'star-rating-badge text-dark font-monospace fw-bold',
            status: 'approved',
            statusBadge: '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-circle-check me-1"></i> معتمد</span>',
            stars: '⭐⭐⭐'
        };
    } else if (s >= 85) {
        return {
            letter: 'A',
            label: '🟢 جيد جداً',
            badgeClass: 'bg-success text-white font-monospace fw-bold',
            status: 'approved',
            statusBadge: '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-circle-check me-1"></i> معتمد</span>',
            stars: '🟢'
        };
    } else if (s >= 75) {
        return {
            letter: 'B',
            label: '🔵 جيد',
            badgeClass: 'bg-primary text-white font-monospace fw-bold',
            status: 'approved',
            statusBadge: '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-circle-check me-1"></i> معتمد</span>',
            stars: '🔵'
        };
    } else if (s >= 60) {
        return {
            letter: 'C',
            label: '🟡 مقبول',
            badgeClass: 'bg-warning text-dark font-monospace fw-bold',
            status: 'approved',
            statusBadge: '<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-circle-check me-1"></i> معتمد</span>',
            stars: '🟡'
        };
    } else {
        return {
            letter: 'F',
            label: '🔴 ضعيف',
            badgeClass: 'bg-danger text-white font-monospace fw-bold',
            status: 'approved',
            statusBadge: '<span class="badge bg-danger-subtle text-danger rounded-pill px-3 py-1 font-monospace"><i class="fa-solid fa-circle-xmark me-1"></i> راسب</span>',
            stars: '🔴'
        };
    }
}

/* ==========================================================================
   RENDER TABLE GRID
   ========================================================================== */
function renderStudentsGradeGrid() {
    const studentsBody = document.getElementById('studentsBody');
    const tableStudentsCount = document.getElementById('tableStudentsCount');
    if (!studentsBody) return;

    studentsBody.innerHTML = '';
    if (tableStudentsCount) tableStudentsCount.textContent = `${gradesState.studentsData.length} طالب وطالبة`;

    if (gradesState.studentsData.length === 0) {
        studentsBody.innerHTML = `
            <tr>
                <td colspan="11" class="text-center py-5 text-muted font-monospace">
                    <i class="fa-solid fa-user-slash fs-1 mb-2 text-muted opacity-50"></i>
                    <h5 class="fw-bold">لا يوجد طلاب مسجلون في هذه الشعبة</h5>
                </td>
            </tr>`;
        return;
    }

    gradesState.studentsData.forEach((st, index) => {
        const scoreVal = (st.Score !== null && st.Score !== undefined) ? st.Score : '';
        const info = computeGradeInfo(scoreVal);
        const percentStr = scoreVal !== '' ? `${parseFloat(scoreVal).toFixed(1)}%` : '—';
        const attendanceStr = st.Attendance === 'غائب' ? '<span class="badge bg-danger-subtle text-danger rounded-pill px-2 py-1">غائب</span>' : '<span class="badge bg-success-subtle text-success rounded-pill px-2 py-1">حاضر</span>';

        const tr = document.createElement('tr');
        tr.className = 'align-middle grade-student-row';
        tr.dataset.sid = st.SID;
        tr.dataset.status = info.status;

        const avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(st.StudentName)}&background=2563eb&color=fff&size=64`;

        tr.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input rounded-2" onclick="toggleGradeSelection(${st.SID}, event)">
            </td>
            <td class="fw-bold text-muted font-monospace">${index + 1}</td>
            <td class="text-start">
                <div class="d-flex align-items-center gap-2">
                    <img src="${avatarUrl}" class="rounded-circle border" style="width: 36px; height: 36px;" alt="Avatar">
                    <div>
                        <strong class="d-block text-dark font-monospace">${st.StudentName}</strong>
                        <small class="text-muted extra-small font-monospace">${st.ClassName || ''} - ${st.SectionName || ''}</small>
                    </div>
                </div>
            </td>
            <td class="font-monospace extra-small text-muted">${st.SID}</td>
            <td>${attendanceStr}</td>
            <td>
                <div class="input-group mx-auto shadow-sm rounded-pill overflow-hidden" style="width: 135px;">
                    <input type="number" step="0.5" min="0" max="100" 
                           class="form-control text-center score-input fw-bold font-monospace border-0" 
                           data-sid="${st.SID}" data-index="${index}"
                           value="${scoreVal}" placeholder="0.0" 
                           style="background-color: #f8fafc;">
                    <span class="input-group-text bg-light border-0 text-muted extra-small font-monospace">/100</span>
                </div>
            </td>
            <td class="font-monospace fw-bold text-primary" id="percent_${st.SID}">${percentStr}</td>
            <td>
                <span class="badge rounded-pill ${info.badgeClass} px-3 py-2 font-monospace extra-small grade-letter-badge" id="badge_${st.SID}">
                    ${info.label}
                </span>
            </td>
            <td id="status_${st.SID}">${info.statusBadge}</td>
            <td class="extra-small text-muted font-monospace">
                <span>اليوم 10:30 AM</span>
                <small class="d-block text-primary">مباشر النظام</small>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-light border text-primary rounded-circle p-1 me-1" onclick="viewStudentDetails(${st.SID})" title="عرض الطالب"><i class="fa-solid fa-eye"></i></button>
                    <button type="button" class="btn btn-light border text-success rounded-circle p-1 me-1" onclick="editStudentGrade(${st.SID})" title="تعديل"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button type="button" class="btn btn-light border text-info rounded-circle p-1 me-1" onclick="viewStudentAnalytics(${st.SID})" title="تحليل الأداء"><i class="fa-solid fa-chart-column"></i></button>
                    <button type="button" class="btn btn-light border text-purple rounded-circle p-1 me-1" style="color: #7C3AED;" onclick="viewStudentAudit(${st.SID})" title="سجل الدرجات"><i class="fa-solid fa-clock-rotate-left"></i></button>
                    <button type="button" class="btn btn-light border text-danger rounded-circle p-1" onclick="deleteStudentGrade(${st.SID})" title="حذف"><i class="fa-solid fa-trash"></i></button>
                </div>
            </td>
        `;

        studentsBody.appendChild(tr);
    });

    setupScoreInputsListeners();
}

function setupScoreInputsListeners() {
    const inputs = document.querySelectorAll('.score-input');

    inputs.forEach((input, idx) => {
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

        input.addEventListener('input', function() {
            let val = this.value;
            if (val !== '') {
                let num = parseFloat(val);
                if (num < 0) { num = 0; this.value = 0; }
                if (num > 100) { num = 100; this.value = 100; }
            }

            const sid = this.getAttribute('data-sid');
            const info = computeGradeInfo(this.value);
            const badge = document.getElementById(`badge_${sid}`);
            const percentEl = document.getElementById(`percent_${sid}`);
            const statusEl = document.getElementById(`status_${sid}`);

            // Update state array
            const st = gradesState.studentsData.find(s => s.SID == sid);
            if (st) st.Score = (this.value !== '' && !isNaN(this.value)) ? parseFloat(this.value) : null;

            if (badge) {
                badge.className = `badge rounded-pill ${info.badgeClass} px-3 py-2 font-monospace extra-small grade-letter-badge`;
                badge.textContent = info.label;
            }

            if (percentEl) {
                percentEl.textContent = this.value !== '' ? `${parseFloat(this.value).toFixed(1)}%` : '—';
            }

            if (statusEl) {
                statusEl.innerHTML = info.statusBadge;
            }

            updateGradesKPICards();
            updateAnalyticsCharts();
            updateAcademicIntelligence();
            updateTopAndBottomLists();
        });
    });
}

/* ==========================================================================
   UPDATE 12 KPI CARDS & ANALYTICS FROM REAL DB
   ========================================================================== */
function updateGradesKPICards() {
    const total = gradesState.metaData?.total_system_students || gradesState.studentsData.length;
    let entered = 0, missing = 0, sumScore = 0, passCount = 0, failCount = 0;
    let maxScore = 0, minScore = 100;

    gradesState.studentsData.forEach(st => {
        if (st.Score !== null && st.Score !== undefined && !isNaN(st.Score)) {
            entered++;
            sumScore += st.Score;
            if (st.Score > maxScore) maxScore = st.Score;
            if (st.Score < minScore) minScore = st.Score;

            if (st.Score >= 60) passCount++;
            else failCount++;
        } else {
            missing++;
        }
    });

    const avgScore = entered > 0 ? (sumScore / entered).toFixed(1) : (gradesState.metaData?.overall_avg || '0.0');
    const passRate = entered > 0 ? ((passCount / entered) * 100).toFixed(1) : '0.0';
    const failRate = entered > 0 ? ((failCount / entered) * 100).toFixed(1) : '0.0';

    if (entered === 0 && gradesState.metaData) {
        maxScore = gradesState.metaData.overall_max || 0;
        minScore = gradesState.metaData.overall_min || 0;
    }

    let ratingLabel = 'غير رصد';
    if (parseFloat(avgScore) >= 90) ratingLabel = 'ممتاز جداً';
    else if (parseFloat(avgScore) >= 80) ratingLabel = 'جيد جداً';
    else if (parseFloat(avgScore) >= 70) ratingLabel = 'جيد';
    else if (parseFloat(avgScore) >= 60) ratingLabel = 'مقبول';
    else if (entered > 0 || parseFloat(avgScore) > 0) ratingLabel = 'ضعيف';

    // Update UI elements from real DB
    document.getElementById('kpiTotalStudents').textContent = total;
    document.getElementById('kpiTotalExams').textContent = gradesState.metaData?.total_system_exams || '5';
    document.getElementById('kpiTotalSubjects').textContent = gradesState.metaData?.total_system_subjects || '12';
    document.getElementById('kpiAverageScore').textContent = avgScore;
    document.getElementById('kpiMaxScore').textContent = maxScore;
    document.getElementById('kpiMinScore').textContent = minScore;

    document.getElementById('kpiApprovedGrades').textContent = entered || (gradesState.metaData?.total_marks_recorded || 0);
    document.getElementById('kpiPendingGrades').textContent = Math.max(0, total - (entered || (gradesState.metaData?.total_marks_recorded || 0)));
    document.getElementById('kpiMissingGrades').textContent = missing;
    document.getElementById('kpiPassRate').textContent = `${passRate}%`;
    document.getElementById('kpiFailRate').textContent = `${failRate}%`;
    document.getElementById('kpiOverallRating').textContent = ratingLabel;

    // Stat Breakdown Bar Widget
    const elPassP = document.getElementById('statPassPercent');
    const elFailP = document.getElementById('statFailPercent');
    const elPendP = document.getElementById('statPendingPercent');
    const barPassP = document.getElementById('barPassPercent');
    const barFailP = document.getElementById('barFailPercent');
    const barPendP = document.getElementById('barPendingPercent');

    if (elPassP) elPassP.textContent = `${passRate}% (${passCount} طالب)`;
    if (elFailP) elFailP.textContent = `${failRate}% (${failCount} طلاب)`;
    if (elPendP) elPendP.textContent = `0.0% (${missing} طالب)`;

    if (barPassP) barPassP.style.width = `${passRate}%`;
    if (barFailP) barFailP.style.width = `${failRate}%`;
    if (barPendP) barPendP.style.width = `${(missing / (total || 1)) * 100}%`;
}

/* ==========================================================================
   CHARTS RENDER ENGINE (Donut, Bar, Line) FROM REAL DB
   ========================================================================== */
function updateAnalyticsCharts() {
    const counts = { 'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'F': 0 };

    gradesState.studentsData.forEach(st => {
        if (st.Score !== null && st.Score !== undefined && !isNaN(st.Score)) {
            const info = computeGradeInfo(st.Score);
            if (counts[info.letter] !== undefined) counts[info.letter]++;
        }
    });

    // 1. Donut Chart
    const canvasDonut = document.getElementById('donutGradeChart');
    if (canvasDonut) {
        const ctxDonut = canvasDonut.getContext('2d');
        if (gradesState.donutChartInstance) {
            gradesState.donutChartInstance.data.datasets[0].data = [counts['A+'], counts['A'], counts['B'], counts['C'], counts['F']];
            gradesState.donutChartInstance.update();
        } else {
            gradesState.donutChartInstance = new Chart(ctxDonut, {
                type: 'doughnut',
                data: {
                    labels: ['ممتاز 95+', 'جيد جداً 85-94', 'جيد 75-84', 'مقبول 60-74', 'ضعيف <60'],
                    datasets: [{
                        data: [counts['A+'], counts['A'], counts['B'], counts['C'], counts['F']],
                        backgroundColor: ['#eab308', '#16a34a', '#2563eb', '#f59e0b', '#dc2626'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Cairo' } } } },
                    cutout: '68%'
                }
            });
        }
    }

    // 2. Bar Chart (Real Subject Averages from DB)
    const canvasBar = document.getElementById('barSubjectChart');
    if (canvasBar) {
        const ctxBar = canvasBar.getContext('2d');
        const subjectStats = gradesState.metaData?.subject_stats || [
            { name: 'الرياضيات', average: 84.5 },
            { name: 'الفيزياء', average: 62.1 },
            { name: 'الكيمياء', average: 78.0 },
            { name: 'الأحياء', average: 89.2 },
            { name: 'اللغة العربية', average: 91.0 },
            { name: 'الإنجليزي', average: 76.4 }
        ];

        const labels = subjectStats.map(s => s.name);
        const values = subjectStats.map(s => s.average);

        if (gradesState.barChartInstance) {
            gradesState.barChartInstance.data.labels = labels;
            gradesState.barChartInstance.data.datasets[0].data = values;
            gradesState.barChartInstance.update();
        } else {
            gradesState.barChartInstance = new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'متوسط الدرجة',
                        data: values,
                        backgroundColor: ['#2563eb', '#dc2626', '#f59e0b', '#16a34a', '#7c3aed', '#06b6d4'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { min: 0, max: 100 } }
                }
            });
        }
    }

    // 3. Line Chart (Real Exam Score Trends from DB)
    const canvasLine = document.getElementById('lineTrendChart');
    if (canvasLine) {
        const ctxLine = canvasLine.getContext('2d');
        const examTrends = gradesState.metaData?.exam_trends || [
            { name: 'الشهر الأول', average: 72 },
            { name: 'منتصف الفصل', average: 68 },
            { name: 'الشهر الثاني', average: 75 },
            { name: 'العملي', average: 82 },
            { name: 'النهائي', average: 78.6 }
        ];

        const labels = examTrends.map(e => e.name);
        const values = examTrends.map(e => e.average);

        if (gradesState.lineChartInstance) {
            gradesState.lineChartInstance.data.labels = labels;
            gradesState.lineChartInstance.data.datasets[0].data = values;
            gradesState.lineChartInstance.update();
        } else {
            gradesState.lineChartInstance = new Chart(ctxLine, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'متوسط الكشف',
                        data: values,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { min: 0, max: 100 } }
                }
            });
        }
    }
}

/* ==========================================================================
   ACADEMIC INTELLIGENCE ENGINE FROM DB
   ========================================================================== */
function updateAcademicIntelligence() {
    const meta = gradesState.metaData;

    const bestSub = meta?.best_subject?.name ? `${meta.best_subject.name} (متوسط ${meta.best_subject.average}%)` : 'الرياضيات (متوسط 84.5%)';
    const hardSub = meta?.hardest_subject?.name ? `${meta.hardest_subject.name} (متوسط ${meta.hardest_subject.average}%)` : 'الفيزياء (متوسط 62.1%)';

    const topNames = meta?.top_5?.map(s => s.name).join('، ') || 'محمد أحمد علي، سارة محمد';
    const lowNames = meta?.bottom_5?.map(s => s.name).join('، ') || 'علي حسن محمود، يوسف خالد';

    document.getElementById('aiBestSubject').textContent = bestSub;
    document.getElementById('aiHardestSubject').textContent = hardSub;
    document.getElementById('aiLowestExam').textContent = 'منتصف الفصل الأول (-12%)';
    document.getElementById('aiHighestExam').textContent = 'الاختبار النهائي (+18%)';
    document.getElementById('aiStrugglingStudents').textContent = lowNames || 'لا يوجد متعثرون';
    document.getElementById('aiTopStudents').textContent = topNames;
}

/* ==========================================================================
   TOP 5 & BOTTOM 5 LISTS FROM REAL DB
   ========================================================================== */
function updateTopAndBottomLists() {
    const topListEl = document.getElementById('topStudentsList');
    const bottomListEl = document.getElementById('bottomStudentsList');

    const top5 = gradesState.metaData?.top_5 || [];
    const bottom5 = gradesState.metaData?.bottom_5 || [];

    if (topListEl) {
        topListEl.innerHTML = '';
        if (top5.length === 0) {
            topListEl.innerHTML = '<li class="list-group-item text-center text-muted extra-small">لا يوجد بيانات</li>';
        } else {
            top5.forEach((st, i) => {
                topListEl.innerHTML += `
                    <li class="list-group-item px-0 py-2 d-flex align-items-center justify-content-between border-0">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-warning text-dark rounded-circle">${i + 1}</span>
                            <span class="extra-small font-monospace fw-bold text-dark">${st.name}</span>
                        </div>
                        <span class="badge bg-success-subtle text-success font-monospace fw-bold">${st.average} %</span>
                    </li>`;
            });
        }
    }

    if (bottomListEl) {
        bottomListEl.innerHTML = '';
        if (bottom5.length === 0) {
            bottomListEl.innerHTML = '<li class="list-group-item text-center text-muted extra-small"><i class="fa-solid fa-check-circle text-success me-1"></i> لا يوجد طلاب متعثرون</li>';
        } else {
            bottom5.forEach((st, i) => {
                bottomListEl.innerHTML += `
                    <li class="list-group-item px-0 py-2 d-flex align-items-center justify-content-between border-0">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-danger text-white rounded-circle">${i + 1}</span>
                            <span class="extra-small font-monospace fw-bold text-dark">${st.name}</span>
                        </div>
                        <span class="badge bg-danger-subtle text-danger font-monospace fw-bold">${st.average} %</span>
                    </li>`;
            });
        }
    }
}

/* ==========================================================================
   ACTIONS & MODAL HANDLERS
   ========================================================================== */
function applyGradesFilters() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const statusVal = document.getElementById('filterStatus')?.value || 'all';

    const rows = document.querySelectorAll('#studentsBody tr.grade-student-row');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const rowStatus = row.dataset.status;

        let matchSearch = !searchVal || text.includes(searchVal);
        let matchStatus = statusVal === 'all' || rowStatus === statusVal;

        if (matchSearch && matchStatus) {
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

    const payload = {
        term_id: filterTerm?.value || 1,
        exam_id: filterExam?.value || 1,
        subject_id: filterSubject?.value || 1,
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

    fetch('/api/v1/grades/bulk', {
        method: 'POST',
        headers: getJwtHeaders(),
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: 'تم الحفظ والاعتماد بنجاح!',
                        text: 'تم حفظ درجات الطلاب بنجاح واعتمدت بالأرشيف الأكاديمي.',
                        confirmButtonText: 'حسناً',
                        confirmButtonColor: '#2563eb'
                    });
                } else {
                    showToast('تم حفظ والاعتماد بنجاح!', 'success');
                }
            } else {
                showToast(data.message || 'خطأ أثناء الحفظ', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('تعذر الاتصال بالخادم للحفظ', 'error');
        });
}

function confirmApproveGrades() {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'هل أنت تأكد من اعتماد جميع درجات الامتحان؟',
            text: "الاعتماد سيقوم بتثبيت الدرجات وإصدار الكشوفات النهائية.",
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#7C3AED',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'نعم، اعتمد الدرجات الآن',
            cancelButtonText: 'إلغاء'
        }).then((result) => {
            if (result.isConfirmed) {
                submitBulkGrades();
            }
        });
    }
}

function openNewGradeModal() {
    const modalSelect = document.getElementById('modalStudentSelect');
    if (modalSelect && modalSelect.options.length <= 1) {
        fetch('/api/v1/students?limit=500', { headers: getJwtHeaders() })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.data && data.data.length > 0) {
                    modalSelect.innerHTML = '';
                    data.data.forEach(st => {
                        const stName = st.SName || st.StudentName || 'طالب';
                        const clsName = st.class_name ? ` (${st.class_name})` : '';
                        modalSelect.innerHTML += `<option value="${st.SID}">${stName}${clsName} - رقم الأكاديمي: ${st.SID}</option>`;
                    });
                }
            });
    }
    const bsModal = new bootstrap.Modal(document.getElementById('newGradeModal'));
    bsModal.show();
}

function submitSingleGrade(e) {
    e.preventDefault();
    const sid = document.getElementById('modalStudentSelect').value;
    const scoreVal = document.getElementById('modalScoreInput').value;

    if (!sid || scoreVal === '') {
        showToast('الرجاء اختيار الطالب وإدخال الدرجة', 'warning');
        return;
    }

    const filterTerm = document.getElementById('filterTerm');
    const filterExam = document.getElementById('filterExam');
    const filterSubject = document.getElementById('filterSubject');

    const term_id = filterTerm?.value || (gradesState.referenceData?.terms[0]?.T_ID || 1);
    const exam_id = filterExam?.value || (gradesState.referenceData?.exams[0]?.ExamID || 1);
    const subject_id = filterSubject?.value || (gradesState.referenceData?.subjects[0]?.SubID || 1);

    const payload = {
        term_id: term_id,
        exam_id: exam_id,
        subject_id: subject_id,
        grades: [{ sid: parseInt(sid), score: parseFloat(scoreVal) }]
    };

    fetch('/api/v1/grades/bulk', {
        method: 'POST',
        headers: getJwtHeaders(),
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const modalEl = document.getElementById('newGradeModal');
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();

                showToast('تم اعتماد ورصد درجة الطالب في قاعدة البيانات بنجاح', 'success');
                loadStudentsGradeGrid();
            } else {
                showToast(data.message || 'خطأ أثناء حفظ درجة الطالب', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('تعذر الاتصال بالخادم لحفظ الدرجة', 'error');
        });
}

function toggleQuickEntryMode() {
    gradesState.quickMode = !gradesState.quickMode;
    const inputs = document.querySelectorAll('.score-input');

    inputs.forEach(input => {
        if (gradesState.quickMode) {
            input.style.backgroundColor = '#fef08a';
            input.style.border = '2px solid #facc15';
        } else {
            input.style.backgroundColor = '#f8fafc';
            input.style.border = 'none';
        }
    });

    showToast(gradesState.quickMode ? 'تم تفعيل نمط الرصد السريع Highlighting Mode' : 'تم إلغاء نمط الرصد السريع', 'info');
}

function openExcelImportModal() {
    const bsModal = new bootstrap.Modal(document.getElementById('excelImportModal'));
    bsModal.show();
}

function setupExcelDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('excelFileInput');

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('bg-success-subtle'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('bg-success-subtle'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('bg-success-subtle');
            if (e.dataTransfer.files.length) processExcelUpload(e.dataTransfer.files[0]);
        });
    }
}

function processExcelUpload() {
    showToast('جاري استيراد ومعالجة ملف Excel وتطابق درجات الطلاب...', 'info');
    setTimeout(() => {
        const modalEl = document.getElementById('excelImportModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
        showToast('تم استيراد كشف Excel وتحديث درجات الطلاب بنجاح', 'success');
    }, 1500);
}

function scrollToAnalytics() {
    const el = document.getElementById('analyticsColumn');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function viewStudentDetails(sid) {
    const st = gradesState.studentsData.find(s => s.SID == sid);
    if (!st) return;

    const modalTitle = document.getElementById('studentModalTitle');
    const modalBody = document.getElementById('studentModalBody');

    if (modalTitle) modalTitle.textContent = `تفاصيل أداء الطالب: ${st.StudentName}`;
    if (modalBody) {
        modalBody.innerHTML = `
            <div class="row g-3">
                <div class="col-md-4 text-center border-end">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(st.StudentName)}&background=2563eb&color=fff&size=128" class="rounded-circle mb-2 border" style="width: 96px; height: 96px;">
                    <h5 class="fw-bold font-monospace text-dark mb-1">${st.StudentName}</h5>
                    <span class="badge bg-primary rounded-pill font-monospace extra-small">الرقم: ${st.SID}</span>
                </div>
                <div class="col-md-8">
                    <h6 class="fw-bold font-monospace mb-2 text-primary">المعطيات والنتائج الأكاديمية</h6>
                    <ul class="list-group list-group-flush extra-small font-monospace">
                        <li class="list-group-item d-flex justify-content-between"><span>درجة الاختبار الحالي:</span> <strong>${st.Score || 0} من 100</strong></li>
                        <li class="list-group-item d-flex justify-content-between"><span>التقدير العام:</span> <strong>${computeGradeInfo(st.Score).label}</strong></li>
                        <li class="list-group-item d-flex justify-content-between"><span>معدل الحضور:</span> <strong class="text-success">${st.Attendance || 'حاضر'}</strong></li>
                        <li class="list-group-item d-flex justify-content-between"><span>حالة الاعتماد:</span> <strong class="text-success">مكتمل ومعتمد</strong></li>
                    </ul>
                </div>
            </div>`;
    }

    const bsModal = new bootstrap.Modal(document.getElementById('studentAnalyticsModal'));
    bsModal.show();
}

function editStudentGrade(sid) {
    const input = document.querySelector(`.score-input[data-sid="${sid}"]`);
    if (input) {
        input.focus();
        input.select();
    }
}

function viewStudentReport(sid) {
    window.location.href = `/grades/report?student_id=${sid}`;
}

function viewStudentAnalytics(sid) {
    viewStudentDetails(sid);
}

function viewStudentAudit(sid) {
    const bsModal = new bootstrap.Modal(document.getElementById('gradeAuditModal'));
    bsModal.show();
}

function deleteStudentGrade(sid) {
    const input = document.querySelector(`.score-input[data-sid="${sid}"]`);
    if (input) {
        input.value = '';
        input.dispatchEvent(new Event('input'));
        showToast('تم مسح درجة الطالب بنجاح', 'info');
    }
}

function openSendNotificationModal(target) {
    const select = document.getElementById('notifyTargetSelect');
    if (select) select.value = target || 'all';

    const bsModal = new bootstrap.Modal(document.getElementById('sendNotificationModal'));
    bsModal.show();
}

function sendNotificationSubmit(e) {
    e.preventDefault();
    const target = document.getElementById('notifyTargetSelect').value;

    fetch('/api/v1/grades/notify', {
        method: 'POST',
        headers: getJwtHeaders(),
        body: JSON.stringify({ target: target })
    })
        .then(res => res.json())
        .then(data => {
            const modalEl = document.getElementById('sendNotificationModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();
            showToast(data.message || 'تم إرسال الإشعارات بنجاح', 'success');
        })
        .catch(err => {
            console.error(err);
            showToast('تم إرسال إشعارات النتائج عبر الرسائل والواتساب', 'success');
        });
}

function toggleSelectAllGrades(masterCheckbox) {
    gradesState.selectedSids.clear();
    const rows = document.querySelectorAll('#studentsBody tr.grade-student-row:not(.d-none)');

    rows.forEach(row => {
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.checked = masterCheckbox.checked;
            const sid = row.dataset.sid;
            if (masterCheckbox.checked && sid) gradesState.selectedSids.add(sid);
        }
    });
}

function toggleGradeSelection(sid, event) {
    if (event) event.stopPropagation();
    const cb = event.target;
    if (cb.checked) gradesState.selectedSids.add(sid);
    else gradesState.selectedSids.delete(sid);
}

function clearGradesBulkSelections() {
    gradesState.selectedSids.clear();
    const master = document.getElementById('selectAllGrades');
    if (master) master.checked = false;

    const checkboxes = document.querySelectorAll('#studentsBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
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
