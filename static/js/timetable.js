/* ==========================================================================
   ENTERPRISE SAAS TIMETABLE MODULE CONTROLLER (static/js/timetable.js)
   ========================================================================== */

let timetableState = {
    referenceData: null,
    entries: [],
    filteredEntries: [],
    selectedSlotIds: new Set(),
    currentTermId: null,
    currentClassId: null,
    currentSectionId: null,
    activeView: 'grid' // grid or list
};

document.addEventListener('turbo:load', function() {
    initTimetableModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initTimetableModule();
});

function initTimetableModule() {
    const tableEl = document.getElementById('mainTimetableGrid');
    if (!tableEl || tableEl.dataset.initialized === 'true') return;
    tableEl.dataset.initialized = 'true';

    const jwtToken = document.querySelector('meta[name="jwt-token"]')?.getAttribute('content');
    window.apiHeadersJSON = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (jwtToken || '')
    };

    setupEventListeners();
    loadTimetableReferenceData();
}

/* ==========================================================================
   1. REFERENCE DATA FETCH & DROPDOWN POPULATION
   ========================================================================== */
function loadTimetableReferenceData() {
    showLoadingSpinner(true);

    fetch('/api/v1/timetable/reference-data', { headers: window.apiHeadersJSON })
        .then(res => res.json())
        .then(data => {
            showLoadingSpinner(false);
            if (data.success) {
                timetableState.referenceData = data.data;
                populateFilterDropdowns();
                populateModalDropdowns();
                updateKPICards();

                // Check URL parameters for class_id / section_id
                const urlParams = new URLSearchParams(window.location.search);
                const classParam = urlParams.get('class_id');
                const sectionParam = urlParams.get('section_id');

                if (classParam) {
                    const classSelect = document.getElementById('filterClass');
                    if (classSelect) {
                        classSelect.value = classParam;
                        handleClassChange(classParam, sectionParam);
                    }
                }
            } else {
                showToast('خطأ في تحميل البيانات الأساسية للجدول', 'error');
            }
        })
        .catch(err => {
            showLoadingSpinner(false);
            console.error(err);
            showToast('تعذر الاتصال بالخادم لتحميل البيانات الأكاديمية', 'error');
        });
}

function populateFilterDropdowns() {
    const ref = timetableState.referenceData;
    if (!ref) return;

    // Term Select
    const termSelect = document.getElementById('filterTerm');
    if (termSelect && ref.terms) {
        termSelect.innerHTML = '<option value="">اختر الفصل الدراسي</option>';
        ref.terms.forEach(t => {
            termSelect.innerHTML += `<option value="${t.T_ID}">${t.T_Name}</option>`;
        });
        if (ref.terms.length > 0) termSelect.value = ref.terms[0].T_ID;
    }

    // Class Select
    const classSelect = document.getElementById('filterClass');
    if (classSelect && ref.classes) {
        classSelect.innerHTML = '<option value="">اختر الصف الدراسي</option>';
        ref.classes.forEach(c => {
            classSelect.innerHTML += `<option value="${c.CID}">${c.CName}</option>`;
        });
    }

    // Day Select
    const daySelect = document.getElementById('filterDay');
    if (daySelect && ref.days) {
        daySelect.innerHTML = '<option value="">جميع الأيام</option>';
        ref.days.forEach(d => {
            daySelect.innerHTML += `<option value="${d.DayID}">${d.DName}</option>`;
        });
    }

    // Lesson Select
    const lessonSelect = document.getElementById('filterLesson');
    if (lessonSelect && ref.lessons) {
        lessonSelect.innerHTML = '<option value="">جميع الحصص</option>';
        ref.lessons.forEach(l => {
            lessonSelect.innerHTML += `<option value="${l.LessonID}">${l.LessonName}</option>`;
        });
    }

    // Teacher Select
    const teacherSelect = document.getElementById('filterTeacher');
    if (teacherSelect && ref.teachers) {
        teacherSelect.innerHTML = '<option value="">جميع المعلمين</option>';
        ref.teachers.forEach(t => {
            teacherSelect.innerHTML += `<option value="${t.TeacherID}">${t.TeacherName}</option>`;
        });
    }
}

