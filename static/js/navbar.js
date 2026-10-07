document.addEventListener('DOMContentLoaded', () => {
  const header = document.querySelector('.minimal-header');
  const toggle = document.querySelector('[data-navbar-toggle]');
  const menu = document.querySelector('[data-navbar-menu]');
  if (!header || !toggle || !menu) return;

  const mobileQuery = window.matchMedia('(max-width: 991.98px)');
  const aboutLink = menu.querySelector('[data-about-link]');
  const shopLink = menu.querySelector('[data-shop-link]');
  const quickAboutLink = document.querySelector('[data-quick-about-link]');
  const quickShopLink = document.querySelector('[data-quick-shop-link]');

  const updateAboutCurrentPage = () => {
    const isAboutSection = window.location.pathname === '/shop' && window.location.hash === '#shop-info';
    if (aboutLink && shopLink) {
      aboutLink.classList.toggle('is-active', isAboutSection);
      shopLink.classList.toggle('is-active', !isAboutSection && window.location.pathname === '/shop');
      if (isAboutSection) {
        aboutLink.setAttribute('aria-current', 'page');
        shopLink.removeAttribute('aria-current');
      } else {
        aboutLink.removeAttribute('aria-current');
        if (window.location.pathname === '/shop') shopLink.setAttribute('aria-current', 'page');
      }
    }

    quickAboutLink?.classList.toggle('active', isAboutSection);
    quickShopLink?.classList.toggle('active', !isAboutSection && window.location.pathname === '/shop');
  };

  const setMenuOpen = (isOpen) => {
    const shouldOpen = mobileQuery.matches && isOpen;
    header.classList.toggle('is-menu-open', shouldOpen);
    toggle.setAttribute('aria-expanded', String(shouldOpen));
    toggle.setAttribute('aria-label', shouldOpen ? 'Close menu' : 'Open menu');
  };

  toggle.addEventListener('click', () => {
    setMenuOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });

  document.addEventListener('click', (event) => {
    if (header.classList.contains('is-menu-open') && !header.contains(event.target)) {
      setMenuOpen(false);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && header.classList.contains('is-menu-open')) {
      setMenuOpen(false);
      toggle.focus();
    }
  });

  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) setMenuOpen(false);
  });

  updateAboutCurrentPage();
  window.addEventListener('hashchange', updateAboutCurrentPage);
  mobileQuery.addEventListener('change', () => setMenuOpen(false));
});
