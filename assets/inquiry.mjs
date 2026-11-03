export const INQUIRY_ENDPOINT = 'https://www.octerv.com/api/app-feedback/a63629e1-f92b-431e-8d39-a110187a3ad6';
const receipt = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const words = {
  en: {empty:'Enter a message containing more than spaces.', invalid:'Please check the app, email address and message length. Delivery was not confirmed; your input remains here.', sending:'Sending…', sent:'Delivery confirmed. Save this reference for an inquiry about this submission: ', failed:'Delivery could not be confirmed. Your message may already have arrived. Your input remains here; please avoid repeated submissions.', limited:'Too many attempts. Wait at least one minute before trying again. Your input remains here.'},
  ja: {empty:'空白以外のお問い合わせ内容を入力してください。', invalid:'対象アプリ、メールアドレスの形式、本文の長さをご確認ください。受付は確認されておらず、入力内容は残しています。', sending:'送信中です…', sent:'受付を確認しました。この送信について問い合わせる際は、次の受付番号をお控えください：', failed:'受付を確認できませんでした。すでに届いている可能性があります。入力内容は残していますので、繰り返し送信しないでください。', limited:'送信回数の上限に達しました。少なくとも1分待ってからお試しください。入力内容は残しています。'},
};
export function mountInquiry(doc, send = globalThis.fetch.bind(globalThis)) {
  const form = doc.getElementById('inquiry-form');
  if (!form || form.action !== INQUIRY_ENDPOINT) return;
  const t = words[doc.documentElement.lang === 'ja' ? 'ja' : 'en'];
  const fieldset = doc.getElementById('inquiry-fields');
  const status = doc.getElementById('inquiry-status');
  const error = doc.getElementById('inquiry-error');
  const count = doc.getElementById('message-count');
  const field = name => form.elements.namedItem(name);
  const updateCount = () => {count.textContent = `${field('message').value.length} / 2000`;};
  field('message').addEventListener('input', updateCount);
  let pending = false;
  fieldset.disabled = false;
  updateCount();
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (pending || !form.reportValidity()) return;
    const payload = {app: field('app').value, message: field('message').value.trim(), reply_email: field('reply_email').value.trim(), website: field('website').value};
    if (!payload.message) {error.textContent = t.empty; field('message').focus(); return;}
    pending = true; fieldset.disabled = true; error.textContent = ''; status.textContent = t.sending;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await send(INQUIRY_ENDPOINT, {
        method:'POST', mode:'cors', credentials:'omit', redirect:'error', referrerPolicy:'no-referrer',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload), signal:controller.signal,
      });
      if (response.status === 429) {error.textContent = t.limited; status.textContent = ''; error.focus(); return;}
      if ([400, 413, 415].includes(response.status)) {error.textContent = t.invalid; status.textContent = ''; error.focus(); return;}
      if (response.status !== 200) throw new Error('unconfirmed');
      const result = await response.json();
      if (!result || result.ok !== true || typeof result.reference !== 'string' || !receipt.test(result.reference)) throw new Error('unconfirmed');
      form.reset(); updateCount(); status.textContent = t.sent + result.reference; status.focus();
    } catch {
      status.textContent = ''; error.textContent = t.failed; error.focus();
    } finally {
      clearTimeout(timer); pending = false; fieldset.disabled = false;
    }
  });
}
if (typeof document !== 'undefined') mountInquiry(document);
