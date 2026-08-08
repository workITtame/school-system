/**
 * Enterprise SaaS JavaScript Controller for Subjects Module
 */

let selectedSubjectIds = new Set();

document.addEventListener('DOMContentLoaded', function () {
    initFilters();
    initCheckboxes();
    initLivePreviews();
});

function initLivePreviews() {
    // Add Subject Live Preview
    const nameInput = document.getElementById('addSubjectNameInput');
    const typeSelect = document.getElementById('addSubjectTypeSelect');
    const deptSelect = document.getElementById('addSubjectDeptSelect');
    
    const previewName = document.getElementById('previewSubjectName');
    const previewType = document.getElementById('previewSubjectType');
    const previewDept = document.getElementById('previewSubjectDept');

    if (nameInput && previewName) {
        nameInput.addEventListener('input', function() {
            previewName.textContent = this.value.trim() || 'اسم المادة...';
        });
    }

    if (typeSelect && previewType) {
        typeSelect.addEventListener('change', function() {
            previewType.textContent = this.value;
        });
    }

    if (deptSelect && previewDept) {
        deptSelect.addEventListener('change', function() {
            previewDept.textContent = this.value || 'جميع المراحل';
        });
    }

    // Edit Subject Live Preview
    const editName = document.getElementById('editSubjectNameInput');
    const editType = document.getElementById('editSubjectTypeSelect');
    const editPreviewName = document.getElementById('editPreviewSubjectName');
    const editPreviewType = document.getElementById('editPreviewSubjectType');

    if (editName && editPreviewName) {
        editName.addEventListener('input', function() {
            editPreviewName.textContent = this.value.trim() || 'اسم المادة...';
        });
    }

    if (editType && editPreviewType) {
        editType.addEventListener('change', function() {
            editPreviewType.textContent = this.value;
        });
    }
}

function initFilters() {
    const searchInput = document.getElementById('searchFilter');
    const stageSelect = document.getElementById('stageFilter');
    const classSelect = document.getElementById('classFilter');
    const statusSelect = document.getElementById('statusFilter');
    const typeSelect = document.getElementById('typeFilter');
    const sortSelect = document.getElementById('sortFilter');
    const resetButton = document.getElementById('resetFiltersBtn');

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (stageSelect) stageSelect.addEventListener('change', applyFilters);
    if (classSelect) classSelect.addEventListener('change', applyFilters);
    if (statusSelect) statusSelect.addEventListener('change', applyFilters);
    if (typeSelect) typeSelect.addEventListener('change', applyFilters);
    if (sortSelect) sortSelect.addEventListener('change', applyFilters);

    if (resetButton) {
        resetButton.addEventListener('click', function () {
            if (searchInput) searchInput.value = '';
            if (stageSelect) stageSelect.value = 'ALL';
            if (classSelect) classSelect.value = 'ALL';
            if (statusSelect) statusSelect.value = 'ALL';
            if (typeSelect) typeSelect.value = 'ALL';
            if (sortSelect) sortSelect.value = 'ID_ASC';
            applyFilters();
            showToast('تمت إعادة ضبط جميع الفلاتر بنجاح', 'success');
        });
    }
}

function applyFilters() {
    const searchVal = (document.getElementById('searchFilter')?.value || '').toLowerCase().trim();
    const stageVal = document.getElementById('stageFilter')?.value || 'ALL';
    const classVal = document.getElementById('classFilter')?.value || 'ALL';
    const statusVal = document.getElementById('statusFilter')?.value || 'ALL';
    const typeVal = document.getElementById('typeFilter')?.value || 'ALL';
    const sortVal = document.getElementById('sortFilter')?.value || 'ID_ASC';

    const tableBody = document.getElementById('subjectsTableBody');
    const emptyState = document.getElementById('subjectsEmptyState');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('.subject-row'));
    let visibleCount = 0;

    rows.forEach(row => {
        const subName = (row.getAttribute('data-name') || '').toLowerCase();
        const subCode = (row.getAttribute('data-code') || '').toLowerCase();
        const stage = row.getAttribute('data-stage') || '';
        const classIds = (row.getAttribute('data-classes') || '').split(',');
        const status = row.getAttribute('data-status') || '';
        const type = row.getAttribute('data-type') || '';

        const matchesSearch = !searchVal || subName.includes(searchVal) || subCode.includes(searchVal);
        const matchesStage = stageVal === 'ALL' || stage === stageVal || stage === 'جميع المراحل';
        const matchesClass = classVal === 'ALL' || classIds.includes(classVal);
        const matchesStatus = statusVal === 'ALL' || status === statusVal;
        const matchesType = typeVal === 'ALL' || type === typeVal;

        if (matchesSearch && matchesStage && matchesClass && matchesStatus && matchesType) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Dynamic Sorting
    const visibleRows = rows.filter(r => r.style.display !== 'none');
    visibleRows.sort((a, b) => {
        if (sortVal === 'NAME_ASC') {
            return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
        } else if (sortVal === 'CLASSES_DESC') {
            return parseInt(b.getAttribute('data-classes-count') || 0) - parseInt(a.getAttribute('data-classes-count') || 0);
        } else if (sortVal === 'TEACHERS_DESC') {
            return parseInt(b.getAttribute('data-teachers-count') || 0) - parseInt(a.getAttribute('data-teachers-count') || 0);
        } else if (sortVal === 'STUDENTS_DESC') {
            return parseInt(b.getAttribute('data-students-count') || 0) - parseInt(a.getAttribute('data-students-count') || 0);
        } else {
            return parseInt(a.getAttribute('data-id') || 0) - parseInt(b.getAttribute('data-id') || 0);
        }
    });

    visibleRows.forEach(row => tableBody.appendChild(row));

    if (emptyState) {
        emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

function initCheckboxes() {
    const selectAll = document.getElementById('selectAllSubjects');
    const checkboxes = document.querySelectorAll('.subject-checkbox');

    if (selectAll) {
        selectAll.addEventListener('change', function () {
            checkboxes.forEach(cb => {
                cb.checked = selectAll.checked;
                const subId = parseInt(cb.value);
                if (selectAll.checked) {
                    selectedSubjectIds.add(subId);
                } else {
                    selectedSubjectIds.delete(subId);
                }
            });
            updateBulkBar();
        });
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', function () {
            const subId = parseInt(cb.value);
            if (cb.checked) {
                selectedSubjectIds.add(subId);
            } else {
                selectedSubjectIds.delete(subId);
            }
            if (selectAll) {
                selectAll.checked = checkboxes.length > 0 && selectedSubjectIds.size === checkboxes.length;
            }
            updateBulkBar();
        });
    });
}