function populateModalDropdowns() {
    const ref = timetableState.referenceData;
    if (!ref) return;

    const addDay = document.getElementById('addSlotDaySelect');
    const addLesson = document.getElementById('addSlotLessonSelect');
    const addTerm = document.getElementById('addSlotTermSelect');
    const addClass = document.getElementById('addSlotClassSelect');

    if (addDay && ref.days) {
        addDay.innerHTML = ref.days.map(d => `<option value="${d.DayID}">${d.DName}</option>`).join('');
    }
    if (addLesson && ref.lessons) {
        addLesson.innerHTML = ref.lessons.map(l => `<option value="${l.LessonID}">${l.LessonName}</option>`).join('');
    }
    if (addTerm && ref.terms) {
        addTerm.innerHTML = ref.terms.map(t => `<option value="${t.T_ID}">${t.T_Name}</option>`).join('');
    }
    if (addClass && ref.classes) {
        addClass.innerHTML = '<option value="">اختر الصف</option>' + ref.classes.map(c => `<option value="${c.CID}">${c.CName}</option>`).join('');
    }
}

function handleClassChange(classId, autoSelectSectionId = null) {
    const ref = timetableState.referenceData;
    const sectionSelect = document.getElementById('filterSection');
    const subjectSelect = document.getElementById('filterSubject');

    if (!sectionSelect || !ref) return;

    sectionSelect.innerHTML = '<option value="">اختر الشعبة</option>';
    if (subjectSelect) subjectSelect.innerHTML = '<option value="">جميع المواد</option>';

    if (!classId) {
        sectionSelect.disabled = true;
        return;
    }

    const selectedClass = ref.classes.find(c => c.CID === parseInt(classId));
    if (selectedClass) {
        sectionSelect.disabled = false;
        if (selectedClass.sections) {
            selectedClass.sections.forEach(s => {
                sectionSelect.innerHTML += `<option value="${s.SectionID}">${s.SectionName}</option>`;
            });
        }
        if (autoSelectSectionId) {
            sectionSelect.value = autoSelectSectionId;
        } else if (selectedClass.sections && selectedClass.sections.length > 0) {
            sectionSelect.value = selectedClass.sections[0].SectionID;
        }

        if (subjectSelect && selectedClass.subjects) {
            selectedClass.subjects.forEach(sub => {
                subjectSelect.innerHTML += `<option value="${sub.SubID}">${sub.SubName}</option>`;
            });
        }
    }
    fetchTimetableGridData();
}

/* ==========================================================================
   2. TIMETABLE FETCH & RENDER ENGINE
   ========================================================================== */
function fetchTimetableGridData() {
    const termId = document.getElementById('filterTerm')?.value;
    const classId = document.getElementById('filterClass')?.value;
    const sectionId = document.getElementById('filterSection')?.value;

    timetableState.currentTermId = termId;
    timetableState.currentClassId = classId;
    timetableState.currentSectionId = sectionId;

    if (!termId || !classId || !sectionId) {
        showEmptyState(true, 'يرجى اختيار الترم، الصف، والشعبة لترسيم الجدول الأسبوعي.');
        return;
    }

    showLoadingSpinner(true);
    const url = `/api/v1/timetable?term_id=${termId}&class_id=${classId}&section_id=${sectionId}`;

    fetch(url, { headers: window.apiHeadersJSON })
        .then(res => res.json())
        .then(data => {
            showLoadingSpinner(false);
            if (data.success) {
                timetableState.entries = data.data || [];
                applyFiltersAndRender();
            } else {
                showToast(data.message || 'تعذر جلب بيانات الجدول', 'error');
                showEmptyState(true);
            }
        })
        .catch(err => {
            showLoadingSpinner(false);
            console.error(err);
            showToast('حدث خطأ أثناء تحميل الحصص المجدولة', 'error');
        });
}

