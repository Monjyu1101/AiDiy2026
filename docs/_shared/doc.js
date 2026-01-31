document.addEventListener('DOMContentLoaded', () => {
  const blocks = document.querySelectorAll('pre[data-src]');
  blocks.forEach(async (block) => {
    const src = block.getAttribute('data-src');
    const code = block.querySelector('code');
    if (!src || !code) return;

    try {
      const response = await fetch(src, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const text = await response.text();
      code.textContent = text.replace(/\s+$/u, '');
      block.classList.add('loaded');
    } catch (error) {
      code.textContent = `読み込みに失敗しました: ${src}`;
      block.classList.add('error');
    }
  });
});