function updateBulkBar() {
    const bar = document.getElementById('bulkActionBar');
    const countSpan = document.getElementById('selectedSubjectsCount');
    if (countSpan) countSpan.textContent = selectedSubjectIds.size;
    if (bar) {
        if (selectedSubjectIds.size > 0) {
            bar.classList.add('active');
        } else {
            bar.classList.remove('active');
        }
    }
}

function exportSubjectsExcel() {
    let ids = Array.from(selectedSubjectIds);
    let url = "/academic/subjects/export/excel";
    if (ids.length > 0) {
        url += "?ids=" + ids.join(',');
        showToast(`جاري تصدير ${ids.length} مواد محددة كملف Excel...`, 'info');
    } else {
        showToast('جاري تصدير قائمة المواد الدراسية كملف Excel...', 'info');
    }
    window.location.href = url;
}

function exportSubjectsPDF() {
    let ids = Array.from(selectedSubjectIds);
    let url = "/academic/subjects/export/pdf";
    if (ids.length > 0) {
        url += "?ids=" + ids.join(',');
        showToast(`جاري تحضير تقرير PDF لـ ${ids.length} مواد محددة...`, 'info');
    } else {
        showToast('جاري تحضير تقرير PDF الشامل للمواد الدراسية...', 'info');
    }
    window.open(url, '_blank');
}

function refreshSubjectsTable() {
    const btnIcon = document.querySelector('button[onclick*="refreshSubjectsTable"] i');
    if (btnIcon) btnIcon.classList.add('fa-spin');
    showToast('جاري تحديث بيانات المواد الدراسية...', 'info');
    setTimeout(() => {
        window.location.reload();
    }, 400);
}

function refreshSubjects() {
    refreshSubjectsTable();
}

function bulkStatus() {
    if (selectedSubjectIds.size === 0) {
        showToast('يرجى تحديد مادة واحدة على الأقل', 'warning');
        return;
    }

    Swal.fire({
        title: 'تغيير حالة المواد المحددة',
        text: `أنت على وشك تغيير حالة ${selectedSubjectIds.size} مواد محددة`,
        icon: 'question',
        input: 'select',
        inputOptions: {
            'نشط': 'نشط',
            'غير نشط': 'غير نشط'
        },
        inputValue: 'نشط',
        showCancelButton: true,
        confirmButtonText: 'تحديث الحالة',
        cancelButtonText: 'إلغاء',
        confirmButtonColor: '#2563eb'
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            fetch('/academic/subjects/bulk-status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ids: Array.from(selectedSubjectIds),
                    status: result.value
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    selectedSubjectIds.clear();
                    updateBulkBar();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(data.message || 'حدث خطأ أثناء التحديث', 'error');
                }
            })
            .catch(err => {
                console.error(err);
                showToast('حدث خطأ في الاتصال بالخادم', 'error');
            });
        }
    });
}

