/* ==========================================================================
   ENTERPRISE SAAS MESSAGES & NOTIFICATIONS CONTROLLER (static/js/messages.js)
   ========================================================================== */

let messagesState = {
    conversations: [],
    activeRecipientId: null,
    selectedIds: new Set()
};

document.addEventListener('turbo:load', function() {
    initMessagesModule();
});

document.addEventListener('DOMContentLoaded', function() {
    initMessagesModule();
});

function initMessagesModule() {
    const rootEl = document.getElementById('messagesModuleRoot');
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    // Register global window handlers
    window.loadMessagesData = loadMessagesData;
    window.exportMessagesExcel = exportMessagesExcel;
    window.selectConversation = selectConversation;
    window.toggleSelectAllMessages = toggleSelectAllMessages;
    window.toggleMessageSelection = toggleMessageSelection;
    window.clearMessageBulkSelections = clearMessageBulkSelections;
    window.switchMessagesTab = switchMessagesTab;
    window.viewMessageProfile = viewMessageProfile;
    window.printMessageProfile = printMessageProfile;
    window.exportMessageProfileExcel = exportMessageProfileExcel;
    window.viewNotificationProfile = viewNotificationProfile;
    window.openComposerModal = openComposerModal;
    window.sendComposerMessage = sendComposerMessage;
    window.openBulkComposerModal = openBulkComposerModal;
    window.toggleBulkRecipientAll = toggleBulkRecipientAll;
    window.sendBulkMessages = sendBulkMessages;
    window.openTemplatesModal = openTemplatesModal;
    window.exportMessagesAnalyticsExcel = exportMessagesAnalyticsExcel;

    setupMessagesEventListeners();
    loadConversations();
}

function setupMessagesEventListeners() {
    const searchInput = document.getElementById('msgFilterSearch');
    const roleSelect = document.getElementById('msgFilterRole');
    const statusSelect = document.getElementById('msgFilterStatus');
    const resetBtn = document.getElementById('msgResetFiltersBtn');
    const msgForm = document.getElementById('msgMessageForm');

    if (searchInput) searchInput.addEventListener('input', applyMessagesFilters);
    if (roleSelect) roleSelect.addEventListener('change', applyMessagesFilters);
    if (statusSelect) statusSelect.addEventListener('change', applyMessagesFilters);

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (roleSelect) roleSelect.value = '';
            if (statusSelect) statusSelect.value = '';
            applyMessagesFilters();
        });
    }

    if (msgForm) {
        msgForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessageSubmit();
        });
    }
}

function loadMessagesData() {
    loadConversations();
    if (messagesState.activeRecipientId) {
        loadThread(messagesState.activeRecipientId);
    }
}

function loadConversations() {
    const convList = document.getElementById('msgConversationsList');
    if (convList) {
        convList.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><div class="small text-muted mt-2 font-monospace">جاري تحميل المحادثات...</div></div>';
    }

    fetch('/messages/api/conversations')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                messagesState.conversations = data.conversations || [];
                updateMessagesKPIs();
                renderConversations(messagesState.conversations);
                renderMessagesDataGrid(messagesState.conversations);
                updateMessagesAnalyticsUI(messagesState.conversations);
            }
        })
        .catch(err => {
            console.error('Error loading conversations:', err);
            if (convList) convList.innerHTML = '<div class="text-center py-4 text-danger font-monospace small"><i class="fa-solid fa-triangle-exclamation me-1"></i> تعذر تحميل البيانات</div>';
        });
}

function updateMessagesKPIs() {
    const convs = messagesState.conversations;
    let totalMessages = convs.length;
    let unreadCount = 0;

    convs.forEach(c => {
        if (c.unread_count > 0) {
            unreadCount += c.unread_count;
        }
    });

    let readCount = Math.max(0, totalMessages - unreadCount);
    let readRate = totalMessages > 0 ? Math.round((readCount / totalMessages) * 100) : 100;

    const elTotal = document.getElementById('kpiTotalMessages');
    const elUnread = document.getElementById('kpiUnreadMessages');
    const elRead = document.getElementById('kpiReadMessages');
    const elConvs = document.getElementById('kpiTotalConversations');
    const elRate = document.getElementById('kpiReadRate');
    const elProgressBar = document.getElementById('kpiReadRateBar');

    if (elTotal) elTotal.textContent = totalMessages;
    if (elUnread) elUnread.textContent = unreadCount;
    if (elRead) elRead.textContent = readCount;
    if (elConvs) elConvs.textContent = convs.length;
    if (elRate) elRate.textContent = `${readRate}%`;
    if (elProgressBar) elProgressBar.style.width = `${readRate}%`;
}

