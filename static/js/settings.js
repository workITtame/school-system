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
        status: '✔ مكتمل',
        statusBadgeClass: 'bg-success-subtle text-success border-success-subtle',
        prev: 'SET-BAK-05',
        next: 'SET-SYS-02',
        related: [
            { name: 'الاسم الرسمي للمدرسة', icon: 'fa-school', code: 'SET-GEN-01' },
            { name: 'البريد الإلكتروني الرسمي', icon: 'fa-envelope', code: 'SET-GEN-01' },
            { name: 'رقم هاتف التواصل', icon: 'fa-phone', code: 'SET-GEN-01' },
            { name: 'العنوان والمنطقة', icon: 'fa-location-dot', code: 'SET-GEN-01' }
        ]
    },
    'SET-SYS-02': {
        code: 'SET-SYS-02',
        name: 'تفاصيل الخادم وقاعدة البيانات',
        category: 'النظام',
        tabId: 'pills-system-tab',
        formTabId: 'tabSystem',
        desc: 'استعراض حالة الاتصال الحية بالـ Database ومحرك بيئة Python 3.12 / Flask 3.x.',
        status: '✔ مكتمل',
        statusBadgeClass: 'bg-info-subtle text-info border-info-subtle',
        prev: 'SET-GEN-01',
        next: 'SET-SEC-03',
        related: [
            { name: 'نوع قاعدة البيانات MySQL', icon: 'fa-database', code: 'SET-SYS-02' },
            { name: 'مكتبات Python 3.12 / Flask', icon: 'fa-code-branch', code: 'SET-SYS-02' },
            { name: 'ربط الجداول والتزامن', icon: 'fa-link', code: 'SET-SYS-02' }
        ]
    },
    'SET-SEC-03': {
        code: 'SET-SEC-03',
        name: 'حظر الحسابات والتشفير JWT',
        category: 'الأمان',
        tabId: 'pills-general-tab',
        formTabId: 'tabGeneral',
        desc: 'خيارات تفعيل حظر المحاولات الخاطئة والتشفير الآمن بالجلسات والمعدات.',
        status: '✔ مكتمل',
        statusBadgeClass: 'bg-warning-subtle text-warning border-warning-subtle',
        prev: 'SET-SYS-02',
        next: 'SET-NOT-04',
        related: [
            { name: 'حظر المحاولات الخاطئة (5 محاولات)', icon: 'fa-user-lock', code: 'SET-SEC-03' },
            { name: 'تشفير مفاتيح HMAC JWT', icon: 'fa-key', code: 'SET-SEC-03' },
            { name: 'جدار حماية الصلاحيات', icon: 'fa-shield-halved', code: 'SET-SEC-03' }
        ]
    },
    'SET-NOT-04': {
        code: 'SET-NOT-04',
        name: 'إرسال تنبيهات غياب الطلاب',
        category: 'الإشعارات',
        tabId: 'pills-notif-tab',
        formTabId: 'tabNotif',
        desc: 'ضبط خيارات إشعارات غياب وحضور الطلاب الإلكترونية الفورية.',
        status: '⚠️ يحتاج مراجعة',
        statusBadgeClass: 'bg-warning-subtle text-warning border-warning-subtle',
        prev: 'SET-SEC-03',
        next: 'SET-BAK-05',
        related: [
            { name: 'إشعارات البريد للتأخر والغياب', icon: 'fa-paper-plane', code: 'SET-NOT-04' },
            { name: 'تنبيهات الشهادات والدرجات', icon: 'fa-graduation-cap', code: 'SET-NOT-04' }
        ]
    },
    'SET-BAK-05': {
        code: 'SET-BAK-05',
        name: 'النسخ الاحتياطي التلقائي SQL',
        category: 'النسخ الاحتياطي',
        tabId: 'pills-backup-tab',
        formTabId: 'tabBackup',
        desc: 'توليد وتحميل وتصدير نسخة احتياطية من قاعدة البيانات بصيغة SQL فورياً.',
        status: '✔ مكتمل',
        statusBadgeClass: 'bg-success-subtle text-success border-success-subtle',
        prev: 'SET-NOT-04',
        next: 'SET-GEN-01',
        related: [
            { name: 'تصدير الملفات بصيغة SQL', icon: 'fa-file-code', code: 'SET-BAK-05' },
            { name: 'الاستعادة والجاهزية الفورية', icon: 'fa-rotate-left', code: 'SET-BAK-05' }
        ]
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
    if (heroStatus) {
        heroStatus.textContent = setting.status;
        heroStatus.className = `extra-small font-monospace badge px-3 py-1 ${setting.statusBadgeClass}`;
    }

    // Populate Related Settings Grid
    const relatedContainer = document.getElementById('wsRelatedSettingsContainer');
    if (relatedContainer) {
        relatedContainer.innerHTML = '';
        if (setting.related && setting.related.length > 0) {
            setting.related.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'col-6 col-md-3';
                itemEl.innerHTML = `
                    <div class="glass-panel-card p-3 rounded-4 border-0 bg-light text-center hover-lift position-relative" style="cursor: pointer;" onclick="openSettingWorkspace('${item.code}')">
                        <div class="rounded-circle bg-white shadow-sm p-2 text-primary mx-auto mb-2 d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                            <i class="fa-solid ${item.icon} fs-6"></i>
                        </div>
                        <strong class="d-block extra-small text-dark font-monospace mb-1">${item.name}</strong>
                        <small class="text-muted extra-small font-monospace"><i class="fa-solid fa-link me-1"></i> إعداد فعال</small>
                    </div>
                `;
                relatedContainer.appendChild(itemEl);
            });
        } else {
            relatedContainer.innerHTML = `
                <div class="col-12 text-center py-3 text-muted extra-small font-monospace">
                    <i class="fa-solid fa-inbox opacity-25 fs-4 d-block mb-1"></i> لا توجد إعدادات فرعية مرتبطة
                </div>
            `;
        }
    }

    // Filter tab navigation pills so ONLY the tab corresponding to THIS specific setting is visible!
    const allTabNavs = document.querySelectorAll('#settingsTabs .nav-item');
    allTabNavs.forEach(nav => {
        const btn = nav.querySelector('.nav-link');
        if (btn && btn.id === setting.tabId) {
            nav.classList.remove('d-none');
            btn.click();
        } else {
            nav.classList.add('d-none');
        }
    });

    // Toggle View: Hide Catalog, Show Workspace smoothly
    if (catalogView) catalogView.classList.add('d-none');
    workspaceView.classList.remove('d-none');
    workspaceView.scrollIntoView({ behavior: 'smooth' });

    if (typeof showToast === 'function') {
        showToast(`تم فتح بروفايل ${setting.name}`, 'info');
    }
}

function closeSettingWorkspace() {
    const catalogView = document.getElementById('settingsCatalogView');
    const workspaceView = document.getElementById('settingWorkspace');

    // Restore all tabs when returning to catalog or general view
    const allTabNavs = document.querySelectorAll('#settingsTabs .nav-item');
    allTabNavs.forEach(nav => nav.classList.remove('d-none'));

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
    link.setAttribute('download', `Settings_Catalog_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    if (typeof showToast === 'function') {
        showToast('تم تصدير سجل الإعدادات بنجاح إلى ملف Excel CSV', 'success');
    }
}
