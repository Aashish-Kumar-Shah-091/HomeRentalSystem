(function () {
  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    if (!window.bootstrap) return;

    const tabsRoot = document.getElementById('tenantProfileTabs');

    // Toast
    const toastEl = document.getElementById('tenantToast');
    const toastBody = document.getElementById('tenantToastBody');
    const toast = toastEl
      ? bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 1600 })
      : null;

    function showToast(message) {
      if (!toast || !toastBody) return;
      toastBody.textContent = message;
      toast.show();
    }

    function getTabButton(tabName) {
      if (!tabsRoot) return null;
      return tabsRoot.querySelector('button[data-tenant-tab="' + tabName + '"]');
    }

    function showTab(tabName, scrollIntoView) {
      const tabBtn = getTabButton(tabName);
      if (!tabBtn) return;
      bootstrap.Tab.getOrCreateInstance(tabBtn).show();
      if (scrollIntoView && tabsRoot) {
        tabsRoot.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    // Keep URL in sync with active tab
    if (tabsRoot) {
      tabsRoot
        .querySelectorAll('button[data-bs-toggle="tab"]')
        .forEach(function (btn) {
          btn.addEventListener('shown.bs.tab', function () {
            const tabName = btn.getAttribute('data-tenant-tab') || '';
            try {
              const url = new URL(window.location.href);
              if (tabName && tabName !== 'overview') {
                url.searchParams.set('tab', tabName);
              } else {
                url.searchParams.delete('tab');
              }
              window.history.replaceState({}, '', url.toString());
            } catch (e) {}
          });
        });
    }

    // Open bookings button
    document
      .querySelector('[data-tenant-action="open-bookings"]')
      ?.addEventListener('click', function () {
        showTab('bookings', true);
      });

    // Stat cards open tabs
    document.querySelectorAll('[data-tenant-open-tab]').forEach(function (el) {
      const tabName = el.getAttribute('data-tenant-open-tab');
      if (!tabName) return;

      const open = function () {
        showTab(tabName, true);
      };

      el.addEventListener('click', open);
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          open();
        }
      });
    });

    // Copy to clipboard
    async function copyText(text) {
      if (!text) return;
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          const temp = document.createElement('textarea');
          temp.value = text;
          temp.setAttribute('readonly', '');
          temp.style.position = 'absolute';
          temp.style.left = '-9999px';
          document.body.appendChild(temp);
          temp.select();
          document.execCommand('copy');
          document.body.removeChild(temp);
        }
        showToast('Copied to clipboard');
      } catch (e) {
        showToast('Copy failed');
      }
    }

    document.querySelectorAll('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        copyText(btn.getAttribute('data-copy'));
      });
    });

    // Respect ?tab=bookings on load
    try {
      const url = new URL(window.location.href);
      const tab = url.searchParams.get('tab');
      if (tab) showTab(tab, false);
    } catch (e) {}
  });
})();

