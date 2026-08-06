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

// Toast notification helper
function showTeacherToast(message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    const toastMsg = document.getElementById('toastMessage');
    if (toastEl && toastMsg) {
        toastMsg.textContent = message;
        toastEl.className = `toast align-items-center text-white border-0 shadow-lg bg-${type}`;
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }
}
