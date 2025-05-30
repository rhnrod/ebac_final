document.addEventListener('DOMContentLoaded', function () {
  const middleColumn = document.getElementById('scroll-mid');

  if (middleColumn) {
    ['esquerda', 'direita'].forEach(classe => {
      const coluna = document.querySelector(`.${classe}`);
      if (!coluna) return;

      coluna.addEventListener('wheel', function (e) {
        e.preventDefault();
        middleColumn.scrollBy({
          top: e.deltaY,
          behavior: 'smooth'
        });
      }, { passive: false });
    });
  }
});