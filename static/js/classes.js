/**
 * Enterprise SaaS JavaScript Controller for Classes & Sections Module
 */

let selectedClassIds = new Set();

document.addEventListener('DOMContentLoaded', function () {
    initFilters();
    initCheckboxes();
    initLivePreviews();
});

function initLivePreviews() {
    // Add Class Preview
    const addClassName = document.getElementById('addClassNameInput');
    const addClassStage = document.getElementById('addClassStageSelect');
    const previewClassName = document.getElementById('previewClassName');
    const previewClassStage = document.getElementById('previewClassStage');

    if (addClassName && previewClassName) {
        addClassName.addEventListener('input', function() {
            previewClassName.textContent = this.value.trim() || 'الاسم يظهر هنا عند الكتابة...';
        });
    }

    if (addClassStage && previewClassStage) {
        addClassStage.addEventListener('change', function() {
            previewClassStage.textContent = this.value;
        });
    }

    // Add Section Preview
    const addSecName = document.getElementById('addSectionNameInput');
    const addSecClass = document.getElementById('addSectionClassSelect');
    const previewSecName = document.getElementById('previewSectionName');
    const previewSecClass = document.getElementById('previewSectionClass');

    if (addSecName && previewSecName) {
        addSecName.addEventListener('input', function() {
            previewSecName.textContent = this.value.trim() || 'اسم الشعبة...';
        });
    }

    if (addSecClass && previewSecClass) {
        const updateSecClassPreview = function() {
            const selectedOpt = addSecClass.options[addSecClass.selectedIndex];
            previewSecClass.textContent = selectedOpt ? `مربوطة بـ ${selectedOpt.text}` : 'مربوطة بصف...';
        };
        addSecClass.addEventListener('change', updateSecClassPreview);
        updateSecClassPreview();
    }

    // Edit Class Live Preview
    const editClassName = document.getElementById('editClassNameInput');
    const editClassStage = document.getElementById('editClassStageSelect');
    const editPreviewName = document.getElementById('editPreviewClassName');
    const editPreviewStage = document.getElementById('editPreviewClassStage');

    if (editClassName && editPreviewName) {
        editClassName.addEventListener('input', function() {
            editPreviewName.textContent = this.value.trim() || 'اسم الصف الحقيقي...';
        });
    }
    if (editClassStage && editPreviewStage) {
        editClassStage.addEventListener('change', function() {
            editPreviewStage.textContent = this.value;
        });
    }
}

function initFilters() {
    const searchInput = document.getElementById('searchFilter');
    const stageSelect = document.getElementById('stageFilter');
    const statusSelect = document.getElementById('statusFilter');
    const sortSelect = document.getElementById('sortFilter');
    const resetButton = document.getElementById('resetFiltersBtn');

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (stageSelect) stageSelect.addEventListener('change', applyFilters);
    if (statusSelect) statusSelect.addEventListener('change', applyFilters);
    if (sortSelect) sortSelect.addEventListener('change', applyFilters);

    if (resetButton) {
        resetButton.addEventListener('click', function () {
            if (searchInput) searchInput.value = '';
            if (stageSelect) stageSelect.value = 'ALL';
            if (statusSelect) statusSelect.value = 'ALL';
            if (sortSelect) sortSelect.value = 'ID_ASC';
            applyFilters();
        });
    }
}

function applyFilters() {
    const searchVal = (document.getElementById('searchFilter')?.value || '').toLowerCase().trim();
    const stageVal = document.getElementById('stageFilter')?.value || 'ALL';
    const statusVal = document.getElementById('statusFilter')?.value || 'ALL';
    const sortVal = document.getElementById('sortFilter')?.value || 'ID_ASC';

    const tableBody = document.getElementById('classesTableBody');
    const emptyState = document.getElementById('classesEmptyState');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('.class-row'));
    let visibleCount = 0;

    rows.forEach(row => {
        const className = (row.getAttribute('data-name') || '').toLowerCase();
        const classCode = (row.getAttribute('data-code') || '').toLowerCase();
        const stage = row.getAttribute('data-stage') || '';
        const status = row.getAttribute('data-status') || '';

        const matchesSearch = !searchVal || className.includes(searchVal) || classCode.includes(searchVal);
        const matchesStage = stageVal === 'ALL' || stage === stageVal;
        const matchesStatus = statusVal === 'ALL' || status === statusVal;

        if (matchesSearch && matchesStage && matchesStatus) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Handle Sorting
    const visibleRows = rows.filter(r => r.style.display !== 'none');
    visibleRows.sort((a, b) => {
        if (sortVal === 'NAME_ASC') {
            return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
        } else if (sortVal === 'STUDENTS_DESC') {
            return parseInt(b.getAttribute('data-students') || 0) - parseInt(a.getAttribute('data-students') || 0);
        } else if (sortVal === 'SECTIONS_DESC') {
            return parseInt(b.getAttribute('data-sections') || 0) - parseInt(a.getAttribute('data-sections') || 0);
        } else if (sortVal === 'OCCUPANCY_DESC') {
            return parseFloat(b.getAttribute('data-occupancy') || -1) - parseFloat(a.getAttribute('data-occupancy') || -1);
        } else {
            return parseInt(a.getAttribute('data-id') || 0) - parseInt(b.getAttribute('data-id') || 0);
        }
    });

    visibleRows.forEach(row => tableBody.appendChild(row));

    // Toggle Empty State
    if (emptyState) {
        emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

function initCheckboxes() {
    const selectAll = document.getElementById('selectAllClasses');
    const checkboxes = document.querySelectorAll('.class-checkbox');

    if (selectAll) {
        selectAll.addEventListener('change', function () {
            checkboxes.forEach(cb => {
                cb.checked = selectAll.checked;
                const cid = parseInt(cb.value);
                if (selectAll.checked) {
                    selectedClassIds.add(cid);
                } else {
                    selectedClassIds.delete(cid);
                }
            });
            updateBulkBar();
        });
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', function () {
            const cid = parseInt(cb.value);
            if (cb.checked) {
                selectedClassIds.add(cid);
            } else {
                selectedClassIds.delete(cid);
            }
            if (selectAll) {
                selectAll.checked = checkboxes.length > 0 && selectedClassIds.size === checkboxes.length;
            }
            updateBulkBar();
        });
    });
}