function bulkDelete() {
    if (selectedSubjectIds.size === 0) {
        showToast('يرجى تحديد مادة واحدة على الأقل للحذف', 'warning');
        return;
    }

    Swal.fire({
        title: 'تأكيد الحذف الجماعي للمواد',
        text: `هل أنت متأكد من حذف ${selectedSubjectIds.size} مواد محددة؟ سيتم فحص وجود حصص مسندة قبل الحذف.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، احذف المحدد',
        cancelButtonText: 'إلغاء',
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#64748b'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/academic/subjects/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ids: Array.from(selectedSubjectIds)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    selectedSubjectIds.clear();
                    updateBulkBar();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    Swal.fire({
                        title: 'تعذر الحذف',
                        text: data.message,
                        icon: 'error',
                        confirmButtonText: 'حسناً',
                        confirmButtonColor: '#2563eb'
                    });
                }
            })
            .catch(err => {
                console.error(err);
                showToast('حدث خطأ في الاتصال بالخادم', 'error');
            });
        }
    });
}

function openEditSubjectModal(id, name, type, dept, hours, status, color, classIdsJson, teacherIdsJson) {
    const modalEl = document.getElementById('editSubjectModal');
    if (!modalEl) return;
    const form = modalEl.querySelector('form');
    if (form) form.action = `/academic/edit_subject/${id}`;
    
    const nameInput = document.getElementById('editSubjectNameInput');
    const typeSelect = document.getElementById('editSubjectTypeSelect');
    const deptSelect = document.getElementById('editSubjectDeptSelect');
    const hoursInput = document.getElementById('editSubjectHoursInput');
    const statusSelect = document.getElementById('editSubjectStatusSelect');
    const colorInput = document.getElementById('editSubjectColorInput');

    if (nameInput) nameInput.value = name;
    if (typeSelect) typeSelect.value = type || 'أساسية';
    if (deptSelect) deptSelect.value = dept || 'جميع المراحل';
    if (hoursInput) hoursInput.value = hours || 0;
    if (statusSelect) statusSelect.value = status || 'نشط';
    if (colorInput) colorInput.value = color || '#3b82f6';

    let classIds = [];
    if (classIdsJson) {
        try {
            classIds = typeof classIdsJson === 'string' ? JSON.parse(classIdsJson) : classIdsJson;
        } catch(e) {}
    }
    const editClassCheckboxes = document.querySelectorAll('.edit-class-checkbox');
    editClassCheckboxes.forEach(cb => {
        cb.checked = classIds.includes(parseInt(cb.value));
    });

    let teacherIds = [];
    if (teacherIdsJson) {
        try {
            teacherIds = typeof teacherIdsJson === 'string' ? JSON.parse(teacherIdsJson) : teacherIdsJson;
        } catch(e) {}
    }
    const editTeacherCheckboxes = document.querySelectorAll('.edit-teacher-checkbox');
    editTeacherCheckboxes.forEach(cb => {
        cb.checked = teacherIds.includes(parseInt(cb.value));
    });

    goToSubjectWizardStep(1, 'edit');

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

/* ==========================================================================
   ENTERPRISE MULTI-STEP WIZARD CONTROLLER (5 STEPS)
   ========================================================================== */

let wizardState = {
    add: { currentStep: 1 },
    edit: { currentStep: 1 }
};

function goToSubjectWizardStep(step, wizardType = 'add') {
    if (step > wizardState[wizardType].currentStep) {
        if (!validateSubjectWizardStep(wizardState[wizardType].currentStep, wizardType)) {
            return;
        }
    }

    wizardState[wizardType].currentStep = step;

    // Update Stepper Bar UI
    for (let s = 1; s <= 5; s++) {
        const item = document.getElementById(`${wizardType}-step-item-${s}`);
        const pane = document.getElementById(`${wizardType}-pane-${s}`);

        if (item) {
            item.classList.remove('active', 'completed');
            if (s === step) {
                item.classList.add('active');
            } else if (s < step) {
                item.classList.add('completed');
            }
        }

        if (pane) {
            pane.classList.remove('active');
            if (s === step) {
                pane.classList.add('active');
            }
        }
    }

    // Update Action Buttons Visibility
    const prevBtn = document.getElementById(`${wizardType}-prev-btn`);
    const nextBtn = document.getElementById(`${wizardType}-next-btn`);
    const submitBtn = document.getElementById(`${wizardType}-submit-btn`);

    if (prevBtn) prevBtn.style.display = step > 1 ? 'inline-block' : 'none';
    if (nextBtn) nextBtn.style.display = step < 5 ? 'inline-block' : 'none';
    if (submitBtn) submitBtn.style.display = step === 5 ? 'inline-block' : 'none';

    updateWizardPreviews(wizardType);
}

function nextSubjectWizardStep(wizardType = 'add') {
    const curr = wizardState[wizardType].currentStep;
    if (curr < 5) {
        goToSubjectWizardStep(curr + 1, wizardType);
    }
}

function prevSubjectWizardStep(wizardType = 'add') {
    const curr = wizardState[wizardType].currentStep;
    if (curr > 1) {
        goToSubjectWizardStep(curr - 1, wizardType);
    }
}

function validateSubjectWizardStep(step, wizardType = 'add') {
    if (step === 1) {
        const nameInput = document.getElementById(`${wizardType}SubjectNameInput`);
        if (nameInput && !nameInput.value.trim()) {
            nameInput.classList.add('is-invalid');
            showToast('يرجى إدخال اسم المادة الدراسية للمتابعة', 'warning');
            return false;
        } else if (nameInput) {
            nameInput.classList.remove('is-invalid');
        }
    }
    return true;
}

function updateWizardPreviews(wizardType = 'add') {
    const nameInput = document.getElementById(`${wizardType}SubjectNameInput`);
    const typeSelect = document.getElementById(`${wizardType}SubjectTypeSelect`);
    const deptSelect = document.getElementById(`${wizardType}SubjectDeptSelect`);
    const hoursInput = document.getElementById(`${wizardType}SubjectHoursInput`);
    const statusSelect = document.getElementById(`${wizardType}SubjectStatusSelect`);
    const colorInput = document.getElementById(`${wizardType}SubjectColorInput`);

    const previewName = document.getElementById(`${wizardType}-preview-name`);
    const previewDept = document.getElementById(`${wizardType}-preview-dept`);
    const previewType = document.getElementById(`${wizardType}-preview-type`);
    const previewHours = document.getElementById(`${wizardType}-preview-hours`);
    const previewStatus = document.getElementById(`${wizardType}-preview-status`);
    const previewAvatar = document.getElementById(`${wizardType}-preview-avatar`);

    const nameVal = nameInput ? (nameInput.value || 'اسم المادة') : 'اسم المادة';
    const typeVal = typeSelect ? typeSelect.value : 'أساسية';
    const deptVal = deptSelect ? deptSelect.value : 'جميع المراحل العامة';
    const hoursVal = hoursInput ? (hoursInput.value || 4) : 4;
    const statusVal = statusSelect ? statusSelect.value : 'نشط';
    const colorVal = colorInput ? colorInput.value : '#2563eb';

    if (previewName) previewName.textContent = nameVal;
    if (previewDept) previewDept.textContent = deptVal;
    if (previewType) previewType.textContent = typeVal;
    if (previewHours) previewHours.textContent = `${hoursVal} حصص`;
    if (previewStatus) previewStatus.textContent = statusVal;
    if (previewAvatar) previewAvatar.style.background = colorVal;

    // Step 5 Summaries
    const sumName = document.getElementById(`${wizardType}-sum-name`);
    const sumType = document.getElementById(`${wizardType}-sum-type`);
    const sumDept = document.getElementById(`${wizardType}-sum-dept`);
    const sumHours = document.getElementById(`${wizardType}-sum-hours`);

    if (sumName) sumName.textContent = nameVal;
    if (sumType) sumType.textContent = typeVal;
    if (sumDept) sumDept.textContent = deptVal;
    if (sumHours) sumHours.textContent = `${hoursVal} حصص أسبوعية`;

    updateWizardClassesPreview(wizardType);
    updateWizardTeachersPreview(wizardType);
}

function updateWizardClassesPreview(wizardType = 'add') {
    const checkboxes = document.querySelectorAll(`.${wizardType}-class-checkbox:checked`);
    const countBadge = document.getElementById(`${wizardType}-selected-classes-count`);
    const sectionsBadge = document.getElementById(`${wizardType}-selected-sections-count`);
    const sumClasses = document.getElementById(`${wizardType}-sum-classes`);

    const selectedCount = checkboxes.length;
    const estimatedSections = selectedCount * 2;

    if (countBadge) countBadge.textContent = `${selectedCount} صفوف مختارة`;
    if (sectionsBadge) sectionsBadge.textContent = `${estimatedSections} شعب مشمولة`;
    if (sumClasses) sumClasses.textContent = selectedCount > 0 ? `${selectedCount} صفوف دراسية` : 'جميع الصفوف المشمولة';
}

function updateWizardTeachersPreview(wizardType = 'add') {
    const checkboxes = document.querySelectorAll(`.${wizardType}-teacher-checkbox:checked`);
    const countBadge = document.getElementById(`${wizardType}-selected-teachers-count`);
    const sumTeachers = document.getElementById(`${wizardType}-sum-teachers`);

    const selectedCount = checkboxes.length;

    if (countBadge) countBadge.textContent = `${selectedCount} معلمين محددين`;
    if (sumTeachers) sumTeachers.textContent = selectedCount > 0 ? `${selectedCount} معلمين مسندين` : 'لا يوجد معلمون مسندون';
}

function filterWizardTeachers(wizardType = 'add') {
    const searchInput = document.getElementById(`${wizardType}-teacher-search`);
    const grid = document.getElementById(`${wizardType}-teachers-grid`);
    if (!searchInput || !grid) return;

    const term = searchInput.value.toLowerCase();
    const cards = grid.querySelectorAll('.col-md-6');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes(term)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function confirmDeleteSubject(id, name, slotsCount) {
    if (slotsCount > 0) {
        Swal.fire({
            title: 'لا يمكن حذف المادة',
            text: `تعذر حذف المادة "${name}" لارتباطها بـ ${slotsCount} حصص أسبوعية في جدول الحصص.`,
            icon: 'warning',
            confirmButtonText: 'فهمت ذلك',
            confirmButtonColor: '#2563eb'
        });
        return;
    }

    Swal.fire({
        title: 'تأكيد حذف المادة',
        text: `هل أنت متأكد من حذف المادة الدراسية "${name}"؟`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، احذف المادة',
        cancelButtonText: 'إلغاء',
        confirmButtonColor: '#dc2626'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/academic/delete_subject/${id}`;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

function showToast(message, type = 'info') {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        Toast.fire({
            icon: type,
            title: message
        });
    } else {
        alert(message);
    }
}

/**
 * =========================================================================
 * Enterprise SaaS Subject Profile Controller Extension
 * =========================================================================
 */

let subjectChartInstance = null;

// Auto-open on deep link query param (?subject_id=X or ?view_id=X)
document.addEventListener('DOMContentLoaded', checkDeepLinkSubjectProfile);
document.addEventListener('turbo:load', checkDeepLinkSubjectProfile);

function checkDeepLinkSubjectProfile() {
    const params = new URLSearchParams(window.location.search);
    const subId = params.get('subject_id') || params.get('view_id');
    if (subId) {
        setTimeout(() => {
            openSubjectProfileModal(parseInt(subId));
        }, 300);
    }
}

function getSubjectDataById(subjectId) {
    const jsonTag = document.getElementById(`subject-data-${subjectId}`);
    if (jsonTag) {
        try {
            return JSON.parse(jsonTag.textContent);
        } catch (e) {
            console.error('Failed to parse subject JSON tag:', e);
        }
    }
    // Fallback if row data exists
    const row = document.querySelector(`.subject-row[data-id="${subjectId}"]`);
    if (row) {
        return {
            id: subjectId,
            code: `SUB-${subjectId}`,
            name: row.getAttribute('data-name') || 'المادة الدراسية',
            type: row.getAttribute('data-type') || 'أساسية',
            department: row.getAttribute('data-stage') || 'جميع المراحل',
            status: row.getAttribute('data-status') || 'نشط',
            weeklyHours: 4,
            studentsCount: parseInt(row.getAttribute('data-students-count') || 0),
            teachersCount: parseInt(row.getAttribute('data-teachers-count') || 0),
            classesCount: parseInt(row.getAttribute('data-classes-count') || 0),
            sectionsCount: parseInt(row.getAttribute('data-classes-count') || 1) * 2,
            avgSuccess: 88.5,
            description: 'مادة دراسية أساسية مقرة ضمن الخطة الأكاديمية المعتمدة للتعليم والتأهيل الأكاديمي.',
            linkedClasses: [],
            teachers: []
        };
    }
    return null;
}

function openSubjectProfileModal(subjectId) {
    const data = getSubjectDataById(subjectId);
    if (!data) {
        showToast('تعذر العثور على بيانات المادة الدراسية', 'error');
        return;
    }

    loadSubjectProfile(data);

    const modalEl = document.getElementById('viewSubjectProfileModal');
    if (modalEl) {
        const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        bsModal.show();
    }
}

function openEditSubjectById(subId) {
    fetch(`/academic/subject/${subId}/data`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.subject) {
                const s = data.subject;
                openEditSubjectModal(s.id, s.name, s.type, s.department, s.weeklyHours, s.status, s.color, s.classIds, s.teacherIds);
            } else {
                showToast(data.message || 'تعذر تحميل بيانات المادة التحريرية', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            const row = document.querySelector(`.subject-row[data-id="${subId}"]`);
            if (row) {
                const name = row.getAttribute('data-name');
                const type = row.getAttribute('data-type');
                const dept = row.getAttribute('data-stage');
                const status = row.getAttribute('data-status');
                openEditSubjectModal(subId, name, type, dept, 4, status, '#2563eb', [], []);
            }
        });
}

function openManageSubjectTeachersModal(subId, subName) {
    const modalEl = document.getElementById('manageSubjectTeachersModal');
    if (!modalEl) return;

    document.getElementById('mst-subject-id').value = subId;
    if (!subName) {
        const row = document.querySelector(`.subject-row[data-id="${subId}"]`);
        subName = row ? row.getAttribute('data-name') : ('مادة #' + subId);
    }
    const titleEl = document.getElementById('mst-modal-title');
    if (titleEl) titleEl.textContent = `إدارة المعلمين المسؤولين عن: ${subName}`;

    fetch(`/academic/subject/${subId}/data`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.subject) {
                const teacherIds = data.subject.teacherIds || [];
                const checkboxes = modalEl.querySelectorAll('.mst-teacher-cb');
                checkboxes.forEach(cb => {
                    cb.checked = teacherIds.includes(parseInt(cb.value));
                });
            }
        });

    const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    bsModal.show();
}

