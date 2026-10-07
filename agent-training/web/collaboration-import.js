/* Local interactions for the migrated document; no source-page globals. */
(() => {
  const triggers = document.querySelectorAll('[data-import-accordion], [data-import-faq]');
  triggers.forEach((trigger, index) => {
    const item = trigger.parentElement;
    const panel = item.querySelector('.accordion-body, .faq-a');
    panel.id = `import-answer-${index}`;
    trigger.setAttribute('role', 'button');
    trigger.tabIndex = 0;
    trigger.setAttribute('aria-controls', panel.id);
    trigger.setAttribute('aria-expanded', 'false');
    trigger.onclick = () => {
      const opening = !item.classList.contains('open');
      // Show one answer at a time so expanded content fits the fixed stage.
      const scope = trigger.closest('.import-body');
      scope.querySelectorAll('.accordion-item.open, .faq-item.open').forEach(sibling => {
        sibling.classList.remove('open');
        sibling.querySelector('[role="button"]').setAttribute('aria-expanded', 'false');
      });
      item.classList.toggle('open', opening);
      trigger.setAttribute('aria-expanded', String(opening));
    };
    trigger.onkeydown = event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        event.stopPropagation();
        trigger.click();
      }
    };
  });

  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch { /* Local files and denied clipboard permissions use the fallback. */ }
    const field = document.createElement('textarea');
    field.value = text;
    field.style.cssText = 'position:fixed;opacity:0';
    document.body.append(field);
    field.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch { /* Report below. */ }
    field.remove();
    return copied;
  }

  document.querySelectorAll('[data-import-copy]').forEach(button => {
    const blockId = button.closest('[data-import-block]').dataset.importBlock;
    const fragments = document.querySelectorAll(`[data-import-block="${blockId}"] .code-block code`);
    const label = fragments.length > 1 ? '复制整段' : '复制';
    button.textContent = label;
    button.onclick = async () => {
      const text = Array.from(fragments, fragment => fragment.textContent).join('\n');
      button.textContent = await copyText(text) ? '已复制' : '复制失败';
      setTimeout(() => { button.textContent = label; }, 1500);
    };
  });
})();