function applyFiltersAndRender() {
    const searchVal = document.getElementById('filterSearch')?.value.toLowerCase().trim() || '';
    const dayVal = document.getElementById('filterDay')?.value;
    const lessonVal = document.getElementById('filterLesson')?.value;
    const teacherVal = document.getElementById('filterTeacher')?.value;
    const subjectVal = document.getElementById('filterSubject')?.value;

    let list = [...timetableState.entries];

    if (searchVal) {
        list = list.filter(item => 
            (item.SubjectName && item.SubjectName.toLowerCase().includes(searchVal)) ||
            (item.TeacherName && item.TeacherName.toLowerCase().includes(searchVal))
        );
    }
    if (dayVal) {
        list = list.filter(item => item.DayID === parseInt(dayVal));
    }
    if (lessonVal) {
        list = list.filter(item => item.LessonID === parseInt(lessonVal));
    }
    if (teacherVal) {
        list = list.filter(item => item.TeacherID === parseInt(teacherVal));
    }
    if (subjectVal) {
        list = list.filter(item => item.SubID === parseInt(subjectVal));
    }

    timetableState.filteredEntries = list;
    updateKPICards();
    renderTimetableGrid();
}

function renderTimetableGrid() {
    const ref = timetableState.referenceData;
    const gridBody = document.getElementById('timetableGridBody');

    if (!gridBody || !ref) return;

    const days = ref.days || [];
    const lessons = ref.lessons || [];
    const entries = timetableState.filteredEntries;

    if (timetableState.entries.length === 0) {
        showEmptyState(true, 'لم يتم إضافة أي حصص لهذه الشعبة بعد. ابدأ بإضافة أول حصة الآن!');
        return;
    }

    showEmptyState(false);

    let html = '';
    days.forEach(day => {
        html += `<tr data-day-id="${day.DayID}">`;
        html += `
            <td class="fw-bold bg-light align-middle text-center p-3 font-monospace text-dark border-end" style="width: 140px;">
                <div class="d-flex align-items-center justify-content-center gap-2">
                    <i class="fa-solid fa-calendar-day text-primary"></i>
                    <span>${day.DName}</span>
                </div>
            </td>
        `;

        lessons.forEach(lesson => {
            const entry = entries.find(e => e.DayID === day.DayID && e.LessonID === lesson.LessonID);
            
            if (entry) {
                const color = getSubjectColor(entry.SubID, entry.SubjectColor);
                const isSelected = timetableState.selectedSlotIds.has(entry.SchoolTableID);
                
                html += `
                    <td class="p-2 align-middle timetable-cell-occupied position-relative" data-day-id="${day.DayID}" data-lesson-id="${lesson.LessonID}">
                        <div class="slot-card-container p-3 rounded-4 shadow-sm border text-white position-relative hover-scale transition-all ${isSelected ? 'border-primary ring-2' : ''}" style="background: ${color}; min-height: 110px;">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input slot-select-cb" value="${entry.SchoolTableID}" ${isSelected ? 'checked' : ''} onclick="toggleSlotSelection(${entry.SchoolTableID}, event)">
                                </div>
                                <div class="dropdown no-print">
                                    <button class="btn btn-sm btn-light bg-white bg-opacity-20 border-0 rounded-circle text-white p-1" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                        <i class="fa-solid fa-ellipsis-vertical"></i>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-end rounded-4 shadow border-0 font-monospace small">
                                        <li><a class="dropdown-item" href="#" onclick="viewSlotDetail(${entry.SchoolTableID}, event)"><i class="fa-solid fa-eye text-info me-2"></i> معاينة التفاصيل</a></li>
                                        <li><a class="dropdown-item" href="#" onclick="openAddSlotModalWithCell(${day.DayID}, ${lesson.LessonID})"><i class="fa-solid fa-pen-to-square text-warning me-2"></i> تعديل الحصة</a></li>
                                        <li><hr class="dropdown-divider"></li>
                                        <li><a class="dropdown-item text-danger" href="#" onclick="deleteSlotConfirm(${entry.SchoolTableID}, event)"><i class="fa-solid fa-trash me-2"></i> حذف الحصة</a></li>
                                    </ul>
                                </div>
                            </div>

                            <div class="fw-extrabold mb-1 fs-6 text-truncate" title="${entry.SubjectName || ''}">
                                <i class="fa-solid fa-book-open me-1 opacity-75"></i> ${entry.SubjectName || 'غير محدد'}
                            </div>
                            <div class="small opacity-90 text-truncate mb-2" title="${entry.TeacherName || ''}">
                                <i class="fa-solid fa-chalkboard-user me-1 opacity-75"></i> ${entry.TeacherName || 'غير كادر'}
                            </div>

                            <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top border-white border-opacity-25 font-monospace extra-small">
                                <span class="badge bg-white bg-opacity-20 text-white rounded-pill px-2 py-1">
                                    <i class="fa-solid fa-clock me-1"></i> ${lesson.LessonName || 'حصة'}
                                </span>
                                <span class="badge bg-white bg-opacity-20 text-white rounded-pill px-2 py-1">مؤكد</span>
                            </div>
                        </div>
                    </td>
                `;
            } else {
                html += `
                    <td class="p-2 align-middle timetable-cell-empty cursor-pointer" data-day-id="${day.DayID}" data-lesson-id="${lesson.LessonID}" onclick="openAddSlotModalWithCell(${day.DayID}, ${lesson.LessonID})">
                        <div class="h-100 p-3 rounded-4 border border-dashed d-flex flex-column align-items-center justify-content-center text-muted bg-light-subtle hover-bg-white transition-all" style="min-height: 110px;">
                            <i class="fa-solid fa-plus fs-5 text-secondary opacity-50 mb-1"></i>
                            <small class="extra-small font-monospace opacity-75">إضافة حصة</small>
                        </div>
                    </td>
                `;
            }
        });

        html += `</tr>`;
    });

    gridBody.innerHTML = html;
}

