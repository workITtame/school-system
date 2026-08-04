/* ==========================================================================
   ENTERPRISE SAAS SETTINGS CENTER CONTROLLER (static/js/settings.js)
   ========================================================================== */

document.addEventListener('turbo:load', function() {
    initSettingsModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initSettingsModule();
});

function initSettingsModule() {
    const rootEl = document.getElementById('settingsModuleRoot');
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    // Register global window handlers
    window.exportSettingsMasterExcel = exportSettingsMasterExcel;
    window.filterSettingsCatalog = filterSettingsCatalog;
    window.resetSettingsFilters = resetSettingsFilters;

    setupSettingsEventListeners();
}

function setupSettingsEventListeners() {
    const searchInput = document.getElementById('settingsFilterSearch');
    const categorySelect = document.getElementById('settingsFilterCategory');
    const resetBtn = document.getElementById('settingsResetFiltersBtn');

    if (searchInput) searchInput.addEventListener('input', filterSettingsCatalog);
    if (categorySelect) categorySelect.addEventListener('change', filterSettingsCatalog);
    if (resetBtn) resetBtn.addEventListener('click', resetSettingsFilters);
}

function filterSettingsCatalog() {
    const searchVal = document.getElementById('settingsFilterSearch')?.value.toLowerCase().trim() || '';
    const catVal = document.getElementById('settingsFilterCategory')?.value || '';
    const badgeEl = document.getElementById('settingsActiveFiltersBadge');

    let isFiltered = searchVal !== '' || catVal !== '';
    if (badgeEl) {
        if (isFiltered) badgeEl.classList.remove('d-none');
        else badgeEl.classList.add('d-none');
    }

    // Filter Category Cards
    const cards = document.querySelectorAll('.settings-category-card');
    let visibleCards = 0;
    cards.forEach(card => {
        const title = card.dataset.title ? card.dataset.title.toLowerCase() : '';
        const cat = card.dataset.category || '';

        const matchesSearch = !searchVal || title.includes(searchVal);
        const matchesCat = !catVal || cat === catVal;

        if (matchesSearch && matchesCat) {
            card.parentElement.classList.remove('d-none');
            visibleCards++;
        } else {
            card.parentElement.classList.add('d-none');
        }
    });

    // Filter Table Rows
    const rows = document.querySelectorAll('#settingsMasterTableBody tr.settings-table-row');
    let visibleRows = 0;
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const cat = row.dataset.category || '';

        const matchesSearch = !searchVal || text.includes(searchVal);
        const matchesCat = !catVal || cat === catVal;

        if (matchesSearch && matchesCat) {
            row.classList.remove('d-none');
            visibleRows++;
        } else {
            row.classList.add('d-none');
        }
    });

    // Handle Empty States
    const cardsEmptyState = document.getElementById('settingsCardsEmptyState');
    const tableEmptyState = document.getElementById('settingsTableEmptyState');

    if (cardsEmptyState) {
        if (visibleCards === 0) cardsEmptyState.classList.remove('d-none');
        else cardsEmptyState.classList.add('d-none');
    }

    if (tableEmptyState) {
        if (visibleRows === 0) tableEmptyState.classList.remove('d-none');
        else tableEmptyState.classList.add('d-none');
    }
}

function resetSettingsFilters() {
    const searchInput = document.getElementById('settingsFilterSearch');
    const categorySelect = document.getElementById('settingsFilterCategory');

    if (searchInput) searchInput.value = '';
    if (categorySelect) categorySelect.value = '';

    filterSettingsCatalog();
    if (typeof showToast === 'function') {
        showToast('تمت إعادة ضبط فلاتر الإعدادات بنجاح', 'info');
    }
}

function exportSettingsMasterExcel() {
    const rows = document.querySelectorAll('#settingsMasterTableBody tr.settings-table-row:not(.d-none)');
    if (!rows || rows.length === 0) {
        if (typeof showToast === 'function') showToast('لا توجد إعدادات مصفاة للتصدير', 'warning');
        else alert('لا توجد إعدادات مصفاة للتصدير');
        return;
    }

    let csvContent = "\uFEFFكود الإعداد,اسم الإعداد الشامل,الفئة النظامية,الحالة التشغيلية\n";

    rows.forEach(row => {
        const code = row.querySelector('.setting-code')?.textContent.trim() || '';
        const name = row.querySelector('.setting-name')?.textContent.trim() || '';
        const cat = row.querySelector('.setting-cat')?.textContent.trim() || '';
        const status = row.querySelector('.setting-status')?.textContent.trim() || '';

        csvContent += `"${code}","${name}","${cat}","${status}"\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Enterprise_Settings_Catalog_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    if (typeof showToast === 'function') {
        showToast('تم تصدير كتالوج الإعدادات بنجاح إلى ملف Excel CSV', 'success');
    }
}
