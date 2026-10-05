const ENDPOINT = 'http://127.0.0.1:8765/v1/linkedin/captures';

chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (message?.type !== 'workhunter:capture' ||
      !sender.url?.startsWith('https://www.linkedin.com/')) return;
  const {url, text, author, source_type} = message.payload || {};
  if (typeof text !== 'string' || text.length > 100000 ||
      typeof url !== 'string' || !url.startsWith('https://www.linkedin.com/')) {
    reply({accepted: false, error: 'invalid_capture'});
    return;
  }
  fetch(ENDPOINT, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url, text, author, source_type})
  }).then(async response => {
    const data = await response.json();
    reply({http_status: response.status, ...data});
  }).catch(error => reply({accepted: false, error: String(error)}));
  return true;
});