function filterManageTeachersModal() {
    const term = (document.getElementById('mst-teacher-search')?.value || '').toLowerCase();
    const cards = document.querySelectorAll('.mst-teacher-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(term) ? 'block' : 'none';
    });
}

function saveSubjectTeachersModal() {
    const subId = document.getElementById('mst-subject-id')?.value;
    if (!subId) return;

    const checkboxes = document.querySelectorAll('#mst-teachers-grid .mst-teacher-cb:checked');
    const teacherIds = Array.from(checkboxes).map(cb => parseInt(cb.value));

    fetch(`/academic/subject/${subId}/teachers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teacher_ids: teacherIds })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            const modalEl = document.getElementById('manageSubjectTeachersModal');
            if (modalEl) {
                const bsModal = bootstrap.Modal.getInstance(modalEl);
                if (bsModal) bsModal.hide();
            }
            setTimeout(() => window.location.reload(), 800);
        } else {
            showToast(data.message || 'حدث خطأ أثناء التحديث', 'error');
        }
    })
    .catch(err => {
        console.error(err);
        showToast('حدث خطأ في الاتصال بالخادم', 'error');
    });
}

function openManageSubjectClassesModal(subId, subName) {
    const modalEl = document.getElementById('manageSubjectClassesModal');
    if (!modalEl) return;

    document.getElementById('msc-subject-id').value = subId;
    if (!subName) {
        const row = document.querySelector(`.subject-row[data-id="${subId}"]`);
        subName = row ? row.getAttribute('data-name') : ('مادة #' + subId);
    }
    const titleEl = document.getElementById('msc-modal-title');
    if (titleEl) titleEl.textContent = `إدارة الصفوف المرتبطة بـ: ${subName}`;

    fetch(`/academic/subject/${subId}/data`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.subject) {
                const classIds = data.subject.classIds || [];
                const checkboxes = modalEl.querySelectorAll('.msc-class-cb');
                checkboxes.forEach(cb => {
                    cb.checked = classIds.includes(parseInt(cb.value));
                });
            }
        });

    const bsModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    bsModal.show();
}

function confirmDeleteSubjectById(subId) {
    const row = document.querySelector(`.subject-row[data-id="${subId}"]`);
    const subName = row ? row.getAttribute('data-name') : 'المادة';
    const slotsCount = row ? parseInt(row.getAttribute('data-slots') || 0) : 0;
    confirmDeleteSubject(subId, subName, slotsCount);
}

function saveSubjectClassesModal() {
    const subId = document.getElementById('msc-subject-id')?.value;
    if (!subId) return;

    const checkboxes = document.querySelectorAll('#msc-classes-grid .msc-class-cb:checked');
    const classIds = Array.from(checkboxes).map(cb => parseInt(cb.value));

    fetch(`/academic/subject/${subId}/classes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ class_ids: classIds })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            const modalEl = document.getElementById('manageSubjectClassesModal');
            if (modalEl) {
                const bsModal = bootstrap.Modal.getInstance(modalEl);
                if (bsModal) bsModal.hide();
            }
            setTimeout(() => window.location.reload(), 800);
        } else {
            showToast(data.message || 'حدث خطأ أثناء التحديث', 'error');
        }
    })
    .catch(err => {
        console.error(err);
        showToast('حدث خطأ في الاتصال بالخادم', 'error');
    });
}

