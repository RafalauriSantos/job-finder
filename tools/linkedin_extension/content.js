(() => {
  if (!document.getElementById('workhunter-extension-status')) {
    const badge = document.createElement('div');
    badge.id = 'workhunter-extension-status';
    badge.textContent = 'WorkHunter ativo';
    Object.assign(badge.style, {position:'fixed', bottom:'16px', right:'16px', zIndex:'2147483647', background:'#0a66c2', color:'#fff', padding:'6px 10px', borderRadius:'14px', font:'12px sans-serif', boxShadow:'0 2px 8px #0004'});
    document.documentElement.appendChild(badge);
  }
  const sent = new Set();
  const badge = document.getElementById('workhunter-extension-status');
  // LinkedIn periodically changes CSS classes and no longer exposes data-urn
  // on every feed card. Keep the semantic label as the stable anchor and pick
  // the deepest card container to avoid scanning the whole feed repeatedly.
  const postSelector = 'main div, [role="main"] div';
  const signals = /\b(vaga|contratando|oportunidade|hiring|recrut)\b/i;
  const tech = /\b(desenvolvedor|developer|dev|api|javascript|python|java|frontend|backend|full.?stack|integra)/i;

  function postBody(card) {
    const lines = (card.innerText || '').split('\n').map(line => line.trim()).filter(Boolean);
    const time = lines.findIndex(line => /^\d+\s*(?:min|h|d|sem|mês|mes|ano)\b/i.test(line));
    if (time < 0) return '';
    let start = time + 1;
    if (lines[start] === 'Seguir') start += 1;
    return lines.slice(start).join('\n').trim();
  }

  function capture(card) {
    const text = postBody(card);
    if (!text || !signals.test(text) || !tech.test(text)) return;
    const link = [...card.querySelectorAll('a[href]')].find(a => /linkedin\.com\/(?:feed\/update\/|posts\/|jobs\/view\/)/i.test(a.href));
    const url = link ? link.href : location.href;
    const key = `${url}|${text.slice(0, 300)}`;
    if (sent.has(key)) return;
    sent.add(key);
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
    const byline = lines[1] || '';
    const author = lines[0] === 'Publicação no feed'
      ? (/\b(gostou|comentou|seguiu|Seguido por)\b/i.test(byline) ? (lines[2] || '') : byline)
      : '';
    chrome.runtime.sendMessage({type: 'workhunter:capture', payload: {
      url, text, author, source_type: 'post'
    }}, response => {
      if (chrome.runtime.lastError || !response?.accepted) {
        sent.delete(key);
        if (badge) badge.textContent = 'WorkHunter: erro no envio';
        console.warn('WorkHunter capture failed', chrome.runtime.lastError?.message || response?.error || response?.reason);
      } else if (badge) {
        badge.textContent = 'WorkHunter: vaga capturada';
      }
    });
  }

  const scan = () => document.querySelectorAll(postSelector).forEach(card => {
    const text = (card.innerText || '').trim();
    if (!text.startsWith('Publicação no feed')) return;
    // Keep the outermost feed card. LinkedIn nests several wrappers that all
    // repeat the accessibility heading.
    if (card.parentElement && (card.parentElement.innerText || '').trim().startsWith('Publicação no feed')) return;
    capture(card);
  });
  let scheduled = false;
  new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    setTimeout(() => { scheduled = false; scan(); }, 1000);
  }).observe(document.body, {childList: true, subtree: true});
  scan();
  setInterval(scan, 5000);
})();
