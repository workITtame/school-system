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

function openEditSubjectModal(id, name, type, dept, hours, status, color, classIdsJson) {
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

    const editClassesSelect = document.getElementById('editSubjectClassesSelect');
    if (editClassesSelect && classIdsJson) {
        let classIds = [];
        try {
            classIds = typeof classIdsJson === 'string' ? JSON.parse(classIdsJson) : classIdsJson;
        } catch(e) {}
        Array.from(editClassesSelect.options).forEach(opt => {
            opt.selected = classIds.includes(parseInt(opt.value));
        });
    }

    const editPreviewName = document.getElementById('editPreviewSubjectName');
    const editPreviewType = document.getElementById('editPreviewSubjectType');
    if (editPreviewName) editPreviewName.textContent = name;
    if (editPreviewType) editPreviewType.textContent = type || 'أساسية';
    
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
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