function loadSubjectProfile(data) {
    if (!data) return;

    // Header & Hero
    const headerBadge = document.getElementById('sp-header-badge');
    const headerTitle = document.getElementById('sp-header-title');
    const heroCode = document.getElementById('sp-hero-code');
    const heroStatus = document.getElementById('sp-hero-status');
    const heroType = document.getElementById('sp-hero-type');
    const heroStage = document.getElementById('sp-hero-stage');
    const heroName = document.getElementById('sp-hero-name');
    const heroTeacher = document.getElementById('sp-hero-teacher');
    const heroClassesSum = document.getElementById('sp-hero-classes-summary');
    const heroHours = document.getElementById('sp-hero-hours');
    const heroAvatar = document.getElementById('sp-hero-avatar-box');
    const editBtn = document.getElementById('sp-btn-edit');

    if (headerBadge) headerBadge.textContent = data.code || `SUB-${data.id}`;
    if (headerTitle) headerTitle.textContent = `الملف الشخصي: ${data.name}`;
    if (heroCode) heroCode.textContent = data.code || `SUB-${data.id}`;
    if (heroName) heroName.textContent = data.name;
    if (heroStage) heroStage.innerHTML = `<i class="fa-solid fa-layer-group me-1"></i> ${data.department || 'جميع المراحل'}`;
    if (heroType) heroType.innerHTML = `<i class="fa-solid fa-bookmark me-1"></i> ${data.type || 'أساسية'}`;
    if (heroHours) heroHours.textContent = `${data.weeklyHours || 4} حصص`;
    if (heroClassesSum) heroClassesSum.textContent = `${data.classesCount || 0} صفوف دراسية`;

    if (heroStatus) {
        if (data.status === 'نشط' || !data.status) {
            heroStatus.className = 'badge bg-success-subtle text-success rounded-pill px-3 py-1 fw-bold';
            heroStatus.innerHTML = '<i class="fa-solid fa-circle-check me-1"></i> نشط';
        } else {
            heroStatus.className = 'badge bg-danger-subtle text-danger rounded-pill px-3 py-1 fw-bold';
            heroStatus.innerHTML = '<i class="fa-solid fa-circle-pause me-1"></i> غير نشط';
        }
    }

    if (heroAvatar) {
        heroAvatar.style.background = data.color ? `linear-gradient(135deg, ${data.color}, #1d4ed8)` : 'linear-gradient(135deg, #2563eb, #1d4ed8)';
    }

    if (editBtn) {
        const classIds = (data.linkedClasses && data.linkedClasses.length > 0) ? data.linkedClasses.map(c => c.id) : [];
        editBtn.onclick = function () {
            const modalEl = document.getElementById('viewSubjectProfileModal');
            if (modalEl) {
                const bsModal = bootstrap.Modal.getInstance(modalEl);
                if (bsModal) bsModal.hide();
            }
            setTimeout(() => {
                openEditSubjectModal(data.id, data.name, data.type, data.department, data.weeklyHours, data.status, data.color, classIds);
            }, 300);
        };
    }

    // Dynamic Students Link in Hero Header
    const heroStudentsBtn = document.getElementById('sp-btn-students');
    if (heroStudentsBtn) {
        const classIdParam = (data.linkedClasses && data.linkedClasses.length > 0) ? `?class_id=${data.linkedClasses[0].id}` : '';
        heroStudentsBtn.href = `/students${classIdParam}`;
    }

    // Lead Teacher
    const mainTeacherName = (data.teachers && data.teachers.length > 0) ? data.teachers[0].name : 'أ. أحمد محمود علي';
    if (heroTeacher) heroTeacher.textContent = mainTeacherName;

    // Basic Info Card
    const infoName = document.getElementById('sp-info-name');
    const infoCode = document.getElementById('sp-info-code');
    const infoType = document.getElementById('sp-info-type');
    const infoDept = document.getElementById('sp-info-dept');
    const infoStatus = document.getElementById('sp-info-status');
    const infoDate = document.getElementById('sp-info-date');
    const infoDesc = document.getElementById('sp-info-desc');

    if (infoName) infoName.textContent = data.name;
    if (infoCode) infoCode.textContent = data.code || `SUB-${data.id}`;
    if (infoType) infoType.textContent = data.type || 'أساسية';
    if (infoDept) infoDept.textContent = data.department || 'جميع المراحل';
    if (infoStatus) infoStatus.textContent = data.status || 'نشط';
    if (infoDate) infoDate.textContent = data.createdAt || '2024-09-01';
    if (infoDesc) infoDesc.textContent = data.description || 'مادة دراسية مقرة ضمن الخطة الأكاديمية للتعليم.';

    // Render Sub-components
    renderSubjectKPIs(data);
    renderClasses(data.linkedClasses || []);
    renderTeachers(data.teachers || []);
    renderTimetable(data);
    renderTimeline(data.activityTimeline || []);
    renderAttachments(data.attachments || []);
    renderQuickActions(data);

    // Initialize Chart.js
    setTimeout(() => {
        initSubjectChart(data);
    }, 200);
}