/* ==========================================================================
   3. KPI CARDS CALCULATION & UPDATES
   ========================================================================== */
function updateKPICards() {
    const entries = timetableState.entries || [];
    const ref = timetableState.referenceData;

    const totalSlots = entries.length;
    const activeSlots = entries.filter(e => !e.is_deleted).length;

    const uniqueTeachers = new Set(entries.map(e => e.TeacherID)).size;
    const uniqueSubjects = new Set(entries.map(e => e.SubID)).size;
    const uniqueClasses = ref ? (ref.classes ? ref.classes.length : 0) : 0;

    const totalPossibleSlots = 25;
    const occupancyRate = Math.min(100, Math.round((totalSlots / totalPossibleSlots) * 100));

    animateCounter('kpiTotalSlots', totalSlots);
    animateCounter('kpiActiveSlots', activeSlots);
    animateCounter('kpiTeachersCount', uniqueTeachers);
    animateCounter('kpiSubjectsCount', uniqueSubjects);
    animateCounter('kpiClassesCount', uniqueClasses);
    
    const occupancyEl = document.getElementById('kpiOccupancyRate');
    const occupancyProgress = document.getElementById('kpiOccupancyProgress');
    if (occupancyEl) occupancyEl.textContent = `${occupancyRate}%`;
    if (occupancyProgress) occupancyProgress.style.width = `${occupancyRate}%`;
}

function animateCounter(id, finalValue) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = finalValue;
}

/* ==========================================================================
   4. BULK ACTIONS & SELECTION
   ========================================================================== */
function toggleSlotSelection(id, event) {
    if (event) event.stopPropagation();
    
    if (timetableState.selectedSlotIds.has(id)) {
        timetableState.selectedSlotIds.delete(id);
    } else {
        timetableState.selectedSlotIds.add(id);
    }

    updateBulkBarUI();
}

