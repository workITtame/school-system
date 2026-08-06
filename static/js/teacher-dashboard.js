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

// 5. Open Lesson Workspace Side Drawer Offcanvas
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
            <p class="extra-small text-muted mt-2">جاري تجهيز مساحة عمل الحصة...</p>
        </div>
    `;
    bsDrawer.show();

    fetch(`/timetable/api/drawer/${slotId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل تحميل مساحة الحصة أو لا توجد صلاحيات.');
            }
            return response.json();
        })
        .then(data => {
            let studentsHtml = '';
            if (data.students && data.students.length > 0) {
                studentsHtml = data.students.map(s => `
                    <div class="d-flex align-items-center justify-content-between p-2 rounded bg-light mb-1 extra-small">
                        <span><i class="fa-solid fa-user-graduate text-primary me-1"></i> ${s.SName}</span>
                        <span class="badge bg-success-subtle text-success rounded-pill extra-small">حاضر</span>
                    </div>
                `).join('');
            } else {
                studentsHtml = '<p class="text-muted extra-small mb-0">لا يوجد طلاب مسجلون بهذه الشعبة.</p>';
            }

            drawerBody.innerHTML = `
                <div class="text-center mb-4">
                    <div class="rounded-circle bg-primary-subtle text-primary fw-bold font-monospace fs-2 d-inline-flex align-items-center justify-content-center shadow-sm mb-2" style="width: 64px; height: 64px;">
                        <i class="fa-solid fa-chalkboard-user"></i>
                    </div>
                    <h5 class="fw-bold text-dark mb-1">${data.subject_name}</h5>
                    <span class="badge bg-light text-dark border rounded-pill extra-small">${data.full_class}</span>
                    <p class="text-muted extra-small mt-2 mb-0"><i class="fa-regular fa-clock text-primary me-1"></i> التوقيت: <span class="font-monospace fw-bold">${data.start_time} - ${data.end_time}</span></p>
                </div>

                <!-- Lesson Performance Summary -->
                <div class="row g-2 mb-4 extra-small text-center">
                    <div class="col-4">
                        <div class="p-2 rounded bg-light border">
                            <span class="text-muted d-block extra-small">عدد الطلاب</span>
                            <strong class="font-monospace fs-6 text-dark">${data.total_students}</strong>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded bg-light border">
                            <span class="text-muted d-block extra-small">الحاضرون</span>
                            <strong class="font-monospace fs-6 text-success">${data.present_count}</strong>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded bg-light border">
                            <span class="text-muted d-block extra-small">المتغيبون</span>
                            <strong class="font-monospace fs-6 text-danger">${data.absent_count}</strong>
                        </div>
                    </div>
                </div>

                <!-- Enrolled Students Roster -->
                <div class="mb-4">
                    <h6 class="fw-bold text-dark mb-2 extra-small"><i class="fa-solid fa-users text-primary me-1"></i> قائمة طلاب الحصة</h6>
                    <div style="max-height: 180px; overflow-y: auto;">${studentsHtml}</div>
                </div>

                <!-- Quick Action Buttons -->
                <div class="d-grid gap-2 extra-small">
                    <a href="/attendance/" class="btn btn-sm btn-primary rounded-pill py-2">
                        <i class="fa-solid fa-clipboard-user me-1"></i> تسجيل حضور الحصة المباشرة
                    </a>
                    <a href="/grades/manage" class="btn btn-sm btn-outline-secondary rounded-pill py-2">
                        <i class="fa-solid fa-star me-1"></i> إدخال درجات الحصة
                    </a>
                    <a href="/messages/" class="btn btn-sm btn-outline-info rounded-pill py-2">
                        <i class="fa-regular fa-paper-plane me-1"></i> إرسال تنبيه لشعبة الحصة
                    </a>
                </div>
            `;
        })
        .catch(err => {
            drawerBody.innerHTML = `
                <div class="text-center py-5 text-danger extra-small">
                    <i class="fa-solid fa-circle-exclamation fs-1 d-block mb-2"></i>
                    <h6 class="fw-bold">حدث خطأ أثناء تحميل الحصة</h6>
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
