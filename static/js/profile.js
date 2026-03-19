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

    const cover = document.querySelector('.profile-cover');
    const tabsRoot = document.getElementById('profileTabs');

    // Toast helpers
    const toastEl = document.getElementById('profileToast');
    const toastBody = document.getElementById('profileToastBody');
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
      return tabsRoot.querySelector('button[data-profile-tab="' + tabName + '"]');
    }

    function showTab(tabName, scrollIntoView) {
      const tabBtn = getTabButton(tabName);
      if (!tabBtn) return;
      bootstrap.Tab.getOrCreateInstance(tabBtn).show();

      if (scrollIntoView && tabsRoot) {
        tabsRoot.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    // Keep URL in sync with active tab (nice for refresh/share)
    if (tabsRoot) {
      tabsRoot
        .querySelectorAll('button[data-bs-toggle="tab"]')
        .forEach(function (btn) {
          btn.addEventListener('shown.bs.tab', function () {
            const tabName = btn.getAttribute('data-profile-tab') || '';
            try {
              const url = new URL(window.location.href);
              if (tabName && tabName !== 'overview') {
                url.searchParams.set('tab', tabName);
              } else {
                url.searchParams.delete('tab');
              }
              window.history.replaceState({}, '', url.toString());
            } catch (e) {
              // ignore (older browsers)
            }
          });
        });
    }

    // Header action buttons
    const openSettingsBtn = document.querySelector(
      '[data-profile-action="open-settings"]'
    );
    if (openSettingsBtn) {
      openSettingsBtn.addEventListener('click', function () {
        showTab('settings', true);
      });
    }

    // Stat cards open tabs (click + keyboard)
    document.querySelectorAll('[data-profile-open-tab]').forEach(function (el) {
      const tabName = el.getAttribute('data-profile-open-tab');
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

    // Image preview (header avatar + settings preview + cover background)
    const fileInput = document.querySelector('input[name="image"]');
    const avatarImg = document.getElementById('profileAvatarImg');
    const avatarPlaceholder = document.getElementById('profileAvatarPlaceholder');
    const settingsPreview = document.getElementById('settingsAvatarPreview');

    const coverGradient =
      'linear-gradient(115deg, rgba(13,110,253,0.86) 0%, rgba(102,16,242,0.78) 45%, rgba(32,201,151,0.78) 100%)';

    let lastObjectUrl = null;

    function setPreview(url) {
      if (avatarImg) {
        avatarImg.src = url;
        avatarImg.classList.remove('d-none');
      }
      if (avatarPlaceholder) {
        avatarPlaceholder.classList.add('d-none');
        avatarPlaceholder.setAttribute('aria-hidden', 'true');
      }
      if (settingsPreview) {
        settingsPreview.src = url;
      }
      if (cover) {
        cover.style.backgroundImage = coverGradient + ', url(\"' + url + '\")';
      }
    }

    if (fileInput) {
      fileInput.addEventListener('change', function () {
        const file = fileInput.files && fileInput.files[0];
        if (!file) return;

        if (lastObjectUrl) {
          URL.revokeObjectURL(lastObjectUrl);
        }
        lastObjectUrl = URL.createObjectURL(file);
        setPreview(lastObjectUrl);
        showToast('Photo selected (save to apply)');
      });
    }

    const changePhotoBtn = document.querySelector(
      '[data-profile-action="change-photo"]'
    );
    if (changePhotoBtn) {
      changePhotoBtn.addEventListener('click', function () {
        showTab('settings', true);
        window.setTimeout(function () {
          if (fileInput) fileInput.click();
        }, 150);
      });
    }
  });
})();

