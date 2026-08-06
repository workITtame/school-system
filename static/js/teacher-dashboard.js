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

            // Store current lesson slot data globally for Attendance Module
            window.currentLessonWorkspaceData = data;
            window.lessonAttendanceState = {};
            window.hasUnsavedAttendanceChanges = false;

            if (data.students) {
                data.students.forEach(s => {
                    window.lessonAttendanceState[s.SID] = s.attendance_status || 'غير مسجل';
                });
            }

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

                    <!-- 2. ATTENDANCE TAB (FULLY FUNCTIONAL ENTERPRISE MODULE) -->
                    <div class="tab-pane fade" id="ws-attendance" role="tabpanel" aria-labelledby="ws-attendance-tab">
                        <div id="attendanceModuleContainer">
                            <!-- Attendance Module populated dynamically -->
                        </div>
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
            // Initialize Attendance Module inside Tab
            renderWorkspaceAttendanceTab();
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

// Render Attendance Module Tab Content
function renderWorkspaceAttendanceTab() {
    const container = document.getElementById('attendanceModuleContainer');
    if (!container || !window.currentLessonWorkspaceData) return;

    const data = window.currentLessonWorkspaceData;
    const students = data.students || [];
    const state = window.lessonAttendanceState || {};

    // Calculate dynamic stats from local client state
    let present = 0, absent = 0, late = 0, excused = 0, unregistered = 0;
    students.forEach(s => {
        const st = state[s.SID] || 'غير مسجل';
        if (st === 'حاضر') present++;
        elif_check: if (st === 'غائب') absent++;
        else if (st === 'متأخر') late++;
        else if (st === 'بعذر') excused++;
        else unregistered++;
    });

    const hasUnsaved = window.hasUnsavedAttendanceChanges;

    let studentsRowsHtml = '';
    if (students.length > 0) {
        studentsRowsHtml = students.map(s => {
            const currentSt = state[s.SID] || 'غير مسجل';

            const chipClass = (stName) => {
                return currentSt === stName ? 'btn-primary active fw-bold shadow-sm' : 'btn-outline-secondary';
            };

            return `
                <div class="card rounded-3 border-0 bg-light p-2 mb-2 att-student-item">
                    <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                        <div class="d-flex align-items-center gap-2">
                            <div class="rounded-circle bg-primary-subtle text-primary fw-bold font-monospace d-flex align-items-center justify-content-center flex-shrink-0" style="width: 34px; height: 34px;">
                                ${s.SName ? s.SName[0] : 'ط'}
                            </div>
                            <div>
                                <strong class="text-dark d-block extra-small mb-0">${s.SName}</strong>
                                <small class="text-muted font-monospace extra-small">${s.academic_id}</small>
                            </div>
                        </div>
                        
                        <!-- Status Chips Toggle -->
                        <div class="btn-group btn-group-sm extra-small font-cairo" role="group" aria-label="تحديد حالة الحضور">
                            <button type="button" class="btn ${currentSt === 'حاضر' ? 'btn-success text-white fw-bold' : 'btn-outline-success'} extra-small py-1 px-2" onclick="setStudentAttendanceStatus(${s.SID}, 'حاضر')">🟢 حاضر</button>
                            <button type="button" class="btn ${currentSt === 'غائب' ? 'btn-danger text-white fw-bold' : 'btn-outline-danger'} extra-small py-1 px-2" onclick="setStudentAttendanceStatus(${s.SID}, 'غائب')">🔴 غائب</button>
                            <button type="button" class="btn ${currentSt === 'متأخر' ? 'btn-warning text-dark fw-bold' : 'btn-outline-warning'} extra-small py-1 px-2" onclick="setStudentAttendanceStatus(${s.SID}, 'متأخر')">🟡 متأخر</button>
                            <button type="button" class="btn ${currentSt === 'بعذر' ? 'btn-info text-white fw-bold' : 'btn-outline-info'} extra-small py-1 px-2" onclick="setStudentAttendanceStatus(${s.SID}, 'بعذر')">🔵 بعذر</button>
                            <button type="button" class="btn ${currentSt === 'غير مسجل' ? 'btn-secondary text-white fw-bold' : 'btn-outline-secondary'} extra-small py-1 px-2" onclick="setStudentAttendanceStatus(${s.SID}, 'غير مسجل')">⚪ غير مسجل</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        studentsRowsHtml = `
            <div class="py-4 text-center text-muted extra-small">
                <i class="fa-solid fa-users-slash text-primary opacity-25 fs-1 d-block mb-2"></i>
                <p class="mb-0">لا يوجد طلاب مسجلون بهذه الحصة.</p>
            </div>
        `;
    }

    container.innerHTML = `
        <!-- UNSAVED CHANGES BANNER -->
        ${hasUnsaved ? `
            <div class="alert alert-warning border-warning d-flex align-items-center justify-content-between p-2 mb-3 rounded-3 extra-small">
                <span><i class="fa-solid fa-triangle-exclamation me-1"></i> لديك تغييرات غير محفوظة في سجل الحضور!</span>
                <button type="button" class="btn btn-sm btn-warning text-dark fw-bold rounded-pill extra-small px-3" onclick="saveLessonAttendanceBulk(${data.slot_id})">
                    <i class="fa-solid fa-floppy-disk me-1"></i> حفظ الآن
                </button>
            </div>
        ` : ''}

        <!-- SUMMARY METRICS BAR -->
        <div class="row g-2 mb-3 extra-small text-center">
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-muted d-block extra-small">الكل</span>
                    <strong class="font-monospace text-dark fs-6">${students.length}</strong>
                </div>
            </div>
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-success d-block extra-small">🟢 حاضر</span>
                    <strong class="font-monospace text-success fs-6">${present}</strong>
                </div>
            </div>
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-danger d-block extra-small">🔴 غائب</span>
                    <strong class="font-monospace text-danger fs-6">${absent}</strong>
                </div>
            </div>
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-warning d-block extra-small">🟡 متأخر</span>
                    <strong class="font-monospace text-warning fs-6">${late}</strong>
                </div>
            </div>
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-info d-block extra-small">🔵 بعذر</span>
                    <strong class="font-monospace text-info fs-6">${excused}</strong>
                </div>
            </div>
            <div class="col-4 col-sm-2">
                <div class="p-2 rounded bg-light border">
                    <span class="text-secondary d-block extra-small">⚪ غير مسجل</span>
                    <strong class="font-monospace text-secondary fs-6">${unregistered}</strong>
                </div>
            </div>
        </div>

        <!-- BULK ACTIONS & SEARCH TOOLBAR -->
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3 extra-small">
            <div class="d-flex align-items-center gap-1 flex-wrap">
                <button type="button" class="btn btn-sm btn-outline-success rounded-pill px-2 py-1 extra-small" onclick="markAllAttendanceBulk('حاضر')">
                    تحديد الجميع حاضر
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger rounded-pill px-2 py-1 extra-small" onclick="markAllAttendanceBulk('غائب')">
                    تحديد الجميع غائب
                </button>
                <button type="button" class="btn btn-sm btn-outline-warning rounded-pill px-2 py-1 extra-small" onclick="markAllAttendanceBulk('متأخر')">
                    تحديد الجميع متأخر
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill px-2 py-1 extra-small" onclick="markAllAttendanceBulk('غير مسجل')">
                    إعادة تعيين
                </button>
            </div>
            <button type="button" id="saveAttendanceBtn" class="btn btn-sm btn-primary rounded-pill px-4 py-1 extra-small fw-bold shadow-sm" onclick="saveLessonAttendanceBulk(${data.slot_id})">
                <i class="fa-solid fa-floppy-disk me-1"></i> حفظ سجل الحضور
            </button>
        </div>

        <!-- SEARCH INPUT -->
        <div class="mb-2">
            <input type="text" class="form-control form-control-sm rounded-pill extra-small" placeholder="بحث باسم الطالب أو الرقم الأكاديمي..." onkeyup="filterAttendanceStudents(this.value)">
        </div>

        <!-- STUDENTS ATTENDANCE ROSTER -->
        <div id="attendanceStudentsListContainer" style="max-height: 340px; overflow-y: auto;">
            ${studentsRowsHtml}
        </div>
    `;
}

// Set individual student status
function setStudentAttendanceStatus(studentId, newStatus) {
    if (!window.lessonAttendanceState) window.lessonAttendanceState = {};
    window.lessonAttendanceState[studentId] = newStatus;
    window.hasUnsavedAttendanceChanges = true;
    renderWorkspaceAttendanceTab();
}

// Bulk mark all students
function markAllAttendanceBulk(status) {
    if (!window.currentLessonWorkspaceData) return;
    const students = window.currentLessonWorkspaceData.students || [];
    students.forEach(s => {
        window.lessonAttendanceState[s.SID] = status;
    });
    window.hasUnsavedAttendanceChanges = true;
    renderWorkspaceAttendanceTab();
}

// Filter attendance students roster
function filterAttendanceStudents(query) {
    const filter = query.toLowerCase().trim();
    const items = document.querySelectorAll('.att-student-item');
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(filter)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// Global state for Standalone Attendance Page
window.pageAttendanceEdits = {};
window.pageAttendanceUnsavedCount = 0;

function setPageStudentAttendance(sid, newStatus) {
    window.pageAttendanceEdits[sid] = newStatus;
    
    const rowEl = document.getElementById(`page-att-row-${sid}`);
    if (rowEl) {
        rowEl.classList.add('modified-row');
        rowEl.setAttribute('data-current-status', newStatus);
        
        const buttons = rowEl.querySelectorAll('.btn-att-chip');
        buttons.forEach(btn => {
            btn.className = 'btn btn-att-chip extra-small py-1 px-3 rounded-pill btn-outline-secondary';
            if (btn.textContent.includes(newStatus)) {
                if (newStatus === 'حاضر') btn.className = 'btn btn-att-chip extra-small py-1 px-3 rounded-pill btn-success text-white fw-bold';
                else if (newStatus === 'غائب') btn.className = 'btn btn-att-chip extra-small py-1 px-3 rounded-pill btn-danger text-white fw-bold';
                else if (newStatus === 'متأخر') btn.className = 'btn btn-att-chip extra-small py-1 px-3 rounded-pill btn-warning text-dark fw-bold';
                else if (newStatus === 'بعذر' || newStatus === 'مستأذن') btn.className = 'btn btn-att-chip extra-small py-1 px-3 rounded-pill btn-info text-white fw-bold';
            }
        });
    }

    window.pageAttendanceUnsavedCount = Object.keys(window.pageAttendanceEdits).length;
    updateStickySaveBarLabel();
    recalculatePageAttendanceMetrics();
}

function recalculatePageAttendanceMetrics() {
    const rows = document.querySelectorAll('.page-att-row');
    const total = rows.length;
    if (total === 0) return;

    let present = 0, absent = 0, late = 0, excused = 0;
    rows.forEach(r => {
        let st = r.getAttribute('data-current-status');
        if (!st) {
            const activeBtn = r.querySelector('.btn-att-chip.fw-bold');
            if (activeBtn) {
                if (activeBtn.textContent.includes('حاضر')) st = 'حاضر';
                else if (activeBtn.textContent.includes('غائب')) st = 'غائب';
                else if (activeBtn.textContent.includes('متأخر')) st = 'متأخر';
                else if (activeBtn.textContent.includes('بعذر')) st = 'بعذر';
            }
        }
        if (st === 'حاضر') present++;
        else if (st === 'غائب') absent++;
        else if (st === 'متأخر') late++;
        else if (st === 'بعذر' || st === 'مستأذن') excused++;
    });

    const pRate = (present / total * 100).toFixed(1);
    const aRate = (absent / total * 100).toFixed(1);
    const lRate = (late / total * 100).toFixed(1);
    const eRate = (excused / total * 100).toFixed(1);

    // Update Progress Bars UI
    const elP = document.getElementById('barPresentPercent');
    const elPF = document.getElementById('barPresentFill');
    if (elP) elP.textContent = `${pRate}%`;
    if (elPF) elPF.style.width = `${pRate}%`;

    const elA = document.getElementById('barAbsentPercent');
    const elAF = document.getElementById('barAbsentFill');
    if (elA) elA.textContent = `${aRate}%`;
    if (elAF) elAF.style.width = `${aRate}%`;

    const elL = document.getElementById('barLatePercent');
    const elLF = document.getElementById('barLateFill');
    if (elL) elL.textContent = `${lRate}%`;
    if (elLF) elLF.style.width = `${lRate}%`;

    const elE = document.getElementById('barExcusedPercent');
    const elEF = document.getElementById('barExcusedFill');
    if (elE) elE.textContent = `${eRate}%`;
    if (elEF) elEF.style.width = `${eRate}%`;
}

function updateStickySaveBarLabel() {
    const btnLabel = document.getElementById('stickySaveBtnLabel');
    const saveBtn = document.getElementById('stickyPageSaveBtn');
    const count = window.pageAttendanceUnsavedCount;
    
    if (btnLabel) {
        if (count > 0) {
            btnLabel.textContent = `حفظ سجل الحضور (${count})`;
            if (saveBtn) {
                saveBtn.className = 'btn btn-sm btn-warning text-dark rounded-pill px-4 py-2 fw-bold shadow-sm extra-small';
            }
        } else {
            btnLabel.textContent = 'حفظ سجل الحضور';
            if (saveBtn) {
                saveBtn.className = 'btn btn-sm btn-primary rounded-pill px-4 py-2 fw-bold shadow-sm extra-small';
            }
        }
    }
}

function filterPageAttendanceList(query) {
    const filter = query.toLowerCase().trim();
    const rows = document.querySelectorAll('.page-att-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    const counterEl = document.getElementById('attendanceResultsCounter');
    if (counterEl) {
        counterEl.textContent = `عرض ${visibleCount} من أصل ${rows.length} طالباً`;
    }
}

function filterPageAttendanceByStatus(status) {
    const filter = status.trim();
    const rows = document.querySelectorAll('.page-att-row');
    let visibleCount = 0;

    rows.forEach(row => {
        if (!filter || row.textContent.includes(filter)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    const counterEl = document.getElementById('attendanceResultsCounter');
    if (counterEl) {
        counterEl.textContent = `عرض ${visibleCount} من أصل ${rows.length} طالباً`;
    }
}

function markAllAttendancePage(status) {
    const rows = document.querySelectorAll('.page-att-row');
    rows.forEach(row => {
        const sid = row.getAttribute('data-sid');
        if (sid) {
            setPageStudentAttendance(parseInt(sid), status);
        }
    });
}

function savePageAttendanceBulk(slotId) {
    const saveBtn = document.getElementById('stickyPageSaveBtn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> جاري الحفظ...';
    }

    const edits = window.pageAttendanceEdits || {};
    let attendancePayload = Object.keys(edits).map(sid => ({
        student_id: parseInt(sid),
        status: edits[sid]
    }));

    if (attendancePayload.length === 0) {
        const rows = document.querySelectorAll('.page-att-row');
        rows.forEach(r => {
            const sid = r.getAttribute('data-sid');
            const activeBtn = r.querySelector('.btn-att-chip.fw-bold');
            if (sid && activeBtn) {
                let st = 'غير مسجل';
                if (activeBtn.textContent.includes('حاضر')) st = 'حاضر';
                else if (activeBtn.textContent.includes('غائب')) st = 'غائب';
                else if (activeBtn.textContent.includes('متأخر')) st = 'متأخر';
                else if (activeBtn.textContent.includes('بعذر')) st = 'بعذر';
                attendancePayload.push({ student_id: parseInt(sid), status: st });
            }
        });
    }

    fetch('/attendance/api/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            slot_id: slotId || 1,
            attendance: attendancePayload
        })
    })
    .then(res => {
        if (!res.ok) throw new Error('فشل حفظ التعديلات.');
        return res.json();
    })
    .then(resData => {
        window.pageAttendanceEdits = {};
        window.pageAttendanceUnsavedCount = 0;
        
        document.querySelectorAll('.page-att-row').forEach(r => r.classList.remove('modified-row'));
        
        const now = new Date();
        const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        const indicator = document.getElementById('lastSaveTimeIndicator');
        if (indicator) indicator.textContent = timeStr;

        if (saveBtn) {
            saveBtn.disabled = false;
            updateStickySaveBarLabel();
        }
        alert('✅ تم حفظ سجل الحضور والغياب بنجاح في قاعدة البيانات!');
    })
    .catch(err => {
        alert('❌ حدث خطأ أثناء الحفظ: ' + err.message);
        if (saveBtn) {
            saveBtn.disabled = false;
            updateStickySaveBarLabel();
        }
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

// Explicitly expose functions to global window object for reliable inline event invocation
window.openLessonDrawer = openLessonDrawer;
window.setPageStudentAttendance = setPageStudentAttendance;
window.updateStickySaveBarLabel = updateStickySaveBarLabel;
window.filterPageAttendanceList = filterPageAttendanceList;
window.filterPageAttendanceByStatus = filterPageAttendanceByStatus;
window.markAllAttendancePage = markAllAttendancePage;
window.savePageAttendanceBulk = savePageAttendanceBulk;
window.setStudentAttendanceStatus = setStudentAttendanceStatus;
window.markAllAttendanceBulk = markAllAttendanceBulk;
window.saveLessonAttendanceBulk = saveLessonAttendanceBulk;
window.switchTimetableTab = switchTimetableTab;
window.toggleSelectAllStudents = toggleSelectAllStudents;
window.updateBulkToolbar = updateBulkToolbar;
window.clearBulkSelection = clearBulkSelection;
window.bulkSendMessage = bulkSendMessage;

// Document-level event delegation to guarantee 100% button execution across all browsers & Turbo page transitions
document.addEventListener('click', function (e) {
    const target = e.target.closest('[data-action], .btn-att-chip, [data-bs-toggle="dropdown"], .dropdown-toggle');
    if (!target) return;

    const action = target.getAttribute('data-action');

    if (action === 'open-lesson-drawer' || (target.getAttribute('onclick') && target.getAttribute('onclick').includes('openLessonDrawer'))) {
        const slotId = target.getAttribute('data-slot-id') || 1;
        if (window.openLessonDrawer) {
            window.openLessonDrawer(parseInt(slotId));
        }
    }
    else if (action === 'set-status') {
        const sid = target.getAttribute('data-sid');
        const status = target.getAttribute('data-status');
        if (sid && status && window.setPageStudentAttendance) {
            window.setPageStudentAttendance(parseInt(sid), status);
        }
    }
    else if (action === 'save-attendance' || target.id === 'stickyPageSaveBtn') {
        const slotId = target.getAttribute('data-slot-id') || 1;
        if (window.savePageAttendanceBulk) {
            window.savePageAttendanceBulk(parseInt(slotId));
        }
    }
    else if (target.matches('[data-bs-toggle="dropdown"], .dropdown-toggle')) {
        if (window.bootstrap && window.bootstrap.Dropdown) {
            const dropdown = window.bootstrap.Dropdown.getOrCreateInstance(target);
            dropdown.toggle();
        }
    }
});