function renderConversations(list) {
    const convList = document.getElementById('msgConversationsList');
    if (!convList) return;

    convList.innerHTML = '';
    if (!list || list.length === 0) {
        convList.innerHTML = `
            <div class="text-center py-5 text-muted font-monospace p-3">
                <i class="fa-solid fa-comments fs-2 text-muted opacity-25 d-block mb-2"></i>
                <div class="small fw-bold">لا توجد محادثات مطابقة</div>
            </div>`;
        return;
    }

    list.forEach(item => {
        const div = document.createElement('div');
        div.className = `conversation-item p-3 border-bottom d-flex align-items-center justify-content-between ${messagesState.activeRecipientId === item.user_id ? 'active bg-primary bg-opacity-10' : ''}`;
        div.onclick = () => selectConversation(item.user_id, item.name, item.role);

        div.innerHTML = `
            <div class="d-flex align-items-center gap-3 overflow-hidden">
                <div class="position-relative flex-shrink-0">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(item.name)}&background=2563eb&color=fff" class="rounded-circle" style="width: 44px; height: 44px; object-fit: cover;">
                    ${item.unread_count > 0 ? '<span class="position-absolute top-0 start-0 p-1 bg-danger border border-light rounded-circle"></span>' : ''}
                </div>
                <div class="overflow-hidden">
                    <h6 class="mb-0 fw-bold text-dark text-truncate font-monospace" style="font-size: 0.92rem;">${escapeHtml(item.name)}</h6>
                    <small class="text-muted text-truncate d-block font-monospace extra-small">${escapeHtml(item.last_message)}</small>
                </div>
            </div>
            <div class="text-end flex-shrink-0 ms-2 font-monospace">
                <span class="badge ${item.role === 'مدير النظام' ? 'bg-primary-subtle text-primary' : 'bg-info-subtle text-info'} rounded-pill extra-small px-2 py-1 mb-1 d-block">${escapeHtml(item.role)}</span>
                <small class="text-muted d-block extra-small">${item.last_time ? item.last_time.split(' ')[0] : ''}</small>
                ${item.unread_count > 0 ? `<span class="badge bg-danger rounded-circle extra-small mt-1">${item.unread_count}</span>` : ''}
            </div>
        `;
        convList.appendChild(div);
    });
}

