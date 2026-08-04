/* ==========================================================================
   ENTERPRISE SAAS SETTINGS WORKSPACE CONTROLLER (static/js/settings.js)
   ========================================================================== */

let currentWorkspaceCode = 'SET-GEN-01';

const SETTINGS_REGISTRY = {
    'SET-GEN-01': {
        code: 'SET-GEN-01',
        name: 'إعدادات المدرسة والتواصل',
        category: 'المدرسة',
        tabId: 'pills-general-tab',
        formTabId: 'tabGeneral',
        desc: 'إدارة الاسم الرسمي للمدرسة، بريد التواصل، هاتف الإدارة والعنوان الجغرافي وخيارات الأمان.',
        status: 'مفعلة وموثقة',
        prev: 'SET-BAK-05',
        next: 'SET-SYS-02'
    },
    'SET-SYS-02': {
        code: 'SET-SYS-02',
        name: 'تفاصيل الخادم وقاعدة البيانات',
        category: 'النظام',
        tabId: 'pills-system-tab',
        formTabId: 'tabSystem',
        desc: 'استعراض حالة الاتصال الحية بالـ Database ومحرك بيئة Python 3.12 / Flask 3.x.',
        status: 'متصل حياً',
        prev: 'SET-GEN-01',
        next: 'SET-SEC-03'
    },
    'SET-SEC-03': {
        code: 'SET-SEC-03',
        name: 'حظر الحسابات والتشفير JWT',
        category: 'الأمان',
        tabId: 'pills-general-tab',
        formTabId: 'tabGeneral',
        desc: 'خيارات تفعيل حظر المحاولات الخاطئة والتشفير الآمن بالجلسات والمعدات.',
        status: 'نشط ومفعل',
        prev: 'SET-SYS-02',
        next: 'SET-NOT-04'
    },
    'SET-NOT-04': {
        code: 'SET-NOT-04',
        name: 'إرسال تنبيهات غياب الطلاب',
        category: 'الإشعارات',
        tabId: 'pills-notif-tab',
        formTabId: 'tabNotif',
        desc: 'ضبط خيارات إشعارات غياب وحضور الطلاب الإلكترونية الفورية.',
        status: 'مفعلة',
        prev: 'SET-SEC-03',
        next: 'SET-BAK-05'
    },
    'SET-BAK-05': {
        code: 'SET-BAK-05',
        name: 'النسخ الاحتياطي التلقائي SQL',
        category: 'النسخ الاحتياطي',
        tabId: 'pills-backup-tab',
        formTabId: 'tabBackup',
        desc: 'توليد وتحميل وتصدير نسخة احتياطية من قاعدة البيانات بصيغة SQL فورياً.',
        status: 'جاهز 100%',
        prev: 'SET-NOT-04',
        next: 'SET-GEN-01'
    }
};

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
    window.openSettingWorkspace = openSettingWorkspace;
    window.closeSettingWorkspace = closeSettingWorkspace;
    window.navigateWorkspace = navigateWorkspace;

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

function openSettingWorkspace(code) {
    const catalogView = document.getElementById('settingsCatalogView');
    const workspaceView = document.getElementById('settingWorkspace');
    if (!workspaceView) return;

    const setting = SETTINGS_REGISTRY[code] || SETTINGS_REGISTRY['SET-GEN-01'];
    currentWorkspaceCode = setting.code;

    // Populate Workspace Hero & Information
    const heroCode = document.getElementById('wsHeroCode');
    const heroName = document.getElementById('wsHeroName');
    const heroCategory = document.getElementById('wsHeroCategory');
    const heroDesc = document.getElementById('wsHeroDesc');
    const heroStatus = document.getElementById('wsHeroStatus');

    if (heroCode) heroCode.textContent = setting.code;
    if (heroName) heroName.textContent = setting.name;
    if (heroCategory) heroCategory.textContent = setting.category;
    if (heroDesc) heroDesc.textContent = setting.desc;
    if (heroStatus) heroStatus.textContent = setting.status;

    // Trigger target Tab in Workspace Form Panel
    const targetTabBtn = document.getElementById(setting.tabId);
    if (targetTabBtn) {
        targetTabBtn.click();
    }

    // Toggle View: Hide Catalog, Show Workspace smoothly
    if (catalogView) catalogView.classList.add('d-none');
    workspaceView.classList.remove('d-none');
    workspaceView.scrollIntoView({ behavior: 'smooth' });

    if (typeof showToast === 'function') {
        showToast(`تم فتح مساحة عمل ${setting.name}`, 'info');
    }
}

function closeSettingWorkspace() {
    const catalogView = document.getElementById('settingsCatalogView');
    const workspaceView = document.getElementById('settingWorkspace');

    if (workspaceView) workspaceView.classList.add('d-none');
    if (catalogView) {
        catalogView.classList.remove('d-none');
        catalogView.scrollIntoView({ behavior: 'smooth' });
    }
}

function navigateWorkspace(direction) {
    const setting = SETTINGS_REGISTRY[currentWorkspaceCode] || SETTINGS_REGISTRY['SET-GEN-01'];
    const targetCode = direction === 'next' ? setting.next : setting.prev;
    openSettingWorkspace(targetCode);
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