function updateBulkBar() {
    const bar = document.getElementById('bulkActionBar');
    const countSpan = document.getElementById('selectedClassesCount');
    if (countSpan) countSpan.textContent = selectedClassIds.size;
    if (bar) {
        if (selectedClassIds.size > 0) {
            bar.classList.add('active');
        } else {
            bar.classList.remove('active');
        }
    }
}

function exportClassesExcel() {
    let ids = Array.from(selectedClassIds);
    let url = "/academic/classes/export/excel";
    if (ids.length > 0) {
        url += "?ids=" + ids.join(',');
        showToast(`جاري تصدير ${ids.length} صفوف محدودة كملف Excel...`, 'info');
    } else {
        showToast('جاري تصدير قائمة الصفوف والشعب كملف Excel...', 'info');
    }
    window.location.href = url;
}

function exportClassesPDF() {
    let ids = Array.from(selectedClassIds);
    let url = "/academic/classes/export/pdf";
    if (ids.length > 0) {
        url += "?ids=" + ids.join(',');
        showToast(`جاري تحضير تقرير PDF لـ ${ids.length} صفوف محددة...`, 'info');
    } else {
        showToast('جاري تحضير تقرير PDF الشامل للصفوف والشعب...', 'info');
    }
    window.open(url, '_blank');
}

function refreshClasses() {
    showToast('جاري تحديث البيانات...', 'info');
    window.location.reload();
}

function bulkStatus() {
    if (selectedClassIds.size === 0) {
        showToast('يرجى تحديد صف واحد على الأقل', 'warning');
        return;
    }

    Swal.fire({
        title: 'تغيير حالة الصفوف المحددة',
        text: `أنت على وشك تغيير حالة ${selectedClassIds.size} صفوف`,
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
            fetch('/academic/classes/bulk-status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ids: Array.from(selectedClassIds),
                    status: result.value
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    selectedClassIds.clear();
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
    if (selectedClassIds.size === 0) {
        showToast('يرجى تحديد صف واحد على الأقل للحذف', 'warning');
        return;
    }

    Swal.fire({
        title: 'تأكيد الحذف الجماعي',
        text: `هل أنت متأكد من حذف ${selectedClassIds.size} صفوف محددة؟ سيتم فحص وجود طلاب مسجلين بالصف قبل الحذف.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، احذف المحدد',
        cancelButtonText: 'إلغاء',
        confirmButtonColor: '#dc2626',
        cancelButtonColor: '#64748b'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/academic/classes/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ids: Array.from(selectedClassIds)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    selectedClassIds.clear();
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

function openEditClassModal(id, name, stage) {
    const modalEl = document.getElementById('editClassModal');
    if (!modalEl) return;
    const form = modalEl.querySelector('form');
    if (form) form.action = `/academic/edit_class/${id}`;
    
    const nameInput = document.getElementById('editClassNameInput');
    const stageSelect = document.getElementById('editClassStageSelect');
    const editPreviewName = document.getElementById('editPreviewClassName');
    const editPreviewStage = document.getElementById('editPreviewClassStage');

    if (nameInput) nameInput.value = name;
    if (stageSelect) stageSelect.value = stage;
    if (editPreviewName) editPreviewName.textContent = name;
    if (editPreviewStage) editPreviewStage.textContent = stage;
    
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function confirmDeleteClass(id, name, studentCount) {
    if (studentCount > 0) {
        Swal.fire({
            title: 'لا يمكن حذف الصف',
            text: `تعذر حذف الصف "${name}" لأنه يحتوي على ${studentCount} طلاب مسجلين بالفعل. يرجى نقل الطلاب أولاً.`,
            icon: 'warning',
            confirmButtonText: 'فهمت ذلك',
            confirmButtonColor: '#2563eb'
        });
        return;
    }

    Swal.fire({
        title: 'تأكيد حذف الصف',
        text: `هل أنت متأكد من حذف الصف "${name}"؟`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، احذف الصف',
        cancelButtonText: 'إلغاء',
        confirmButtonColor: '#dc2626'
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/academic/delete_class/${id}`;
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
