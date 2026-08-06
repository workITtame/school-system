document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Sidebar collapse toggle
    const sidebarCollapseBtn = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const appWrapper = document.querySelector('.app-wrapper');

    if (sidebarCollapseBtn && sidebar) {
        sidebarCollapseBtn.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            if (appWrapper) {
                appWrapper.classList.toggle('sidebar-collapsed');
            }
        });
    }

    // 3. Live search filter for today's schedule table
    const scheduleFilterInput = document.getElementById('scheduleFilterInput');
    const todayScheduleTable = document.getElementById('todayScheduleTable');

    if (scheduleFilterInput && todayScheduleTable) {
        scheduleFilterInput.addEventListener('keyup', function () {
            const filterValue = this.value.toLowerCase().trim();
            const rows = todayScheduleTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const textContent = row.textContent.toLowerCase();
                if (textContent.includes(filterValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

// 4. Open Student Side Drawer Offcanvas
function openStudentDrawer(studentId) {
    const drawerEl = document.getElementById('studentDetailDrawer');
    const drawerBody = document.getElementById('drawerBodyContent');
    if (!drawerEl || !drawerBody) return;

    const bsDrawer = bootstrap.Offcanvas.getOrCreateInstance(drawerEl);
    
    drawerBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
            <p class="extra-small text-muted mt-2">جاري جلب بيانات الطالب...</p>
        </div>
    `;
    bsDrawer.show();

    fetch(`/students/api/drawer/${studentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل جلب بيانات الطالب أو لا توجد صلاحيات.');
            }
            return response.json();
        })
        .then(data => {
            let marksHtml = '';
            if (data.recent_marks && data.recent_marks.length > 0) {
                marksHtml = data.recent_marks.map(m => `
                    <div class="d-flex align-items-center justify-content-between p-2 rounded bg-light mb-1 extra-small">
                        <span><i class="fa-solid fa-book text-primary me-1"></i> ${m.subject_name}</span>
                        <span class="font-monospace fw-bold text-dark">${m.score}%</span>
                    </div>
                `).join('');
            } else {
                marksHtml = '<p class="text-muted extra-small mb-0">لا توجد درجات مسجلة مؤخراً.</p>';
            }

            let attHtml = '';
            if (data.recent_attendance && data.recent_attendance.length > 0) {
                attHtml = data.recent_attendance.map(a => `
                    <span class="badge ${a.status === 'غائب' ? 'bg-danger-subtle text-danger' : 'bg-success-subtle text-success'} rounded-pill extra-small me-1 mb-1">
                        ${a.date}: ${a.status}
                    </span>
                `).join('');
            } else {
                attHtml = '<p class="text-muted extra-small mb-0">لا يوجد سجل غياب مؤخراً.</p>';
            }

            drawerBody.innerHTML = `
                <div class="text-center mb-4">
                    <div class="rounded-circle bg-primary text-white fw-bold font-monospace fs-1 d-inline-flex align-items-center justify-content-center shadow mb-2" style="width: 72px; height: 72px;">
                        ${data.student_name ? data.student_name[0] : 'ط'}
                    </div>
                    <h5 class="fw-bold text-dark mb-1">${data.student_name}</h5>
                    <p class="text-muted extra-small mb-0">الرقم الأكاديمي: <span class="font-monospace fw-bold">${data.academic_id}</span></p>
                    <span class="badge bg-light text-dark border rounded-pill mt-1 extra-small">${data.full_class}</span>
                </div>

                <div class="row g-2 mb-4 extra-small text-center">
                    <div class="col-6">
                        <div class="p-3 rounded-3 bg-light border">
                            <span class="text-muted d-block mb-1">نسبة الحضور</span>
                            <h5 class="fw-bold font-monospace text-primary mb-0">${data.attendance_rate}%</h5>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="p-3 rounded-3 bg-light border">
                            <span class="text-muted d-block mb-1">معدل الدرجات</span>
                            <h5 class="fw-bold font-monospace text-success mb-0">${data.avg_score}%</h5>
                        </div>
                    </div>
                </div>

                <div class="mb-4">
                    <h6 class="fw-bold text-dark mb-2 extra-small"><i class="fa-solid fa-star text-warning me-1"></i> آخر الدرجات المسجلة</h6>
                    ${marksHtml}
                </div>

                <div class="mb-4">
                    <h6 class="fw-bold text-dark mb-2 extra-small"><i class="fa-solid fa-user-clock text-info me-1"></i> آخر سجل الحضور والغياب</h6>
                    <div>${attHtml}</div>
                </div>

                <div class="mb-4 p-3 rounded-3 bg-light border extra-small">
                    <strong class="d-block text-dark mb-1"><i class="fa-solid fa-user-shield me-1"></i> ولي الأمر: ${data.parent_name}</strong>
                    <small class="text-muted d-block font-monospace"><i class="fa-solid fa-phone me-1"></i> ${data.parent_number}</small>
                    <hr class="my-2">
                    <p class="text-secondary mb-0"><i class="fa-regular fa-comment-dots me-1"></i> ${data.notes}</p>
                </div>

                <div class="d-grid gap-2 extra-small">
                    <a href="/attendance/" class="btn btn-sm btn-primary rounded-pill py-2">
                        <i class="fa-solid fa-clipboard-user me-1"></i> تسجيل حضور الطالب
                    </a>
                    <a href="/grades/manage" class="btn btn-sm btn-outline-secondary rounded-pill py-2">
                        <i class="fa-solid fa-pen-to-square me-1"></i> إدخال درجات الطالب
                    </a>
                    <a href="/messages/" class="btn btn-sm btn-outline-info rounded-pill py-2">
                        <i class="fa-regular fa-paper-plane me-1"></i> إرسال رسالة لولي الأمر
                    </a>
                </div>
            `;
        })
        .catch(err => {
            drawerBody.innerHTML = `
                <div class="text-center py-5 text-danger extra-small">
                    <i class="fa-solid fa-circle-exclamation fs-1 d-block mb-2"></i>
                    <h6 class="fw-bold">حدث خطأ أثناء جلب ملف الطالب</h6>
                    <p class="text-muted mb-0">${err.message}</p>
                </div>
            `;
        });
}

// 5. Open Enterprise Lesson Workspace Shell Drawer Offcanvas
function openLessonDrawer(slotId) {
    const drawerEl = document.getElementById('lessonDetailDrawer');
    const drawerBody = document.getElementById('lessonDrawerBodyContent');
    if (!drawerEl || !drawerBody) return;

    const bsDrawer = bootstrap.Offcanvas.getOrCreateInstance(drawerEl);
    
    drawerBody.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
            <p class="extra-small text-muted mt-2">جاري تحميل مساحة عمل الحصة الموحدة...</p>
        </div>
    `;
    bsDrawer.show();

    fetch(`/timetable/api/drawer/${slotId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل تحميل مساحة عمل الحصة أو لا توجد صلاحيات.');
            }
            return response.json();
        })
        .then(data => {
            // Build Status Badge HTML
            let statusBadgeHtml = '';
            if (data.status_code === 'current') {
                statusBadgeHtml = '<span class="badge bg-success text-white rounded-pill px-3 py-1 extra-small"><i class="fa-solid fa-spinner fa-spin me-1"></i> جارية الآن</span>';
            } else if (data.status_code === 'ended') {
                statusBadgeHtml = '<span class="badge bg-secondary text-white rounded-pill px-3 py-1 extra-small"><i class="fa-regular fa-circle-check me-1"></i> منتهية</span>';
            } else {
                statusBadgeHtml = '<span class="badge bg-info text-white rounded-pill px-3 py-1 extra-small"><i class="fa-regular fa-clock me-1"></i> قادمة</span>';
            }

            // Build Students List HTML for Students Tab
            let studentsListHtml = '';
            if (data.students && data.students.length > 0) {
                studentsListHtml = data.students.map(s => `
                    <div class="card rounded-3 border-0 bg-light p-2 mb-2 student-workspace-item">
                        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                            <div class="d-flex align-items-center gap-2">
                                <div class="rounded-circle bg-primary-subtle text-primary fw-bold font-monospace d-flex align-items-center justify-content-center flex-shrink-0" style="width: 36px; height: 36px;">
                                    ${s.SName ? s.SName[0] : 'ط'}
                                </div>
                                <div>
                                    <strong class="text-dark d-block extra-small mb-0">${s.SName}</strong>
                                    <small class="text-muted font-monospace extra-small">الرقم الأكاديمي: ${s.academic_id}</small>
                                </div>
                            </div>
                            <div class="d-flex align-items-center gap-2 flex-wrap extra-small">
                                <span class="badge ${s.attendance_status === 'حاضر' ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-danger-subtle text-danger border border-danger-subtle'} rounded-pill">
                                    ${s.attendance_status}
                                </span>
                                <span class="badge bg-white text-dark border font-monospace">درجة: ${s.latest_score}%</span>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-light border rounded-circle extra-small p-1" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="إجراءات الطالب">
                                        <i class="fa-solid fa-ellipsis-vertical text-muted"></i>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-end shadow border-0 rounded-3 extra-small font-cairo">
                                        <li>
                                            <button class="dropdown-item py-1" type="button" onclick="alert('تسجيل حضور الطالب: ${s.SName}')">
                                                <i class="fa-solid fa-clipboard-user text-warning me-2"></i> تسجيل حضور
                                            </button>
                                        </li>
                                        <li>
                                            <button class="dropdown-item py-1" type="button" onclick="alert('إدخال درجة الطالب: ${s.SName}')">
                                                <i class="fa-solid fa-star text-warning me-2"></i> إدخال درجة
                                            </button>
                                        </li>
                                        <li>
                                            <button class="dropdown-item py-1" type="button" onclick="alert('إرسال رسالة للطالب: ${s.SName}')">
                                                <i class="fa-regular fa-paper-plane text-info me-2"></i> إرسال رسالة
                                            </button>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                studentsListHtml = `
                    <div class="py-4 text-center text-muted extra-small">
                        <i class="fa-solid fa-users-slash text-primary opacity-25 fs-1 d-block mb-2"></i>
                        <p class="mb-0">لا يوجد طلاب مسجلون بهذه الحصة حالياً.</p>
                    </div>
                `;
            }

            // Helper macro for Coming Soon tabs empty state
            const renderComingSoonTab = (iconClass, title, moduleName) => `
                <div class="card rounded-4 border-0 bg-light py-5 px-3 text-center my-3">
                    <i class="${iconClass} text-primary opacity-25 fs-1 d-block mb-3"></i>
                    <h6 class="fw-bold text-dark mb-1 extra-small">${title}</h6>
                    <p class="text-muted extra-small max-w-sm mx-auto mb-3">سيتم تفعيل قسم ${moduleName} المباشر للحصة وتطويره بالكامل في المرحلة القادمة.</p>
                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill max-w-fit mx-auto px-3 py-2 extra-small">
                        <i class="fa-solid fa-wand-magic-sparkles me-1"></i> قريباً في المرحلة القادمة (Coming Soon)
                    </span>
                </div>
            `;

            drawerBody.innerHTML = `
                <!-- WORKSPACE HEADER -->
                <div class="p-3 rounded-4 bg-primary-subtle border border-primary-subtle mb-3">
                    <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-2">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-primary text-white rounded-pill px-3 py-1 font-cairo extra-small">
                                📚 ${data.subject_name}
                            </span>
                            ${statusBadgeHtml}
                        </div>
                        <small class="text-muted font-monospace extra-small">
                            <i class="fa-regular fa-clock text-primary me-1"></i> ${data.start_time} - ${data.end_time}
                        </small>
                    </div>
                    <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                        <h6 class="fw-bold text-dark mb-0 font-cairo">🏫 ${data.full_class}</h6>
                        <small class="text-secondary extra-small fw-bold"><i class="fa-solid fa-users text-success me-1"></i> ${data.total_students} طلاب مسجلون</small>
                    </div>
                </div>

                <!-- QUICK STATISTICS BAR (5 KPI Cards) -->
                <div class="row g-2 mb-3 extra-small text-center">
                    <div class="col-4">
                        <div class="p-2 rounded-3 bg-light border">
                            <span class="text-muted d-block extra-small">الطلاب</span>
                            <strong class="font-monospace text-dark fs-6">${data.total_students}</strong>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded-3 bg-light border">
                            <span class="text-muted d-block extra-small">الحاضرون</span>
                            <strong class="font-monospace text-success fs-6">${data.present_count}</strong>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded-3 bg-light border">
                            <span class="text-muted d-block extra-small">الغائبون</span>
                            <strong class="font-monospace text-danger fs-6">${data.absent_count}</strong>
                        </div>
                    </div>
                </div>

                <!-- WORKSPACE NAVIGATION (7 TABS) -->
                <ul class="nav nav-tabs nav-tabs-workspace mb-3 extra-small font-cairo" id="workspaceTab" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active rounded-pill px-3 py-1 me-1" id="ws-students-tab" data-bs-toggle="tab" data-bs-target="#ws-students" type="button" role="tab" aria-controls="ws-students" aria-selected="true">
                            <i class="fa-solid fa-users me-1 text-primary"></i> الطلاب (${data.total_students})
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1 me-1" id="ws-attendance-tab" data-bs-toggle="tab" data-bs-target="#ws-attendance" type="button" role="tab" aria-controls="ws-attendance" aria-selected="false">
                            <i class="fa-solid fa-clipboard-user me-1 text-warning"></i> الحضور
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1 me-1" id="ws-grades-tab" data-bs-toggle="tab" data-bs-target="#ws-grades" type="button" role="tab" aria-controls="ws-grades" aria-selected="false">
                            <i class="fa-solid fa-star me-1 text-warning"></i> الدرجات
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1 me-1" id="ws-homework-tab" data-bs-toggle="tab" data-bs-target="#ws-homework" type="button" role="tab" aria-controls="ws-homework" aria-selected="false">
                            <i class="fa-solid fa-book-open me-1 text-info"></i> الواجبات
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1 me-1" id="ws-exams-tab" data-bs-toggle="tab" data-bs-target="#ws-exams" type="button" role="tab" aria-controls="ws-exams" aria-selected="false">
                            <i class="fa-solid fa-file-signature me-1 text-danger"></i> الاختبارات
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1 me-1" id="ws-messages-tab" data-bs-toggle="tab" data-bs-target="#ws-messages" type="button" role="tab" aria-controls="ws-messages" aria-selected="false">
                            <i class="fa-regular fa-paper-plane me-1 text-info"></i> الرسائل
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-3 py-1" id="ws-notes-tab" data-bs-toggle="tab" data-bs-target="#ws-notes" type="button" role="tab" aria-controls="ws-notes" aria-selected="false">
                            <i class="fa-regular fa-note-sticky me-1 text-secondary"></i> الملاحظات
                        </button>
                    </li>
                </ul>

                <!-- TAB PANELS CONTENT CONTAINER -->
                <div class="tab-content" id="workspaceTabContent">

                    <!-- 1. STUDENTS TAB (FULLY FUNCTIONAL) -->
                    <div class="tab-pane fade show active" id="ws-students" role="tabpanel" aria-labelledby="ws-students-tab">
                        <div class="mb-2">
                            <input type="text" id="workspaceStudentSearch" class="form-control form-control-sm rounded-pill extra-small" placeholder="بحث باسم الطالب أو الرقم الأكاديمي..." onkeyup="filterWorkspaceStudents(this.value)">
                        </div>
                        <div id="workspaceStudentsListContainer" style="max-height: 360px; overflow-y: auto;">
                            ${studentsListHtml}
                        </div>
                    </div>

                    <!-- 2. ATTENDANCE TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-attendance" role="tabpanel" aria-labelledby="ws-attendance-tab">
                        ${renderComingSoonTab("fa-solid fa-clipboard-user", "وحدة تسجيل الحضور المباشر للحصة", "الحضور والغياب")}
                    </div>

                    <!-- 3. GRADES TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-grades" role="tabpanel" aria-labelledby="ws-grades-tab">
                        ${renderComingSoonTab("fa-solid fa-star", "وحدة إدخال وتتبع درجات الحصة", "الدرجات والتقييمات")}
                    </div>

                    <!-- 4. HOMEWORK TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-homework" role="tabpanel" aria-labelledby="ws-homework-tab">
                        ${renderComingSoonTab("fa-solid fa-book-open", "وحدة متابعة وإضافة واجبات الحصة", "الواجبات التفاعلية")}
                    </div>

                    <!-- 5. EXAMS TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-exams" role="tabpanel" aria-labelledby="ws-exams-tab">
                        ${renderComingSoonTab("fa-solid fa-file-signature", "وحدة اختبارات وتقييمات الحصة", "الاختبارات الأكاديمية")}
                    </div>

                    <!-- 6. MESSAGES TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-messages" role="tabpanel" aria-labelledby="ws-messages-tab">
                        ${renderComingSoonTab("fa-regular fa-paper-plane", "وحدة الرسائل والتنبيهات المباشرة", "الرسائل والإشعارات")}
                    </div>

                    <!-- 7. NOTES TAB (COMING SOON EMPTY STATE) -->
                    <div class="tab-pane fade" id="ws-notes" role="tabpanel" aria-labelledby="ws-notes-tab">
                        ${renderComingSoonTab("fa-regular fa-note-sticky", "وحدة ملاحظات وتحضير الحصة", "الملاحظات الأكاديمية")}
                    </div>

                </div>
            `;
        })
        .catch(err => {
            drawerBody.innerHTML = `
                <div class="text-center py-5 text-danger extra-small">
                    <i class="fa-solid fa-circle-exclamation fs-1 d-block mb-2"></i>
                    <h6 class="fw-bold">حدث خطأ أثناء تحميل مساحة عمل الحصة</h6>
                    <p class="text-muted mb-0">${err.message}</p>
                </div>
            `;
        });
}

// 6. Timetable View Switcher (Today Timeline vs Weekly Calendar)
function switchTimetableTab(viewMode) {
    const todayTab = document.getElementById('todayTimelineView');
    const weekTab = document.getElementById('weeklyCalendarView');
    if (todayTab && weekTab) {
        if (viewMode === 'today') {
            todayTab.classList.add('show', 'active');
            weekTab.classList.remove('show', 'active');
        } else {
            weekTab.classList.add('show', 'active');
            todayTab.classList.remove('show', 'active');
        }
    }
}

// 7. Bulk selection & Floating toolbar functions
function toggleSelectAllStudents(source) {
    const checkboxes = document.querySelectorAll('.student-select-checkbox');
    checkboxes.forEach(cb => cb.checked = source.checked);
    updateBulkToolbar();
}

function updateBulkToolbar() {
    const checkboxes = document.querySelectorAll('.student-select-checkbox:checked');
    const toolbar = document.getElementById('bulkActionsToolbar');
    const countEl = document.getElementById('selectedStudentsCount');
    
    if (toolbar && countEl) {
        if (checkboxes.length > 0) {
            countEl.textContent = checkboxes.length;
            toolbar.classList.remove('d-none');
        } else {
            toolbar.classList.add('d-none');
        }
    }
}

function clearBulkSelection() {
    const checkboxes = document.querySelectorAll('.student-select-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAllStudents');
    if (selectAll) selectAll.checked = false;
    updateBulkToolbar();
}

function bulkSendMessage() {
    const checkboxes = document.querySelectorAll('.student-select-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);
    if (ids.length === 0) return;
    alert(`سيتم توجيهك إلى صفحة الرسائل لإرسال رسالة جماعية لـ ${ids.length} طلاب.`);
    window.location.href = `/messages/?recipients=${ids.join(',')}`;
}
