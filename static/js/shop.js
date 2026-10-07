document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.shop-catalog-form');
  if (!form) return;

  const sidebar = document.querySelector('#shopFilters');
  const filterToggle = document.querySelector('[data-shop-filter-toggle]');
  const sortSelect = document.querySelector('[data-shop-sort]');
  const productGrid = document.querySelector('[data-shop-grid]');

  if (filterToggle && sidebar) {
    const closeFilters = () => {
      sidebar.classList.remove('is-open');
      filterToggle.setAttribute('aria-expanded', 'false');
    };

    filterToggle.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('is-open');
      filterToggle.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sidebar.classList.contains('is-open')) {
        closeFilters();
        filterToggle.focus();
      }
    });
  }

  sortSelect?.addEventListener('change', () => form.requestSubmit());

  const brandCheckboxes = form.querySelectorAll('input[name="brand"][type="checkbox"]');
  brandCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', () => {
      if (!checkbox.checked) return;
      brandCheckboxes.forEach((other) => {
        if (other !== checkbox) other.checked = false;
      });
    });
  });

  if (productGrid) {
    document.querySelectorAll('[data-shop-view]').forEach((button) => {
      button.addEventListener('click', () => {
        const listView = button.dataset.shopView === 'list';
        productGrid.classList.toggle('is-list', listView);
        document.querySelectorAll('[data-shop-view]').forEach((viewButton) => {
          const isActive = viewButton === button;
          viewButton.classList.toggle('is-active', isActive);
          viewButton.setAttribute('aria-pressed', String(isActive));
        });
      });
    });
  }

  const range = document.querySelector('.shop-dual-range');
  const minRange = document.querySelector('#shopMinPriceRange');
  const maxRange = document.querySelector('#shopMaxPriceRange');
  const minValue = document.querySelector('#shopMinPriceValue');
  const maxValue = document.querySelector('#shopMaxPriceValue');
  const minLabel = document.querySelector('#shopMinPriceLabel');
  const maxLabel = document.querySelector('#shopMaxPriceLabel');

  if (!range || !minRange || !maxRange || !minValue || !maxValue) return;

  const rangeMin = Number(range.dataset.rangeMin);
  const rangeMax = Number(range.dataset.rangeMax);
  const formatPrice = new Intl.NumberFormat('en-PK', { maximumFractionDigits: 0 });

  const updateRange = (changedInput) => {
    let low = Number(minRange.value);
    let high = Number(maxRange.value);

    if (low > high) {
      if (changedInput === minRange) high = low;
      else low = high;
    }

    minRange.value = String(low);
    maxRange.value = String(high);
    minValue.value = low > rangeMin ? String(low) : '';
    maxValue.value = high < rangeMax ? String(high) : '';

    if (minLabel) minLabel.textContent = `Rs. ${formatPrice.format(low)}`;
    if (maxLabel) maxLabel.textContent = `Rs. ${formatPrice.format(high)}`;

    const span = rangeMax - rangeMin;
    const start = span > 0 ? ((low - rangeMin) / span) * 100 : 0;
    const width = span > 0 ? ((high - low) / span) * 100 : 100;
    range.style.setProperty('--shop-range-start', `${start}%`);
    range.style.setProperty('--shop-range-width', `${width}%`);
  };

  [minRange, maxRange].forEach((input) => {
    input.addEventListener('input', () => updateRange(input));
    input.addEventListener('pointerdown', () => {
      minRange.classList.toggle('is-active', input === minRange);
      maxRange.classList.toggle('is-active', input === maxRange);
    });
    input.addEventListener('focus', () => {
      minRange.classList.toggle('is-active', input === minRange);
      maxRange.classList.toggle('is-active', input === maxRange);
    });
  });

  updateRange();
});