function updateBulkBarUI() {
    const bulkBar = document.getElementById('floatingBulkBar');
    const selectedCountSpan = document.getElementById('bulkSelectedCount');
    const count = timetableState.selectedSlotIds.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (selectedCountSpan) selectedCountSpan.textContent = `${count} حصص محددة`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function clearSlotSelections() {
    timetableState.selectedSlotIds.clear();
    updateBulkBarUI();
    renderTimetableGrid();
}

function deleteBulkSlots() {
    const ids = Array.from(timetableState.selectedSlotIds);
    if (ids.length === 0) return;

    Swal.fire({
        title: `حذف ${ids.length} حصص محددة؟`,
        text: "هل أنت متأكد من حذف الحصص المحددة من الجدول الدراسي؟",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'نعم، احذف الحصص',
        cancelButtonText: 'إلغاء'
    }).then(res => {
        if (res.isConfirmed) {
            Promise.all(ids.map(id => 
                fetch(`/api/v1/timetable/${id}`, { method: 'DELETE', headers: window.apiHeadersJSON })
            )).then(() => {
                showToast(`تم حذف ${ids.length} حصص بنجاح`, 'success');
                clearSlotSelections();
                fetchTimetableGridData();
            }).catch(err => {
                console.error(err);
                showToast('حدث خطأ أثناء تنفيذ الحذف الجماعي', 'error');
            });
        }
    });
}

/* ==========================================================================
   5. QUICK ACTIONS & MODALS
   ========================================================================== */
function openAddSlotModalWithCell(dayId, lessonId) {
    const addModal = document.getElementById('addSlotModal');
    if (!addModal) return;

    const daySelect = document.getElementById('addSlotDaySelect');
    const lessonSelect = document.getElementById('addSlotLessonSelect');
    const classSelect = document.getElementById('addSlotClassSelect');

    if (daySelect) daySelect.value = dayId;
    if (lessonSelect) lessonSelect.value = lessonId;
    if (classSelect) {
        classSelect.value = timetableState.currentClassId || '';
        classSelect.dispatchEvent(new Event('change'));
    }

    const bsModal = new bootstrap.Modal(addModal);
    bsModal.show();
}

function handleAddSlotFormSubmit(event) {
    event.preventDefault();
    const form = event.target;

    const payload = {
        term_id: parseInt(document.getElementById('addSlotTermSelect').value || timetableState.currentTermId),
        class_id: parseInt(document.getElementById('addSlotClassSelect').value || timetableState.currentClassId),
        section_id: parseInt(document.getElementById('addSlotSectionSelect').value || timetableState.currentSectionId),
        day_id: parseInt(document.getElementById('addSlotDaySelect').value),
        lesson_id: parseInt(document.getElementById('addSlotLessonSelect').value),
        subject_id: parseInt(document.getElementById('addSlotSubjectSelect').value),
        teacher_id: parseInt(document.getElementById('addSlotTeacherSelect').value)
    };

    if (!payload.class_id || !payload.section_id || !payload.subject_id || !payload.teacher_id) {
        showToast('يرجى تعبئة جميع حقول الحصة الدراسية للمتابعة', 'warning');
        return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> جاري التثبيت...';
    }

    fetch('/api/v1/timetable', {
        method: 'POST',
        headers: window.apiHeadersJSON,
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-check me-1"></i> حفظ الحصة';
        }
        if (data.success) {
            showToast('تمت إضافة الحصة إلى الجدول بنجاح!', 'success');
            const bsModal = bootstrap.Modal.getInstance(document.getElementById('addSlotModal'));
            if (bsModal) bsModal.hide();
            fetchTimetableGridData();
        } else {
            Swal.fire({
                title: 'تعارض في التوزيع',
                text: data.message || 'حدث تعارض في الجدول بنفس الوقت',
                icon: 'error',
                confirmButtonColor: '#2563eb'
            });
        }
    })
    .catch(err => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-check me-1"></i> حفظ الحصة';
        }
        console.error(err);
        showToast('حدث خطأ في الاتصال بالخادم أثناء التثبيت', 'error');
    });
}

let sessionChartInstance = null;