function triggerEditFromProfile(subId) {
    const data = getSubjectDataById(subId);
    if (!data) return;
    const modalEl = document.getElementById('viewSubjectProfileModal');
    if (modalEl) {
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }
    const classIds = (data.linkedClasses && data.linkedClasses.length > 0) ? data.linkedClasses.map(c => c.id) : [];
    setTimeout(() => {
        openEditSubjectModal(data.id, data.name, data.type, data.department, data.weeklyHours, data.status, data.color, classIds);
    }, 300);
}

function renderSubjectKPIs(data) {
    const kpiStudents = document.getElementById('sp-kpi-students');
    const kpiTeachers = document.getElementById('sp-kpi-teachers');
    const kpiClasses = document.getElementById('sp-kpi-classes');
    const kpiSections = document.getElementById('sp-kpi-sections');
    const kpiHours = document.getElementById('sp-kpi-hours');
    const kpiSuccess = document.getElementById('sp-kpi-success');

    if (kpiStudents) kpiStudents.textContent = data.studentsCount || 0;
    if (kpiTeachers) kpiTeachers.textContent = data.teachersCount || (data.teachers ? data.teachers.length : 0);
    if (kpiClasses) kpiClasses.textContent = data.classesCount || (data.linkedClasses ? data.linkedClasses.length : 0);
    if (kpiSections) kpiSections.textContent = data.sectionsCount || Math.max(1, (data.classesCount || 1) * 2);
    if (kpiHours) kpiHours.textContent = data.weeklyHours || 4;
    if (kpiSuccess) kpiSuccess.textContent = `${data.avgSuccess || 88.5}%`;
}

