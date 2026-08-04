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
                    <button type="button" class="btn btn-sm btn-light border rounded-pill px-3 fw-bold font-monospace extra-small text-primary" onclick="selectConversation(${item.user_id}, '${escapeJsString(item.name)}', '${escapeJsString(item.role)}')">
                        <i class="fa-solid fa-comments me-1"></i> فتح المحادثة
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
    const tabGrid  = document.getElementById('msgTabGridBtn');
    const tabChat  = document.getElementById('msgTabChatBtn');

    if (tabName === 'grid') {
        if (gridPane) gridPane.classList.remove('d-none');
        if (chatPane) chatPane.classList.add('d-none');
        if (tabGrid)  { tabGrid.classList.add('active', 'btn-primary'); tabGrid.classList.remove('btn-light'); }
        if (tabChat)  { tabChat.classList.remove('active', 'btn-primary'); tabChat.classList.add('btn-light'); }
    } else {
        if (gridPane) gridPane.classList.add('d-none');
        if (chatPane) chatPane.classList.remove('d-none');
        if (tabChat)  { tabChat.classList.add('active', 'btn-primary'); tabChat.classList.remove('btn-light'); }
        if (tabGrid)  { tabGrid.classList.remove('active', 'btn-primary'); tabGrid.classList.add('btn-light'); }
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