function viewSlotDetail(id, event) {
    if (event) event.stopPropagation();
    const entry = timetableState.entries.find(e => e.SchoolTableID === id);
    if (!entry) return;

    const modalEl = document.getElementById('viewSlotProfileModal');
    if (!modalEl) return;

    // Header Badges & Titles
    const headerBadge = document.getElementById('tsp-header-badge');
    const codeBadge = document.getElementById('tsp-code-badge');
    const heroTitle = document.getElementById('tsp-hero-title');
    const heroSubtitle = document.getElementById('tsp-hero-subtitle');
    const heroCard = document.getElementById('tsp-hero-card');

    const codeStr = `SLOT-${entry.SchoolTableID}`;
    if (headerBadge) headerBadge.textContent = codeStr;
    if (codeBadge) codeBadge.textContent = codeStr;
    if (heroTitle) heroTitle.textContent = entry.SubjectName || 'المادة الدراسية';
    if (heroSubtitle) heroSubtitle.textContent = `المعلم: ${entry.TeacherName || 'غير مسند'} | ${entry.DayName || ''} - ${entry.LessonName || ''}`;

    const color = getSubjectColor(entry.SubID, entry.SubjectColor);
    if (heroCard) heroCard.style.background = color;

    // Deep Navigation Action Links
    const btnTeacher = document.getElementById('tsp-btn-teacher');
    const btnSubject = document.getElementById('tsp-btn-subject');
    const btnStudents = document.getElementById('tsp-btn-students');

    if (btnTeacher) btnTeacher.href = `/teacher/view/${entry.TeacherID || 1}`;
    if (btnSubject) btnSubject.href = `/academic/subjects?view_id=${entry.SubID || 1}`;
    if (btnStudents) btnStudents.href = `/students?class_id=${timetableState.currentClassId || 1}`;

    // KPI Cards
    const kpiStudents = document.getElementById('tsp-kpi-students');
    const kpiAttendance = document.getElementById('tsp-kpi-attendance');
    const kpiHomework = document.getElementById('tsp-kpi-homework');
    const kpiExams = document.getElementById('tsp-kpi-exams');
    const kpiAvgGrade = document.getElementById('tsp-kpi-avg-grade');

    if (kpiStudents) kpiStudents.textContent = '35';
    if (kpiAttendance) kpiAttendance.textContent = '94.5%';
    if (kpiHomework) kpiHomework.textContent = '8';
    if (kpiExams) kpiExams.textContent = '3';
    if (kpiAvgGrade) kpiAvgGrade.textContent = '88.5%';

    // Information details
    const infoTime = document.getElementById('tsp-info-time');
    const infoClass = document.getElementById('tsp-info-class');

    if (infoTime) infoTime.textContent = `${entry.DayName || ''} | ${entry.LessonName || ''}`;
    if (infoClass) infoClass.textContent = `الصف الدراسي المخصص`;

    // Teacher card
    const teacherName = document.getElementById('tsp-teacher-name');
    const teacherAvatar = document.getElementById('tsp-teacher-avatar');
    if (teacherName) teacherName.textContent = entry.TeacherName || 'غير مسند';
    if (teacherAvatar) teacherAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.TeacherName || 'Teacher')}&background=2563eb&color=fff`;

    // Subject card
    const subjectName = document.getElementById('tsp-subject-name');
    if (subjectName) subjectName.textContent = entry.SubjectName || 'المادة الدراسية';

    // Populate Quick Actions
    const quickActionsContainer = document.getElementById('session-quick-actions-container');
    if (quickActionsContainer) {
        quickActionsContainer.innerHTML = `
            <div class="col">
                <button type="button" class="quick-action-card w-100 border-0 bg-light text-center p-3 rounded-4" onclick="openAddSlotModalWithCell(${entry.DayID}, ${entry.LessonID})">
                    <i class="fa-solid fa-pen-to-square fs-3 text-warning mb-2 d-block mx-auto"></i>
                    <h6 class="fw-bold text-dark mb-0 small">تعديل الحصة</h6>
                </button>
            </div>
            <div class="col">
                <a href="/teacher/view/${entry.TeacherID || 1}" data-turbo="false" class="quick-action-card w-100 border-0 bg-light text-center p-3 rounded-4 d-block text-decoration-none">
                    <i class="fa-solid fa-chalkboard-user fs-3 text-primary mb-2 d-block mx-auto"></i>
                    <h6 class="fw-bold text-dark mb-0 small">ملف المعلم</h6>
                </a>
            </div>
            <div class="col">
                <a href="/academic/subjects?view_id=${entry.SubID || 1}" data-turbo="false" class="quick-action-card w-100 border-0 bg-light text-center p-3 rounded-4 d-block text-decoration-none">
                    <i class="fa-solid fa-book-open fs-3 text-info mb-2 d-block mx-auto"></i>
                    <h6 class="fw-bold text-dark mb-0 small">ملف المادة</h6>
                </a>
            </div>
            <div class="col">
                <a href="/students?class_id=${timetableState.currentClassId || 1}" data-turbo="false" class="quick-action-card w-100 border-0 bg-light text-center p-3 rounded-4 d-block text-decoration-none">
                    <i class="fa-solid fa-users fs-3 text-success mb-2 d-block mx-auto"></i>
                    <h6 class="fw-bold text-dark mb-0 small">عرض الطلاب</h6>
                </a>
            </div>
            <div class="col">
                <button type="button" class="quick-action-card w-100 border-0 bg-light text-center p-3 rounded-4" onclick="printSlotProfile()">
                    <i class="fa-solid fa-print fs-3 text-secondary mb-2 d-block mx-auto"></i>
                    <h6 class="fw-bold text-dark mb-0 small">طباعة التقرير</h6>
                </button>
            </div>
        `;
    }

    // Render Chart
    initSessionChart();

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function initSessionChart() {
    const ctx = document.getElementById('sessionPerfChart');
    if (!ctx || typeof Chart === 'undefined') return;

    if (sessionChartInstance) {
        sessionChartInstance.destroy();
    }

    sessionChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['الأسبوع 1', 'الأسبوع 2', 'الأسبوع 3', 'الأسبوع 4'],
            datasets: [{
                label: 'نسبة الحضور والتفاعل %',
                data: [92, 95, 88, 96],
                backgroundColor: 'rgba(37, 99, 235, 0.85)',
                borderColor: '#2563eb',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
}

function printSlotProfile() {
    window.print();
}

function deleteSlotConfirm(id, event) {
    if (event) event.stopPropagation();

    Swal.fire({
        title: 'حذف الحصة من الجدول؟',
        text: 'لن تتمكن من استعادة بيانات الحصة المحددة بعد الحذف.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'نعم، احذف الحصة',
        cancelButtonText: 'إلغاء'
    }).then(res => {
        if (res.isConfirmed) {
            fetch(`/api/v1/timetable/${id}`, {
                method: 'DELETE',
                headers: window.apiHeadersJSON
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('تم حذف الحصة بنجاح', 'success');
                    fetchTimetableGridData();
                } else {
                    showToast(data.message || 'فشل الحذف', 'error');
                }
            })
            .catch(err => {
                console.error(err);
                showToast('حدث خطأ أثناء الاتصال بالخادم للحذف', 'error');
            });
        }
    });
}

/* ==========================================================================
   6. EXPORT ENGINES (EXCEL & PRINT/PDF)
   ========================================================================== */
function exportTimetableExcel() {
    if (timetableState.entries.length === 0) {
        showToast('لا توجد بيانات جدول حالية للتصدير', 'warning');
        return;
    }

    let csvContent = "data:text/csv;charset=utf-8,\uFEFF";
    csvContent += "اليوم,الحصة,المادة الدراسية,المعلم المسند,الصف,الشعبة\n";

    timetableState.entries.forEach(e => {
        csvContent += `"${e.DayName || ''}","${e.LessonName || ''}","${e.SubjectName || ''}","${e.TeacherName || ''}","${timetableState.currentClassId || ''}","${timetableState.currentSectionId || ''}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `timetable_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('تم تصدير الجدول بصيغة Excel بنجاح', 'success');
}

