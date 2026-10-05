document.addEventListener('DOMContentLoaded', () => {
  const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
  deleteButtons.forEach((button) => {
    button.addEventListener('click', (event) => {
      const confirmed = window.confirm('Are you sure you want to delete this item?');
      if (!confirmed) {
        event.preventDefault();
      }
    });

    const galleryMain = document.querySelector('[data-gallery-main]');
    const galleryButtons = document.querySelectorAll('[data-gallery-src]');
    galleryButtons.forEach((button) => {
      button.addEventListener('click', () => {
        if (!galleryMain) return;
        galleryMain.src = button.dataset.gallerySrc;
        galleryButtons.forEach((item) => item.classList.toggle('is-active', item === button));
      });
    });
  });
});