function renderMessagesDataGrid(list) {
    const tbody = document.getElementById('msgGridTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-muted font-monospace">
                    <i class="fa-solid fa-inbox fs-1 mb-3 text-muted opacity-50 d-block"></i>
                    <h5 class="fw-bold">لا توجد رسائل أو محادثات مسجلة حالياً</h5>
                    <p class="small text-muted">يمكنك البدء بمراسلة المعلمين أو الإدارة عبر أزرار التحكم أعلاه.</p>
                </td>
            </tr>`;
        return;
    }

    let count = 0;
    list.forEach(item => {
        count++;
        const tr = document.createElement('tr');
        tr.className = 'align-middle msg-grid-row';
        tr.dataset.userId = item.user_id;
        tr.dataset.role = item.role;
        tr.dataset.unread = item.unread_count;

        const isUnread = item.unread_count > 0;
        const statusBadge = isUnread 
            ? `<span class="badge bg-warning-subtle text-warning rounded-pill px-3 py-1 font-monospace extra-small"><i class="fa-solid fa-envelope me-1"></i>غير مقروءة (${item.unread_count})</span>`
            : `<span class="badge bg-success-subtle text-success rounded-pill px-3 py-1 font-monospace extra-small"><i class="fa-solid fa-envelope-open me-1"></i>مقروءة</span>`;

        tr.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input rounded-2" onclick="toggleMessageSelection(${item.user_id}, event)">
            </td>
            <td class="fw-bold text-muted font-monospace">${count}</td>
            <td class="text-start">
                <div class="d-flex align-items-center gap-3">
                    <div class="p-2 rounded-circle ${isUnread ? 'bg-warning' : 'bg-primary'} bg-opacity-10 ${isUnread ? 'text-warning' : 'text-primary'}">
                        <i class="fa-solid ${isUnread ? 'fa-envelope' : 'fa-comments'} fs-5"></i>
                    </div>
                    <div>
                        <strong class="d-block text-dark font-monospace text-truncate" style="max-width: 320px;">${escapeHtml(item.last_message)}</strong>
                        <small class="text-muted extra-small font-monospace">محادثة مع ${escapeHtml(item.name)}</small>
                    </div>
                </div>
            </td>
            <td class="font-monospace fw-bold text-dark">
                <div class="d-flex align-items-center justify-content-center gap-2">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(item.name)}&background=2563eb&color=fff" class="rounded-circle" style="width: 28px; height: 28px;">
                    <span>${escapeHtml(item.name)}</span>
                </div>
            </td>
            <td>
                <span class="badge ${item.role === 'مدير النظام' ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-info-subtle text-info border border-info-subtle'} rounded-pill px-3 py-1 font-monospace extra-small">
                    ${escapeHtml(item.role)}
                </span>
            </td>
            <td class="font-monospace text-muted small fw-bold">
                ${item.last_time || '—'}
            </td>
            <td>
                ${statusBadge}
            </td>
            <td>
                <div class="d-flex justify-content-center gap-1">
                    <button type="button" class="btn btn-sm btn-light border rounded-pill px-2 fw-bold font-monospace extra-small text-dark" title="عرض الملف الشخصي للرسالة والمحادثات" onclick="viewMessageProfile(${item.user_id}, '${escapeJsString(item.name)}', '${escapeJsString(item.role)}')">
                        <i class="fa-solid fa-eye text-primary me-1"></i> عرض
                    </button>
                    <button type="button" class="btn btn-sm btn-light border rounded-pill px-2 fw-bold font-monospace extra-small text-primary" title="المحادثة الحية" onclick="selectConversation(${item.user_id}, '${escapeJsString(item.name)}', '${escapeJsString(item.role)}')">
                        <i class="fa-solid fa-comments me-1"></i> محادثة
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function applyMessagesFilters() {
    const searchVal = document.getElementById('msgFilterSearch')?.value.toLowerCase().trim() || '';
    const roleVal   = document.getElementById('msgFilterRole')?.value || '';
    const statusVal = document.getElementById('msgFilterStatus')?.value || '';

    const filteredConvs = messagesState.conversations.filter(item => {
        let match = true;

        if (searchVal) {
            const nameMatch = item.name.toLowerCase().includes(searchVal);
            const msgMatch  = item.last_message.toLowerCase().includes(searchVal);
            if (!nameMatch && !msgMatch) match = false;
        }

        if (roleVal && item.role !== roleVal) match = false;

        if (statusVal === 'unread' && item.unread_count === 0) match = false;
        if (statusVal === 'read'   && item.unread_count > 0) match = false;

        return match;
    });

    renderConversations(filteredConvs);
    renderMessagesDataGrid(filteredConvs);

    const activeBadge = document.getElementById('msgActiveFiltersBadge');
    if (activeBadge) {
        if (searchVal || roleVal || statusVal) {
            activeBadge.classList.remove('d-none');
        } else {
            activeBadge.classList.add('d-none');
        }
    }
}

function selectConversation(userId, name, role) {
    messagesState.activeRecipientId = userId;

    switchMessagesTab('chat');

    const emptyState = document.getElementById('msgChatEmptyState');
    const chatHeader = document.getElementById('msgChatHeader');
    const chatBody   = document.getElementById('msgChatBody');
    const chatFooter = document.getElementById('msgChatFooter');

    if (emptyState) emptyState.classList.add('d-none');
    if (chatHeader) { chatHeader.classList.remove('d-none'); chatHeader.classList.add('d-flex'); }
    if (chatBody)   chatBody.classList.remove('d-none');
    if (chatFooter) chatFooter.classList.remove('d-none');

    const userNameEl = document.getElementById('msgChatUserName');
    const userRoleEl = document.getElementById('msgChatUserRole');
    const avatarEl   = document.getElementById('msgChatAvatar');

    if (userNameEl) userNameEl.textContent = name;
    if (userRoleEl) userRoleEl.textContent = role;
    if (avatarEl)   avatarEl.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=2563eb&color=fff`;

    renderConversations(messagesState.conversations);
    loadThread(userId);
}

function loadThread(userId) {
    const container = document.getElementById('msgContainer');
    const chatBody  = document.getElementById('msgChatBody');
    if (!container) return;

    container.innerHTML = '<div class="text-center py-5 font-monospace"><div class="spinner-border text-primary" role="status"></div><div class="small text-muted mt-2">جاري جلب الرسائل...</div></div>';

    fetch(`/messages/api/thread/${userId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                container.innerHTML = '';
                if (!data.messages || data.messages.length === 0) {
                    container.innerHTML = `
                        <div class="text-center py-5 text-muted font-monospace">
                            <i class="fa-solid fa-paper-plane fs-1 opacity-25 d-block mb-3 text-primary"></i>
                            <h6 class="fw-bold">لا توجد رسائل سابقة مع هذا المستخدم</h6>
                            <p class="extra-small text-muted mb-0">اكتب رسالتك الأولى بالأسفل للبدء والتواصل الحقيقي المباشر.</p>
                        </div>`;
                } else {
                    data.messages.forEach(msg => {
                        const div = document.createElement('div');
                        div.className = `message-bubble ${msg.is_mine ? 'message-mine' : 'message-other'}`;
                        div.innerHTML = `
                            <div class="font-monospace">${escapeHtml(msg.content)}</div>
                            <div class="text-start opacity-75 mt-1 font-monospace extra-small">${msg.time || ''}</div>
                        `;
                        container.appendChild(div);
                    });
                }
                if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;

                loadConversations();
            }
        })
        .catch(err => {
            console.error('Error loading thread:', err);
            container.innerHTML = '<div class="text-center py-4 text-danger font-monospace small"><i class="fa-solid fa-triangle-exclamation me-1"></i> تعذر تحميل الرسائل</div>';
        });
}

function sendMessageSubmit() {
    const input = document.getElementById('msgInput');
    if (!input || !messagesState.activeRecipientId) return;

    const text = input.value.trim();
    if (!text) return;

    fetch('/messages/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_id: messagesState.activeRecipientId, content: text })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            loadThread(messagesState.activeRecipientId);
            showToast('تم إرسال الرسالة بنجاح', 'success');
        } else {
            showToast(data.message || 'حدث خطأ أثناء الإرسال', 'error');
        }
    })
    .catch(err => {
        console.error('Error sending message:', err);
        showToast('تعذر الإرسال، الرجاء المحاولة لاحقاً', 'error');
    });
}

function switchMessagesTab(tabName) {
    const gridPane = document.getElementById('msgPaneGrid');
    const chatPane = document.getElementById('msgPaneChat');
    const analyticsPane = document.getElementById('msgPaneAnalytics');

    const tabGrid  = document.getElementById('msgTabGridBtn');
    const tabChat  = document.getElementById('msgTabChatBtn');
    const tabAnalytics = document.getElementById('msgTabAnalyticsBtn');

    if (gridPane) gridPane.classList.add('d-none');
    if (chatPane) chatPane.classList.add('d-none');
    if (analyticsPane) analyticsPane.classList.add('d-none');

    if (tabGrid) { tabGrid.classList.remove('active', 'btn-primary'); tabGrid.classList.add('btn-light'); }
    if (tabChat) { tabChat.classList.remove('active', 'btn-primary'); tabChat.classList.add('btn-light'); }
    if (tabAnalytics) { tabAnalytics.classList.remove('active', 'btn-primary'); tabAnalytics.classList.add('btn-light'); }

    if (tabName === 'grid') {
        if (gridPane) gridPane.classList.remove('d-none');
        if (tabGrid)  { tabGrid.classList.add('active', 'btn-primary'); tabGrid.classList.remove('btn-light'); }
    } else if (tabName === 'chat') {
        if (chatPane) chatPane.classList.remove('d-none');
        if (tabChat)  { tabChat.classList.add('active', 'btn-primary'); tabChat.classList.remove('btn-light'); }
    } else if (tabName === 'analytics') {
        if (analyticsPane) analyticsPane.classList.remove('d-none');
        if (tabAnalytics)  { tabAnalytics.classList.add('active', 'btn-primary'); tabAnalytics.classList.remove('btn-light'); }
        initMessagesAnalyticsCharts();
    }
}

function toggleSelectAllMessages(masterCb) {
    messagesState.selectedIds.clear();
    const rows = document.querySelectorAll('#msgGridTableBody tr.msg-grid-row:not(.d-none)');

    rows.forEach(row => {
        const cb = row.querySelector('input[type="checkbox"]');
        if (cb) {
            cb.checked = masterCb.checked;
            if (masterCb.checked && row.dataset.userId) {
                messagesState.selectedIds.add(row.dataset.userId);
            }
        }
    });

    updateMessagesBulkBar();
}

function toggleMessageSelection(id, event) {
    if (event) event.stopPropagation();
    const cb = event.target;

    if (cb.checked) {
        messagesState.selectedIds.add(id);
    } else {
        messagesState.selectedIds.delete(id);
    }

    updateMessagesBulkBar();
}

function clearMessageBulkSelections() {
    messagesState.selectedIds.clear();
    const master = document.getElementById('selectAllMessages');
    if (master) master.checked = false;

    const checkboxes = document.querySelectorAll('#msgGridTableBody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);

    updateMessagesBulkBar();
}

function updateMessagesBulkBar() {
    const bulkBar = document.getElementById('messagesBulkBar');
    const countBadge = document.getElementById('bulkSelectedMessagesCount');
    const count = messagesState.selectedIds.size;

    if (!bulkBar) return;

    if (count > 0) {
        bulkBar.classList.remove('d-none');
        if (countBadge) countBadge.textContent = `${count} محدد`;
    } else {
        bulkBar.classList.add('d-none');
    }
}

function exportMessagesExcel() {
    const convs = messagesState.conversations;
    if (!convs || convs.length === 0) {
        showToast('لا توجد بيانات رسائل لتصديرها', 'warning');
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
        <h2 style="text-align: center; font-family: Cairo, Arial; color: #1e40af;">سجل مركز الرسائل والمحادثات الأكاديمية</h2>
        <p style="text-align: center; font-family: Cairo, Arial; color: #64748b;">تاريخ التصدير: ${new Date().toLocaleDateString('ar-EG')}</p>
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;">#</th>
                    <th>المستخدم</th>
                    <th>الدور الوظيفي</th>
                    <th>آخر رسالة</th>
                    <th>تاريخ/وقت التحديث</th>
                    <th>عدد الرسائل غير المقروءة</th>
                </tr>
            </thead>
            <tbody>`;

    convs.forEach((item, idx) => {
        excelHTML += `
            <tr>
                <td>${idx + 1}</td>
                <td>${escapeHtml(item.name)}</td>
                <td>${escapeHtml(item.role)}</td>
                <td style="text-align: right;">${escapeHtml(item.last_message)}</td>
                <td>${item.last_time || '—'}</td>
                <td>${item.unread_count || 0}</td>
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
    a.download = `سجل_الرسائل_والمحادثات_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('تم تصدير ملف Excel للرسائل بنجاح', 'success');
}

function showToast(message, icon) {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        Toast.fire({ icon: icon, title: message });
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

function escapeJsString(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

/* ==========================================================================
   10-SECTION MESSAGE & NOTIFICATION PROFILE CONTROLLER
   ========================================================================== */

function viewMessageProfile(userId, name, role) {
    const modalEl = document.getElementById('viewMessageProfileModal');
    if (!modalEl) return;

    const codeBadge   = document.getElementById('msgp-code-badge');
    const heroTitle   = document.getElementById('msgp-hero-title');
    const heroSub     = document.getElementById('msgp-hero-subtitle');
    const recipientEl = document.getElementById('msgp-info-recipient');
    const roleBadge   = document.getElementById('msgp-role-badge');
    const targetAvatar= document.getElementById('msgp-target-avatar');

    if (codeBadge)   codeBadge.textContent = `MSG-${userId}`;
    if (heroTitle)   heroTitle.textContent = `الملف الشخصي للمحادثة والرسائل | ${name}`;
    if (heroSub)     heroSub.textContent = `طرف التواصل: ${name} (${role}) | المعرف الرقمي: USER-${userId}`;
    if (recipientEl) recipientEl.textContent = `${name} (${role})`;
    if (roleBadge)   roleBadge.textContent = role;
    if (targetAvatar) targetAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=2563eb&color=fff`;

    const threadBox = document.getElementById('msgp-thread-container');
    if (threadBox) {
        threadBox.innerHTML = '<div class="text-center py-4 font-monospace"><div class="spinner-border text-primary" role="status"></div><div class="small text-muted mt-2">جاري جلب تفاصيل المحادثة...</div></div>';
    }

    fetch(`/messages/api/thread/${userId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const msgs = data.messages || [];

                const kpiCount  = document.getElementById('msgp-kpi-count');
                const kpiStatus = document.getElementById('msgp-kpi-status');
                const kpiLast   = document.getElementById('msgp-kpi-last-active');

                if (kpiCount)  kpiCount.textContent  = msgs.length;
                if (kpiStatus) kpiStatus.textContent = msgs.length > 0 ? 'نشطة ومطلّع عليها' : 'محادثة جديدة';
                if (kpiLast)   kpiLast.textContent   = msgs.length > 0 ? msgs[msgs.length - 1].time : '—';

                const infoContent = document.getElementById('msgp-info-content');
                const infoTime    = document.getElementById('msgp-info-time');

                if (infoContent) {
                    infoContent.textContent = msgs.length > 0 
                        ? msgs[msgs.length - 1].content 
                        : 'لا توجد رسائل سابقة مسجلة في هذا التكليف الدراسي.';
                }
                if (infoTime) {
                    infoTime.textContent = msgs.length > 0 ? msgs[msgs.length - 1].time : '—';
                }

                if (threadBox) {
                    threadBox.innerHTML = '';
                    if (msgs.length === 0) {
                        threadBox.innerHTML = `
                            <div class="text-center py-4 text-muted font-monospace p-3">
                                <i class="fa-solid fa-comments opacity-25 fs-1 d-block mb-2"></i>
                                <span>لا توجد رسائل سابقة في السلسلة. يمكنك الرد والمراسلة الآن.</span>
                            </div>`;
                    } else {
                        msgs.forEach(m => {
                            const msgDiv = document.createElement('div');
                            msgDiv.className = `p-3 rounded-4 mb-2 border ${m.is_mine ? 'bg-primary-subtle border-primary-subtle text-primary ms-4' : 'bg-white border-light text-dark me-4'}`;
                            msgDiv.innerHTML = `
                                <div class="d-flex align-items-center justify-content-between mb-1">
                                    <strong class="font-monospace small">${m.is_mine ? 'أنت (المرسل)' : escapeHtml(name)}</strong>
                                    <small class="text-muted extra-small">${m.time}</small>
                                </div>
                                <p class="mb-0 font-monospace small">${escapeHtml(m.content)}</p>
                            `;
                            threadBox.appendChild(msgDiv);
                        });
                    }
                }

                const timelineContainer = document.getElementById('msgp-timeline-box');
                if (timelineContainer) {
                    const lastTime = msgs.length > 0 ? msgs[msgs.length - 1].time : 'اليوم';
                    timelineContainer.innerHTML = `
                        <div class="d-flex gap-3 align-items-start mb-3">
                            <div class="p-2 rounded-circle bg-success text-white"><i class="fa-solid fa-check"></i></div>
                            <div>
                                <strong class="d-block text-dark small">تم فتح وإنشاء السلسلة المحادثات</strong>
                                <small class="text-muted extra-small">المستخدم المخاطب: ${escapeHtml(name)} (${escapeHtml(role)})</small>
                            </div>
                        </div>
                        <div class="d-flex gap-3 align-items-start">
                            <div class="p-2 rounded-circle bg-primary text-white"><i class="fa-solid fa-clock"></i></div>
                            <div>
                                <strong class="d-block text-dark small">آخر نشاط وتحديث للرسائل</strong>
                                <small class="text-muted extra-small">الوقت: ${lastTime}</small>
                            </div>
                        </div>`;
                }
            }
        });

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function printMessageProfile() {
    window.print();
}

function exportMessageProfileExcel() {
    exportMessagesExcel();
}

function viewNotificationProfile(id, title, category, time, read) {
    const modalEl = document.getElementById('viewNotificationProfileModal');
    if (!modalEl) return;

    const badgeEl    = document.getElementById('notifp-code-badge');
    const titleEl    = document.getElementById('notifp-title');
    const categoryEl = document.getElementById('notifp-category');
    const timeEl     = document.getElementById('notifp-time');
    const statusEl   = document.getElementById('notifp-status');

    if (badgeEl)    badgeEl.textContent    = `NOTIF-${id}`;
    if (titleEl)    titleEl.textContent    = title || 'تفاصيل الإشعار الأكاديمي';
    if (categoryEl) categoryEl.textContent = category || 'عام';
    if (timeEl)     timeEl.textContent     = time || 'الآن';
    if (statusEl)   statusEl.textContent   = read ? 'تم الاطلاع والاعتماد' : 'إشعار جديد غير مقروء';

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

/* ==========================================================================
   PHASE 3: MESSAGE COMPOSER & BULK MESSAGING CONTROLLER
   ========================================================================== */

function openComposerModal(targetRecipientId = null) {
    const modalEl = document.getElementById('newMessageComposerModal');
    if (!modalEl) return;

    const recipientSelect = document.getElementById('composerRecipientSelect');
    const contentInput = document.getElementById('composerContentInput');
    const charCounter = document.getElementById('composerCharCounter');

    if (contentInput) {
        contentInput.value = '';
        contentInput.classList.remove('is-invalid');
    }
    if (charCounter) charCounter.textContent = '0';

    if (recipientSelect) {
        recipientSelect.innerHTML = '<option value="">-- اختر المستلم المخاطب من القائمة --</option>';
        if (messagesState.conversations && messagesState.conversations.length > 0) {
            messagesState.conversations.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.user_id;
                opt.textContent = `${c.name} (${c.role})`;
                if (targetRecipientId && parseInt(targetRecipientId) === c.user_id) {
                    opt.selected = true;
                }
                recipientSelect.appendChild(opt);
            });
        }
    }

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function sendComposerMessage() {
    const recipientSelect = document.getElementById('composerRecipientSelect');
    const contentInput = document.getElementById('composerContentInput');
    const sendBtn = document.getElementById('composerSendBtn');

    const recipientId = recipientSelect?.value;
    const content = contentInput?.value.trim();

    let isValid = true;

    if (!recipientId) {
        if (recipientSelect) recipientSelect.classList.add('is-invalid');
        showToast('يرجى اختيار المستلم المخاطب من القائمة', 'warning');
        isValid = false;
    } else {
        if (recipientSelect) recipientSelect.classList.remove('is-invalid');
    }

    if (!content) {
        if (contentInput) contentInput.classList.add('is-invalid');
        showToast('يرجى كتابة نص الرسالة قبل الإرسال', 'warning');
        isValid = false;
    } else {
        if (contentInput) contentInput.classList.remove('is-invalid');
    }

    if (!isValid) return;

    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> جاري الإرسال...';
    }

    fetch('/messages/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_id: parseInt(recipientId), content: content })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast('تم إرسال الرسالة بنجاح', 'success');
            const modalEl = document.getElementById('newMessageComposerModal');
            const bsModal = bootstrap.Modal.getInstance(modalEl);
            if (bsModal) bsModal.hide();

            loadConversations();
        } else {
            showToast(data.message || 'تعذر إرسال الرسالة', 'error');
        }
    })
    .catch(err => {
        showToast('حدث خطأ أثناء الإرسال', 'error');
    })
    .finally(() => {
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-1"></i> إرسال الرسالة';
        }
    });
}

function openBulkComposerModal() {
    const modalEl = document.getElementById('bulkMessageComposerModal');
    if (!modalEl) return;

    const recipientsList = document.getElementById('bulkRecipientsList');
    const contentInput = document.getElementById('bulkComposerContentInput');
    const progressContainer = document.getElementById('bulkProgressContainer');
    const selectAllCheck = document.getElementById('bulkSelectAllCheck');

    if (contentInput) {
        contentInput.value = '';
        contentInput.classList.remove('is-invalid');
    }
    if (progressContainer) progressContainer.classList.add('d-none');
    if (selectAllCheck) selectAllCheck.checked = false;

    if (recipientsList) {
        recipientsList.innerHTML = '';
        if (!messagesState.conversations || messagesState.conversations.length === 0) {
            recipientsList.innerHTML = '<div class="p-3 text-muted text-center extra-small font-monospace">لا يوجد مستخدمين مسجلين</div>';
        } else {
            messagesState.conversations.forEach(c => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'list-group-item p-3 d-flex align-items-center justify-content-between bg-white border-bottom';
                itemDiv.innerHTML = `
                    <div class="d-flex align-items-center gap-3">
                        <input type="checkbox" class="form-check-input bulk-user-checkbox rounded-2" value="${c.user_id}">
                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(c.name)}&background=2563eb&color=fff" class="rounded-circle" style="width: 36px; height: 36px;">
                        <div>
                            <strong class="d-block text-dark font-monospace extra-small">${escapeHtml(c.name)}</strong>
                            <small class="text-muted extra-small">${escapeHtml(c.role)}</small>
                        </div>
                    </div>
                    <span class="badge ${c.role === 'مدير النظام' ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-info-subtle text-info border border-info-subtle'} rounded-pill extra-small px-3 py-1 font-monospace">
                        ${escapeHtml(c.role)}
                    </span>
                `;
                recipientsList.appendChild(itemDiv);
            });
        }
    }

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

function toggleBulkRecipientAll(checked) {
    const checkboxes = document.querySelectorAll('.bulk-user-checkbox');
    checkboxes.forEach(cb => cb.checked = checked);
}

function sendBulkMessages() {
    const contentInput = document.getElementById('bulkComposerContentInput');
    const sendBtn = document.getElementById('bulkSendSubmitBtn');
    const progressContainer = document.getElementById('bulkProgressContainer');
    const progressBar = document.getElementById('bulkSendProgressBar');
    const successCountEl = document.getElementById('bulkSendSuccessCount');
    const failCountEl = document.getElementById('bulkSendFailCount');

    const checkboxes = document.querySelectorAll('.bulk-user-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));

    const content = contentInput?.value.trim();

    let isValid = true;

    if (selectedIds.length === 0) {
        showToast('يرجى اختيار مستلم واحد على الأقل من القائمة الإرسال الجماعي', 'warning');
        isValid = false;
    }

    if (!content) {
        if (contentInput) contentInput.classList.add('is-invalid');
        showToast('يرجى كتابة نص الرسالة الجماعية قبل الإرسال', 'warning');
        isValid = false;
    } else {
        if (contentInput) contentInput.classList.remove('is-invalid');
    }

    if (!isValid) return;

    if (sendBtn) sendBtn.disabled = true;
    if (progressContainer) progressContainer.classList.remove('d-none');
    if (progressBar) progressBar.style.width = '0%';
    if (successCountEl) successCountEl.textContent = '0';
    if (failCountEl) failCountEl.textContent = '0';

    let total = selectedIds.length;
    let successCount = 0;
    let failCount = 0;
    let completed = 0;

    const promises = selectedIds.map(rid => {
        return fetch('/messages/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipient_id: rid, content: content })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                successCount++;
            } else {
                failCount++;
            }
        })
        .catch(() => {
            failCount++;
        })
        .finally(() => {
            completed++;
            let pct = Math.round((completed / total) * 100);
            if (progressBar) progressBar.style.width = pct + '%';
            if (successCountEl) successCountEl.textContent = successCount;
            if (failCountEl) failCountEl.textContent = failCount;
        });
    });

    Promise.all(promises).then(() => {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'إرسال جماعي مكتمل',
                html: `تم إرسال الرسالة الجماعية بنجاح إلى <b>${successCount}</b> مستخدم.<br>عدد الرسائل غير المسلمة: <b>${failCount}</b>`,
                icon: successCount > 0 ? 'success' : 'error',
                confirmButtonText: 'حسناً'
            });
        } else {
            showToast(`تم إرسال الرسائل الجماعية: ${successCount} نجاح، ${failCount} فشل`, 'success');
        }

        loadConversations();

        setTimeout(() => {
            const modalEl = document.getElementById('bulkMessageComposerModal');
            const bsModal = bootstrap.Modal.getInstance(modalEl);
            if (bsModal) bsModal.hide();
            if (sendBtn) sendBtn.disabled = false;
        }, 1200);
    });
}

