/* ==========================================================================
   ENTERPRISE SAAS REPORTS CENTER CONTROLLER (static/js/reports.js)
   ========================================================================== */

document.addEventListener('turbo:load', function() {
    initReportsModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initReportsModule();
});

function initReportsModule() {
    const rootEl = document.getElementById('reportsModuleRoot');
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    // Register global window handlers
    window.exportReportsMasterExcel = exportReportsMasterExcel;
    window.filterReportsCatalog = filterReportsCatalog;
    window.resetReportsFilters = resetReportsFilters;

    setupReportsEventListeners();
}

function setupReportsEventListeners() {
    const searchInput = document.getElementById('reportsFilterSearch');
    const categorySelect = document.getElementById('reportsFilterCategory');
    const typeSelect = document.getElementById('reportsFilterType');
    const resetBtn = document.getElementById('reportsResetFiltersBtn');

    if (searchInput) {
        searchInput.addEventListener('input', filterReportsCatalog);
    }
    if (categorySelect) {
        categorySelect.addEventListener('change', filterReportsCatalog);
    }
    if (typeSelect) {
        typeSelect.addEventListener('change', filterReportsCatalog);
    }
    if (resetBtn) {
        resetBtn.addEventListener('click', resetReportsFilters);
    }
}

function filterReportsCatalog() {
    const searchVal = document.getElementById('reportsFilterSearch')?.value.toLowerCase().trim() || '';
    const catVal = document.getElementById('reportsFilterCategory')?.value || '';
    const typeVal = document.getElementById('reportsFilterType')?.value || '';
    const badgeEl = document.getElementById('reportsActiveFiltersBadge');

    let isFiltered = searchVal !== '' || catVal !== '' || typeVal !== '';
    if (badgeEl) {
        if (isFiltered) badgeEl.classList.remove('d-none');
        else badgeEl.classList.add('d-none');
    }

    // Filter Category Cards
    const cards = document.querySelectorAll('.report-category-card');
    let visibleCards = 0;
    cards.forEach(card => {
        const title = card.dataset.title ? card.dataset.title.toLowerCase() : '';
        const cat = card.dataset.category || '';
        const type = card.dataset.type || '';

        const matchesSearch = !searchVal || title.includes(searchVal);
        const matchesCat = !catVal || cat === catVal;
        const matchesType = !typeVal || type.includes(typeVal);

        if (matchesSearch && matchesCat && matchesType) {
            card.parentElement.classList.remove('d-none');
            visibleCards++;
        } else {
            card.parentElement.classList.add('d-none');
        }
    });

    // Filter Table Rows
    const rows = document.querySelectorAll('#reportsMasterTableBody tr.report-table-row');
    let visibleRows = 0;
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const cat = row.dataset.category || '';
        const type = row.dataset.type || '';

        const matchesSearch = !searchVal || text.includes(searchVal);
        const matchesCat = !catVal || cat === catVal;
        const matchesType = !typeVal || type.includes(typeVal);

        if (matchesSearch && matchesCat && matchesType) {
            row.classList.remove('d-none');
            visibleRows++;
        } else {
            row.classList.add('d-none');
        }
    });

    // Handle Empty States
    const cardsEmptyState = document.getElementById('reportsCardsEmptyState');
    const tableEmptyState = document.getElementById('reportsTableEmptyState');

    if (cardsEmptyState) {
        if (visibleCards === 0) cardsEmptyState.classList.remove('d-none');
        else cardsEmptyState.classList.add('d-none');
    }

    if (tableEmptyState) {
        if (visibleRows === 0) tableEmptyState.classList.remove('d-none');
        else tableEmptyState.classList.add('d-none');
    }
}

function resetReportsFilters() {
    const searchInput = document.getElementById('reportsFilterSearch');
    const categorySelect = document.getElementById('reportsFilterCategory');
    const typeSelect = document.getElementById('reportsFilterType');

    if (searchInput) searchInput.value = '';
    if (categorySelect) categorySelect.value = '';
    if (typeSelect) typeSelect.value = '';

    filterReportsCatalog();
    showToast('تمت إعادة ضبط الفلاتر بنجاح', 'info');
}

function exportReportsMasterExcel() {
    const rows = document.querySelectorAll('#reportsMasterTableBody tr.report-table-row:not(.d-none)');
    if (rows.length === 0) {
        showToast('لا توجد تقارير مطابقة لتصديرها', 'warning');
        return;
    }

    let excelHTML = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="content-type" content="text/plain; charset=UTF-8"/>
        <style>
            table { border-collapse: collapse; width: 100%; direction: rtl; }
            th { background-color: #1e40af; color: #ffffff; font-weight: bold; text-align: center; padding: 10px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; }
            td { text-align: center; padding: 8px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; font-size: 13px; }
            tr:nth-child(even) { background-color: #f8fafc; }
        </style>
    </head>
    <body dir="rtl">
        <h2 style="text-align: center; font-family: Cairo, Arial; color: #1e40af;">كتالوج مركز التقارير والإحصائيات المعتمد</h2>
        <p style="text-align: center; font-family: Cairo, Arial; color: #64748b;">تاريخ التصدير: ${new Date().toLocaleDateString('ar-EG')}</p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>كود التقرير</th>
                    <th>اسم التقرير الشامل</th>
                    <th>الفئة الأكاديمية / الإدارية</th>
                    <th>الصيغة والنوع المتاح</th>
                    <th>حالة الجاهزية والربط</th>
                </tr>
            </thead>
            <tbody>`;

    let count = 0;
    rows.forEach(row => {
        count++;
        const code = row.querySelector('.report-code')?.textContent.trim() || `REP-0${count}`;
        const name = row.querySelector('.report-name')?.textContent.trim() || 'تقرير غير مسمى';
        const cat = row.querySelector('.report-cat')?.textContent.trim() || 'عام';
        const type = row.querySelector('.report-type')?.textContent.trim() || 'PDF / Excel';
        const status = row.querySelector('.report-status')?.textContent.trim() || 'جاهز وموثق';

        excelHTML += `
            <tr>
                <td>${count}</td>
                <td>${escapeHtml(code)}</td>
                <td style="text-align: right;">${escapeHtml(name)}</td>
                <td>${escapeHtml(cat)}</td>
                <td>${escapeHtml(type)}</td>
                <td>${escapeHtml(status)}</td>
            </tr>`;
    });

    excelHTML += `
            </tbody>
        </table>
    </body>
    </html>`;

    const blob = new Blob(['\ufeff' + excelHTML], { type: 'application/vnd.ms-excel;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `كتالوج_التقارير_المعتمدة_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('تم تصدير كتالوج التقارير إلى Excel بنجاح', 'success');
}

function showToast(message, icon = 'info') {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        Toast.fire({
            icon: icon,
            title: message
        });
    } else {
        alert(message);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