function exportTimetablePDF() {
    window.print();
}

/* ==========================================================================
   7. UI HELPERS & LISTENERS
   ========================================================================== */
function setupEventListeners() {
    const filterClassSelect = document.getElementById('filterClass');
    if (filterClassSelect) {
        filterClassSelect.addEventListener('change', function() {
            handleClassChange(this.value);
        });
    }

    const filterSectionSelect = document.getElementById('filterSection');
    if (filterSectionSelect) {
        filterSectionSelect.addEventListener('change', function() {
            fetchTimetableGridData();
        });
    }

    const filterTermSelect = document.getElementById('filterTerm');
    if (filterTermSelect) {
        filterTermSelect.addEventListener('change', function() {
            fetchTimetableGridData();
        });
    }

    const searchInput = document.getElementById('filterSearch');
    if (searchInput) searchInput.addEventListener('keyup', applyFiltersAndRender);

    const dayFilter = document.getElementById('filterDay');
    if (dayFilter) dayFilter.addEventListener('change', applyFiltersAndRender);

    const lessonFilter = document.getElementById('filterLesson');
    if (lessonFilter) lessonFilter.addEventListener('change', applyFiltersAndRender);

    const teacherFilter = document.getElementById('filterTeacher');
    if (teacherFilter) teacherFilter.addEventListener('change', applyFiltersAndRender);

    const subjectFilter = document.getElementById('filterSubject');
    if (subjectFilter) subjectFilter.addEventListener('change', applyFiltersAndRender);

    const resetBtn = document.getElementById('resetFiltersBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (dayFilter) dayFilter.value = '';
            if (lessonFilter) lessonFilter.value = '';
            if (teacherFilter) teacherFilter.value = '';
            if (subjectFilter) subjectFilter.value = '';
            applyFiltersAndRender();
            showToast('تم إعادة ضبط الفلاتر', 'info');
        });
    }

    const addClassSelect = document.getElementById('addSlotClassSelect');
    if (addClassSelect) {
        addClassSelect.addEventListener('change', function() {
            const classId = parseInt(this.value);
            const ref = timetableState.referenceData;
            const sectionSelect = document.getElementById('addSlotSectionSelect');
            const subjectSelect = document.getElementById('addSlotSubjectSelect');

            if (!sectionSelect || !ref) return;
            sectionSelect.innerHTML = '<option value="">اختر الشعبة</option>';
            if (subjectSelect) subjectSelect.innerHTML = '<option value="">اختر المادة</option>';

            const selectedClass = ref.classes.find(c => c.CID === classId);
            if (selectedClass) {
                if (selectedClass.sections) {
                    selectedClass.sections.forEach(s => {
                        sectionSelect.innerHTML += `<option value="${s.SectionID}">${s.SectionName}</option>`;
                    });
                }
                if (selectedClass.subjects) {
                    selectedClass.subjects.forEach(sub => {
                        subjectSelect.innerHTML += `<option value="${sub.SubID}">${sub.SubName}</option>`;
                    });
                }
            }
        });
    }

    const addSubjectSelect = document.getElementById('addSlotSubjectSelect');
    if (addSubjectSelect) {
        addSubjectSelect.addEventListener('change', function() {
            const subId = parseInt(this.value);
            const ref = timetableState.referenceData;
            const teacherSelect = document.getElementById('addSlotTeacherSelect');
            if (!teacherSelect || !ref) return;

            teacherSelect.innerHTML = '<option value="">اختر المعلم</option>';
            const matchingTeachers = ref.teachers.filter(t => t.subjects && t.subjects.includes(subId));
            
            if (matchingTeachers.length > 0) {
                matchingTeachers.forEach(t => {
                    teacherSelect.innerHTML += `<option value="${t.TeacherID}">${t.TeacherName}</option>`;
                });
            } else {
                ref.teachers.forEach(t => {
                    teacherSelect.innerHTML += `<option value="${t.TeacherID}">${t.TeacherName}</option>`;
                });
            }
        });
    }

    const addForm = document.getElementById('addSlotModalForm');
    if (addForm) addForm.addEventListener('submit', handleAddSlotFormSubmit);
}