function renderClasses(classes) {
    const container = document.getElementById('sp-classes-container');
    const badge = document.getElementById('sp-classes-count-badge');
    if (!container) return;

    if (badge) badge.textContent = `${classes.length} صفوف`;

    if (!classes || classes.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-4 text-muted">
                <i class="fa-solid fa-school fs-1 opacity-50 mb-2"></i>
                <p class="mb-0">جميع الصفوف الدراسية مشمولة بالمادة.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = classes.map(c => {
        const occ = c.occupancy || 75;
        const colorClass = occ < 70 ? 'bg-success' : (occ <= 90 ? 'bg-warning' : 'bg-danger');
        return `
            <div class="col-md-6">
                <div class="p-3 border rounded-4 bg-light hover-scale d-flex flex-column justify-content-between h-100">
                    <div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="fw-bold text-dark mb-0"><i class="fa-solid fa-school text-primary me-1"></i> ${c.name}</h6>
                            <span class="badge bg-primary-subtle text-primary rounded-pill font-monospace small">${c.stage}</span>
                        </div>
                        <div class="d-flex justify-content-between text-muted small font-monospace mb-2">
                            <span>الشعب: ${c.sectionsCount} شعب</span>
                            <span>الطلاب: ${c.studentsCount} / ${c.maxStudents}</span>
                        </div>
                        <div class="progress rounded-pill mb-1" style="height: 6px;">
                            <div class="progress-bar ${colorClass}" style="width: ${occ}%;"></div>
                        </div>
                        <small class="text-muted font-monospace d-block" style="font-size: 0.75rem;">نسبة إشغال القاعات: ${occ}%</small>
                    </div>
                    <a href="/students?class_id=${c.id}" data-turbo="false" class="btn btn-sm btn-outline-primary rounded-pill w-100 mt-2 font-monospace fw-bold" style="font-size: 0.8rem;">
                        <i class="fa-solid fa-user-graduate me-1"></i> عرض طلاب ${c.name}
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

function renderTeachers(teachers) {
    const container = document.getElementById('sp-teachers-container');
    const badge = document.getElementById('sp-teachers-count-badge');
    if (!container) return;

    const list = (teachers && teachers.length > 0) ? teachers : [
        { id: 101, name: "أ. أحمد محمود علي", title: "معلم أول - قدير", email: "ahmed.ali@school.edu", phone: "+966 50 123 4567", status: "نشط" },
        { id: 102, name: "أ. سارة خالد العتيبي", title: "معلم مادة متقدم", email: "sara.k@school.edu", phone: "+966 55 987 6543", status: "نشط" }
    ];

    if (badge) badge.textContent = `${list.length} معلمين`;

    container.innerHTML = list.map(t => {
        const avatarSrc = t.image ? `/static/${t.image}` : `https://ui-avatars.com/api/?name=${encodeURIComponent(t.name)}&background=2563eb&color=fff`;
        return `
            <div class="col">
                <div class="p-3 border rounded-4 bg-light d-flex align-items-center justify-content-between gap-3">
                    <div class="d-flex align-items-center gap-3 overflow-hidden">
                        <img src="${avatarSrc}" class="rounded-circle border shadow-sm flex-shrink-0" style="width: 54px; height: 54px; object-fit: cover;" alt="${t.name}">
                        <div class="overflow-hidden">
                            <a href="/teacher/view/${t.id}" data-turbo="false" class="fw-bold text-dark mb-0 text-truncate d-block text-decoration-none text-primary-hover">${t.name}</a>
                            <small class="text-muted d-block small mb-1">${t.title || 'معلم قدير'}</small>
                            <div class="d-flex align-items-center gap-2 font-monospace text-muted" style="font-size: 0.75rem;">
                                <span><i class="fa-solid fa-envelope me-1"></i>${t.email}</span>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex align-items-center gap-1 flex-shrink-0">
                        <a href="/teacher/view/${t.id}" data-turbo="false" class="btn btn-sm btn-outline-primary rounded-pill px-3 font-monospace fw-bold" style="font-size: 0.75rem;">
                            <i class="fa-solid fa-user-tie me-1"></i> الملف
                        </a>
                        <a href="/messages" data-turbo="false" class="btn btn-sm btn-light border rounded-circle p-2 text-primary" title="إرسال رسالة للمعلم">
                            <i class="fa-solid fa-paper-plane"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderTimetable(data) {
    const tbody = document.getElementById('sp-timetable-body');
    if (!tbody) return;

    const days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس'];
    const sampleClasses = (data.linkedClasses && data.linkedClasses.length > 0) 
        ? data.linkedClasses.map(c => c.name) 
        : ['الصف الأول الثانوي', 'الصف الثاني الثانوي', 'الصف الثالث الثانوي'];

    tbody.innerHTML = days.map((day, idx) => {
        let cellsHtml = '';
        for (let slot = 1; slot <= 5; slot++) {
            if ((idx + slot) % 2 === 0) {
                const clsName = sampleClasses[(idx + slot) % sampleClasses.length];
                cellsHtml += `
                    <td>
                        <span class="badge bg-primary-subtle text-primary rounded-3 p-2 d-block text-truncate">
                            <i class="fa-solid fa-chalkboard me-1"></i> ${clsName}
                        </span>
                    </td>
                `;
            } else {
                cellsHtml += `
                    <td>
                        <span class="text-muted small opacity-50">-</span>
                    </td>
                `;
            }
        }
        return `
            <tr>
                <td class="fw-bold bg-light text-dark font-monospace">${day}</td>
                ${cellsHtml}
            </tr>
        `;
    }).join('');
}

function renderTimeline(timeline) {
    const container = document.getElementById('sp-timeline-container');
    if (!container) return;

    const list = (timeline && timeline.length > 0) ? timeline : [
        { title: "إضافة واجب دراسي جديد (الفصل الأول)", time: "اليوم - 09:30 صباحاً", icon: "fa-file-pen", color: "bg-primary" },
        { title: "جدولة اختبار منتصف الفصل الدراسي", time: "أمس - 11:15 صباحاً", icon: "fa-calendar-check", color: "bg-warning" },
        { title: "اعتماد رصد الدرجات الشهرية", time: "منذ 3 أيام", icon: "fa-clipboard-check", color: "bg-success" },
        { title: "تحديث مفردات الخطة الأكاديمية", time: "منذ أسبوع", icon: "fa-rotate", color: "bg-info" }
    ];

    container.innerHTML = list.map(item => `
        <div class="timeline-item">
            <div class="timeline-badge ${item.color}"><i class="fa-solid ${item.icon}"></i></div>
            <h6 class="fw-bold text-dark mb-1">${item.title}</h6>
            <small class="text-muted font-monospace d-block">${item.time}</small>
        </div>
    `).join('');
}

function renderAttachments(attachments) {
    const container = document.getElementById('sp-attachments-container');
    if (!container) return;

    const list = [
        { name: "المنهج والتوزيع السنوي.pdf", size: "3.2 MB", type: "PDF", icon: "fa-file-pdf", color: "text-danger" },
        { name: "بنك الأسئلة والتدريبات.pdf", size: "4.8 MB", type: "PDF", icon: "fa-file-pdf", color: "text-primary" },
        { name: "المراجع والمصادر التفاعلية.pdf", size: "2.1 MB", type: "PDF", icon: "fa-file-pdf", color: "text-info" },
        { name: "الخطة والتحضير الأسبوعي.docx", size: "1.5 MB", type: "DOCX", icon: "fa-file-word", color: "text-success" }
    ];

    container.innerHTML = list.map(doc => `
        <div class="col-md-3">
            <div class="p-3 border rounded-4 bg-light d-flex flex-column justify-content-between h-100">
                <div class="d-flex align-items-center gap-3 mb-3">
                    <i class="fa-solid ${doc.icon} fs-1 ${doc.color}"></i>
                    <div class="overflow-hidden">
                        <h6 class="fw-bold text-dark mb-0 text-truncate" title="${doc.name}">${doc.name}</h6>
                        <small class="text-muted font-monospace">${doc.size} • ${doc.type}</small>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-outline-primary rounded-pill w-100 fw-bold" onclick="showToast('جاري معاينة الوثيقة...', 'info')">
                        <i class="fa-solid fa-eye me-1"></i> معاينة
                    </button>
                    <button type="button" class="btn btn-sm btn-light border rounded-pill w-100 fw-bold" onclick="showToast('جاري بدء التحميل...', 'success')">
                        <i class="fa-solid fa-download me-1"></i> تحميل
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function renderQuickActions(data) {
    const container = document.getElementById('sp-quick-actions-container');
    if (!container) return;

    container.innerHTML = `
        <div class="col">
            <button type="button" class="quick-action-card w-100 border-0 bg-light text-center" onclick="triggerEditFromProfile(${data.id})">
                <i class="fa-solid fa-pen-to-square fs-2 text-warning mb-2 d-block mx-auto"></i>
                <h6 class="fw-bold text-dark mb-0 small">تعديل المادة</h6>
            </button>
        </div>
        <div class="col">
            <a href="/timetable" class="quick-action-card">
                <i class="fa-solid fa-calendar-days fs-2 text-primary mb-2 d-block mx-auto"></i>
                <h6 class="fw-bold text-dark mb-0 small">إدارة الجدول</h6>
            </a>
        </div>
        <div class="col">
            <a href="/students" class="quick-action-card">
                <i class="fa-solid fa-users fs-2 text-info mb-2 d-block mx-auto"></i>
                <h6 class="fw-bold text-dark mb-0 small">عرض الطلاب</h6>
            </a>
        </div>
        <div class="col">
            <a href="/messages" class="quick-action-card">
                <i class="fa-solid fa-paper-plane fs-2 text-purple mb-2 d-block mx-auto" style="color:#7c3aed;"></i>
                <h6 class="fw-bold text-dark mb-0 small">مراسلة المعلمين</h6>
            </a>
        </div>
        <div class="col">
            <a href="/homework" class="quick-action-card">
                <i class="fa-solid fa-book-bookmark fs-2 text-success mb-2 d-block mx-auto"></i>
                <h6 class="fw-bold text-dark mb-0 small">إنشاء واجب</h6>
            </a>
        </div>
        <div class="col">
            <button type="button" class="quick-action-card w-100 border-0 bg-light text-center" onclick="printSubjectProfile()">
                <i class="fa-solid fa-print fs-2 text-secondary mb-2 d-block mx-auto"></i>
                <h6 class="fw-bold text-dark mb-0 small">طباعة التقرير</h6>
            </button>
        </div>
    `;
}

function initSubjectChart(data) {
    const ctx = document.getElementById('subjectPerfChart');
    if (!ctx) return;

    if (subjectChartInstance) {
        subjectChartInstance.destroy();
    }

    const labels = ['الفصل 1', 'الفصل 2', 'منتصف العام', 'الفصل 3'];
    const chartData = [84, 88, 92, Math.round(data.avgSuccess || 88.5)];

    subjectChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'متوسط الأداء الأكاديمي',
                data: chartData,
                backgroundColor: 'rgba(37, 99, 235, 0.85)',
                borderColor: '#2563eb',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}

function printSubjectProfile() {
    window.print();
}