function openTemplatesModal() {
    const modalEl = document.getElementById('messageTemplatesModal');
    if (!modalEl) return;
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

/* ==========================================================================
   PHASE 4: MESSAGES ANALYTICS & SMART REPORTS CONTROLLER (Chart.js)
   ========================================================================== */

let msgAnalyticsCharts = {
    volume: null,
    role: null,
    readRate: null,
    notifications: null
};

function initMessagesAnalyticsCharts() {
    if (typeof Chart === 'undefined') return;

    const convs = messagesState.conversations || [];
    updateMessagesAnalyticsUI(convs);
}

function updateMessagesAnalyticsUI(convs) {
    if (!convs) return;

    let total = convs.length;
    let unreadTotal = 0;
    let adminUsers = 0;
    let teacherUsers = 0;

    convs.forEach(c => {
        if (c.unread_count > 0) unreadTotal += c.unread_count;
        if (c.role === 'مدير النظام') adminUsers++;
        else teacherUsers++;
    });

    let readTotal = Math.max(0, total - unreadTotal);
    let readRatePct = total > 0 ? Math.round((readTotal / total) * 100) : 100;

    // Render Top Activity Rankings Table
    const topTbody = document.getElementById('msgTopActivityTableBody');
    if (topTbody) {
        topTbody.innerHTML = '';
        if (convs.length === 0) {
            topTbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted font-monospace">لا توجد بيانات محادثات سابقة لحساب الترتيب الإحصائي</td></tr>';
        } else {
            let sortedConvs = [...convs].sort((a, b) => b.unread_count - a.unread_count);
            sortedConvs.forEach((item, idx) => {
                const tr = document.createElement('tr');
                tr.className = 'align-middle';
                tr.innerHTML = `
                    <td class="font-monospace fw-bold text-primary">${idx + 1}</td>
                    <td class="text-start">
                        <div class="d-flex align-items-center gap-2">
                            <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(item.name)}&background=2563eb&color=fff" class="rounded-circle" style="width: 34px; height: 34px;">
                            <div>
                                <strong class="d-block text-dark font-monospace extra-small">${escapeHtml(item.name)}</strong>
                                <small class="text-muted extra-small font-monospace">${item.last_message ? escapeHtml(item.last_message.substring(0, 30)) + '...' : ''}</small>
                            </div>
                        </div>
                    </td>
                    <td><span class="badge ${item.role === 'مدير النظام' ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-info-subtle text-info border border-info-subtle'} rounded-pill extra-small px-3 py-1 font-monospace">${escapeHtml(item.role)}</span></td>
                    <td class="font-monospace fw-bold text-dark">${item.unread_count > 0 ? `<span class="badge bg-warning text-dark font-monospace">${item.unread_count} غير مقروءة</span>` : '<span class="badge bg-success-subtle text-success font-monospace">مطلّع عليها</span>'}</td>
                    <td class="font-monospace text-muted extra-small">${item.last_time || '—'}</td>
                    <td class="font-monospace fw-bold text-success">${item.unread_count === 0 ? '100%' : '50%'}</td>
                    <td>
                        <div class="d-flex justify-content-center gap-1">
                            <button type="button" class="btn btn-sm btn-light border rounded-pill px-2 extra-small font-monospace fw-bold" onclick="viewMessageProfile(${item.user_id}, '${escapeJsString(item.name)}', '${escapeJsString(item.role)}')">
                                <i class="fa-solid fa-eye text-primary me-1"></i> عرض
                            </button>
                            <button type="button" class="btn btn-sm btn-light border rounded-pill px-2 extra-small font-monospace text-primary fw-bold" onclick="selectConversation(${item.user_id}, '${escapeJsString(item.name)}', '${escapeJsString(item.role)}')">
                                <i class="fa-solid fa-comments me-1"></i> محادثة
                            </button>
                        </div>
                    </td>
                `;
                topTbody.appendChild(tr);
            });
        }
    }

    if (typeof Chart === 'undefined') return;

    // Chart 1: Volume Doughnut
    const canvasVol = document.getElementById('msgChartVolume');
    if (canvasVol) {
        if (msgAnalyticsCharts.volume) msgAnalyticsCharts.volume.destroy();
        msgAnalyticsCharts.volume = new Chart(canvasVol.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['المقروءة بالكامل', 'غير المقروءة / تتطلب المتابعة'],
                datasets: [{
                    data: [readTotal, unreadTotal],
                    backgroundColor: ['#10b981', '#f59e0b'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { family: 'Cairo' } } } }
            }
        });
    }

    // Chart 2: Role Bar
    const canvasRole = document.getElementById('msgChartRole');
    if (canvasRole) {
        if (msgAnalyticsCharts.role) msgAnalyticsCharts.role.destroy();
        msgAnalyticsCharts.role = new Chart(canvasRole.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['مدراء النظام', 'المعلمون والكادر الأكاديمي'],
                datasets: [{
                    label: 'عدد المحادثات المسجلة',
                    data: [adminUsers, teacherUsers],
                    backgroundColor: ['#2563eb', '#06b6d4'],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    // Chart 3: Read Rate Gauge
    const canvasRate = document.getElementById('msgChartReadRate');
    if (canvasRate) {
        if (msgAnalyticsCharts.readRate) msgAnalyticsCharts.readRate.destroy();
        msgAnalyticsCharts.readRate = new Chart(canvasRate.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['معدل القراءة %', 'المتبقي %'],
                datasets: [{
                    data: [readRatePct, Math.max(0, 100 - readRatePct)],
                    backgroundColor: ['#2563eb', '#e2e8f0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: { legend: { position: 'bottom', labels: { font: { family: 'Cairo' } } } }
            }
        });
    }

    // Chart 4: Notifications Category Breakdown
    const canvasNotif = document.getElementById('msgChartNotifications');
    if (canvasNotif) {
        if (msgAnalyticsCharts.notifications) msgAnalyticsCharts.notifications.destroy();
        msgAnalyticsCharts.notifications = new Chart(canvasNotif.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['واجبات دراسية', 'اختبارات ودرجات', 'حضور وغياب', 'إدارية عامة'],
                datasets: [{
                    data: [2, 1, 1, 1],
                    backgroundColor: ['#2563eb', '#f59e0b', '#10b981', '#64748b'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { family: 'Cairo' } } } }
            }
        });
    }
}

function exportMessagesAnalyticsExcel() {
    const convs = messagesState.conversations || [];
    if (convs.length === 0) {
        showToast('لا توجد بيانات تحليلات لتصديرها', 'warning');
        return;
    }

    let total = convs.length;
    let unreadTotal = 0;
    let adminUsers = 0;
    let teacherUsers = 0;

    convs.forEach(c => {
        if (c.unread_count > 0) unreadTotal += c.unread_count;
        if (c.role === 'مدير النظام') adminUsers++;
        else teacherUsers++;
    });

    let readTotal = Math.max(0, total - unreadTotal);
    let readRatePct = total > 0 ? Math.round((readTotal / total) * 100) : 100;

    let excelHTML = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="content-type" content="text/plain; charset=UTF-8"/>
        <style>
            table { border-collapse: collapse; width: 100%; direction: rtl; margin-bottom: 20px; }
            th { background-color: #1e40af; color: #ffffff; font-weight: bold; text-align: center; padding: 10px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; }
            td { text-align: center; padding: 8px; border: 1px solid #cbd5e1; font-family: Cairo, Arial; font-size: 13px; }
            .kpi-title { font-weight: bold; background-color: #f1f5f9; text-align: right; }
            tr:nth-child(even) { background-color: #f8fafc; }
        </style>
    </head>
    <body dir="rtl">
        <h2 style="text-align: center; font-family: Cairo, Arial; color: #1e40af;">تقرير التحليلات والإحصائيات الشامل لمركز الرسائل والمحادثات</h2>
        <p style="text-align: center; font-family: Cairo, Arial; color: #64748b;">تاريخ التتقرير: ${new Date().toLocaleDateString('ar-EG')}</p>

        <!-- KPI SUMMARY TABLE -->
        <table>
            <thead>
                <tr>
                    <th colspan="2">الملخص التنفيذي ومؤشرات الأداء الرئيسية (KPIs)</th>
                </tr>
            </thead>
            <tbody>
                <tr><td class="kpi-title">إجمالي المحادثات المسجلة</td><td>${total}</td></tr>
                <tr><td class="kpi-title">الرسائل والمحادثات المقروءة</td><td>${readTotal}</td></tr>
                <tr><td class="kpi-title">الرسائل غير المقروءة</td><td>${unreadTotal}</td></tr>
                <tr><td class="kpi-title">معدل الاطلاع والقراءة الشامل %</td><td>${readRatePct}%</td></tr>
                <tr><td class="kpi-title">محادثات مدراء النظام</td><td>${adminUsers}</td></tr>
                <tr><td class="kpi-title">محادثات المعلمين والكادر الأكاديمي</td><td>${teacherUsers}</td></tr>
            </tbody>
        </table>

        <!-- USER ACTIVITY RANKINGS TABLE -->
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>اسم المستخدم والطرف المخاطب</th>
                    <th>الدور الوظيفي</th>
                    <th>حالة الاطلاع</th>
                    <th>تاريخ/وقت آخر نشاط</th>
                    <th>معدل القراءة المقدر %</th>
                </tr>
            </thead>
            <tbody>`;

    convs.forEach((item, idx) => {
        excelHTML += `
            <tr>
                <td>${idx + 1}</td>
                <td style="text-align: right;">${escapeHtml(item.name)}</td>
                <td>${escapeHtml(item.role)}</td>
                <td>${item.unread_count > 0 ? `غير مقروءة (${item.unread_count})` : 'مقروءة بالكامل'}</td>
                <td>${item.last_time || '—'}</td>
                <td>${item.unread_count === 0 ? '100%' : '50%'}</td>
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
    a.download = `تقرير_تحليلات_الرسائل_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('تم تصدير تقرير تحليلات الرسائل إلى Excel بنجاح', 'success');
}
