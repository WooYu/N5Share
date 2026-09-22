/* Shared authoring helpers. This course is standalone and uses no external assets. */
(function () {
  'use strict';
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const cards = (items, columns = items.length) => '<div class="grid cols-' + Math.min(columns, 3) + '">' + items.map(([title, body]) => '<article class="card"><h3>' + title + '</h3><p>' + body + '</p></article>').join('') + '</div>';
  const callout = text => '<div class="callout">' + text + '</div>';
  const table = (heads, rows) => '<table class="table"><thead><tr>' + heads.map(x => '<th scope="col">' + x + '</th>').join('') + '</tr></thead><tbody>' + rows.map(row => '<tr>' + row.map(x => '<td>' + x + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
  const code = value => '<pre class="code"><code>' + esc(value) + '</code></pre>';
  let serial = 0;
  const flow = (labels, title, desc, loop = false) => {
    const uid = 'n5-flow-' + (++serial), n = labels.length, gap = 32, width = (1160 - gap * (n - 1)) / n;
    const nodes = labels.map(([label, sub], i) => {
      const x = 20 + i * (width + gap), cx = x + width / 2;
      return '<rect x="' + x + '" y="48" width="' + width + '" height="116" rx="18" fill="' + (i % 2 ? '#e9f5f3' : '#edf2ff') + '" stroke="' + (i % 2 ? '#087f79' : '#215bea') + '" stroke-width="2"/><text x="' + cx + '" y="96" text-anchor="middle" fill="#172c42" font-size="25" font-weight="700">' + esc(label) + '</text><text x="' + cx + '" y="134" text-anchor="middle" fill="#627286" font-size="19">' + esc(sub || '') + '</text>' + (i < n - 1 ? '<path d="M ' + (x + width + 3) + ' 106 H ' + (x + width + gap - 6) + '" stroke="#215bea" stroke-width="3" marker-end="url(#' + uid + '-arrow)"/>' : '');
    }).join('');
    const loopTarget = loop && typeof loop === 'object' ? loop.target : 0;
    const loopLabel = loop && typeof loop === 'object' ? loop.label : '观察或失败触发下一轮；满足退出条件即结束';
    const targetX = 20 + loopTarget * (width + gap) + width / 2;
    const back = loop ? '<path d="M ' + (1180 - width / 2) + ' 165 V 211 H ' + targetX + ' V 169" fill="none" stroke="#087f79" stroke-width="3" marker-end="url(#' + uid + '-arrow)"/><text x="600" y="237" text-anchor="middle" fill="#087f79" font-size="20">' + esc(loopLabel) + '</text>' : '';
    return '<svg class="diagram" viewBox="0 0 1200 ' + (loop ? 255 : 205) + '" role="img" aria-labelledby="' + uid + '-title ' + uid + '-desc"><title id="' + uid + '-title">' + esc(title) + '</title><desc id="' + uid + '-desc">' + esc(desc) + '</desc><defs><marker id="' + uid + '-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#215bea"/></marker></defs>' + nodes + back + '</svg>';
  };
  const notes = (explain, question, operation, transition) => '讲解：' + explain + '\n\n提问：' + question + '\n\n演示操作：' + operation + '\n\n转场：' + transition;
  const slide = (id, title, seconds, html, noteText, extra = {}) => Object.assign({id, title, seconds, coreSeconds: seconds, html, notes: noteText, demo: null, quiz: null}, extra);
  window.N5.content = {esc, cards, callout, table, code, flow, notes, slide};
})();