function getSubjectColor(subId, dbColor) {
    if (dbColor && dbColor !== 'None' && dbColor !== '#e2e8f0') return dbColor;
    if (!subId) return 'linear-gradient(135deg, #475569, #334155)';
    const hue = (subId * 137.508) % 360;
    return `linear-gradient(135deg, hsl(${hue}, 70%, 45%), hsl(${hue}, 75%, 55%))`;
}

function showLoadingSpinner(show) {
    const spinner = document.getElementById('timetableLoadingSpinner');
    if (spinner) {
        if (show) spinner.classList.remove('d-none');
        else spinner.classList.add('d-none');
    }
}

function showEmptyState(show, customMessage = '') {
    const emptyContainer = document.getElementById('timetableEmptyState');
    const tableWrapper = document.getElementById('timetableTableContainer');
    const messageEl = document.getElementById('emptyStateMessage');

    if (show) {
        if (emptyContainer) emptyContainer.classList.remove('d-none');
        if (tableWrapper) tableWrapper.classList.add('d-none');
        if (messageEl && customMessage) messageEl.textContent = customMessage;
    } else {
        if (emptyContainer) emptyContainer.classList.add('d-none');
        if (tableWrapper) tableWrapper.content = '';
        if (tableWrapper) tableWrapper.classList.remove('d-none');
    }
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
