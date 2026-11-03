#!/usr/bin/env python3
"""Render bilingual static privacy policies; --check verifies generated files and links."""
import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'policies.json').read_text())
CSS = '''body{font:17px/1.75 system-ui,sans-serif;color:#263238;background:#f6f8fa;margin:0}main{max-width:850px;margin:auto;padding:28px 22px 60px;background:#fff}h1{font-size:1.8rem;line-height:1.4}h2{font-size:1.25rem;margin-top:2em}a{color:#075a9c;overflow-wrap:anywhere}code{font-size:.9em;overflow-wrap:anywhere}label{display:block;font-weight:600;margin-top:18px}input,select,textarea,button{font:inherit;box-sizing:border-box;max-width:100%}input,select,textarea{width:100%;padding:9px;border:1px solid #8b989e;border-radius:4px}textarea{resize:vertical}fieldset{border:0;padding:0;margin:0}button{padding:10px 22px;margin-top:18px;background:#075a9c;color:white;border:0;border-radius:4px;cursor:pointer}:focus-visible{outline:3px solid #b56c00;outline-offset:3px}button:disabled{opacity:.6;cursor:wait}.help{font-size:.92rem;color:#49565c}.error{color:#a20f22}.meta,footer{font-size:.92rem;color:#49565c}nav ul{display:flex;gap:8px 24px;flex-wrap:wrap;padding-left:20px}.apps li{margin:14px 0}section{scroll-margin-top:16px}hr{border:0;border-top:1px solid #d4dce0;margin-top:28px}'''
TEXT = {'en': {'hub': 'Shared Privacy Policy',
        'privacy': 'Privacy Policy',
        'apps': 'App-specific pages',
        'common': 'Common provisions',
        'lang': '日本語',
        'back': 'Shared policy and all apps',
        'contact': 'Contact form',
        'date': 'Last updated',
        'links': 'Provider information',
        'other': 'Other app pages',
        'overview': 'PureA and Beat Weave overview',
        'overview_body': 'PureA stores tone preferences locally and generates audio without '
                         'microphone recording. Beat Weave records tap events and stores projects '
                         'and recovery copies locally. Their detailed pages explain storage and '
                         'deletion limits. Other apps can handle different data; use their '
                         'individual pages.'},
 'ja': {'hub': '共通プライバシーポリシー',
        'privacy': 'プライバシーポリシー',
        'apps': 'アプリ別ページ',
        'common': '共通事項',
        'lang': 'English',
        'back': '共通ポリシーと全アプリ',
        'contact': 'お問い合わせフォーム',
        'date': '最終更新日',
        'links': '外部サービスの情報',
        'other': 'その他のアプリ別ページ',
        'overview': 'PureA・Beat Weaveの概要',
        'overview_body': 'PureAは音の設定を端末内に保存し、マイク録音を使わずに音を生成します。Beat '
                         'Weaveはタップした演奏イベントを記録し、プロジェクトと復元用コピーを端末内に保存します。個別ページに保存と削除の範囲を記載しています。他アプリの取り扱いは異なるため、各アプリのページをご確認ください。'}}

def target(lang, app=None):
 return (('ja/' if lang=='ja' else '') + (f'apps/{app["slug"]}/' if app else '') + 'index.html')
def link(current, dest, label):
 return f'<a href="{escape(posixpath.relpath(dest, posixpath.dirname(current) or "."),quote=True)}">{escape(label)}</a>'
def external(url,label):
 return f'<a href="{escape(url,quote=True)}">{escape(label)}</a>'
def sections(rows, prefix):
 return '\n'.join(f'<section id="{prefix}-{i}"><h2>{escape(heading)}</h2><p>{escape(body)}</p></section>' for i,(heading,body) in enumerate(rows,1))
def providers(lang, app):
 rows=[('https://policies.google.com/privacy','Google '+('Privacy Policy' if lang=='en' else 'プライバシーポリシー')),('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement','GitHub '+('Privacy Statement' if lang=='en' else 'プライバシーに関する説明'))]
 if app and app['slug']=='voluclip':rows.append(('https://developers.google.com/ar/develop/privacy-requirements','ARCore '+('privacy information' if lang=='en' else 'プライバシー情報')))
 if app and app['slug']=='drumstick-id':rows.append(('https://developers.google.com/ml-kit/android-data-disclosure','ML Kit Android '+('data disclosure' if lang=='en' else 'データ開示情報')))
 if app and app['slug'] in ['octerv-setlist','repop-tracker','voluclip','drumstick-id']:
  rows.append(('https://www.apple.com/legal/privacy/','Apple '+('Privacy Policy' if lang=='en' else 'プライバシーポリシー')))
 return '<ul>'+''.join('<li>'+external(url,label)+'</li>' for url,label in rows)+'</ul>'
def render(lang,app=None):
 t=TEXT[lang];current=target(lang,app);other='ja' if lang=='en' else 'en'
 title=(app['name']+' — '+t['privacy']) if app else t['hub']
 parts=[f'<nav aria-label="{"Page navigation" if lang=="en" else "ページ案内"}"><ul><li>'+link(current,target(lang),t['back'])+'</li><li>'+link(current,target(other,app),t['lang'])+'</li></ul></nav>',f'<h1>{escape(title)} — lizefield</h1>',f'<p class="meta">{escape(t["date"])}: <time datetime="{DATA["updated_date"]}">{DATA["updated_date"]}</time></p>']
 if app:
  parts+=[f'<p><strong>{escape(app["name"])}</strong><br><span class="meta">{"Developer" if lang=="en" else "開発者"}: lizefield<br>Android: <code>{escape(app["package"])}</code></span></p>']
  if app.get('ios_bundle'):parts.append('<p class="meta">iOS: <code>'+escape(app['ios_bundle'])+'</code></p>')
  if app['alias'][lang]:parts.append('<p>'+escape(app['alias'][lang])+'</p>')
  parts.append(sections(app['sections'][lang],'app'))
 else:
  parts.append('<h2>'+escape(t['apps'])+'</h2><ul class="apps">'+''.join('<li>'+link(current,target(lang,a),a['name'])+'<br><code>'+escape(a['package'])+'</code>'+('<br>'+escape(a['alias'][lang]) if a['alias'][lang] else '')+'</li>' for a in DATA['apps'])+'</ul>')
  parts.append('<section id="existing-disclosures"><h2>'+escape(t['overview'])+'</h2><p>'+escape(t['overview_body'])+'</p></section>')
 parts.append('<hr><h2>'+escape(t['common'])+'</h2>')
 parts.append(sections(DATA['common'][lang],'common'))
 parts.append('<p>'+link(current,contact_target(lang),'PrivacyPolicy inquiry form' if lang=='en' else 'PrivacyPolicyお問い合わせフォーム')+'</p>')
 parts.append('<h2>'+escape(t['links'])+'</h2>'+providers(lang,app))
 parts.append('<footer><hr><h2>'+escape(t['other'])+'</h2><nav><ul>'+''.join('<li>'+link(current,target(lang,a),a['name'])+'</li>' for a in DATA['apps'] if not app or a['slug']!=app['slug'])+'</ul></nav></footer>')
 return f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{escape(title)} | lizefield</title>\n<style>{CSS}</style>\n</head>\n<body><main>\n'+ '\n'.join(parts)+'\n</main></body>\n</html>\n'


INQUIRY_ENDPOINT = 'https://www.octerv.com/api/app-feedback/a63629e1-f92b-431e-8d39-a110187a3ad6'
def contact_target(lang):
 return ('ja/' if lang=='ja' else '')+'contact/index.html'
def render_contact(lang):
 t=TEXT[lang]; current=contact_target(lang); other='ja' if lang=='en' else 'en'
 en=lang=='en'
 title='PrivacyPolicy inquiries' if en else 'PrivacyPolicyに関するお問い合わせ'
 text={
  'intro': 'Use this form for privacy questions, deletion inquiries or app feedback to lizefield. A reply email is optional; include it if you would like a reply. Sending does not itself delete any data.' if en else 'lizefieldへのプライバシーのご質問、削除に関するお問い合わせ、アプリへのご意見を受け付けます。返信を希望する場合は任意の返信先を入力してください。送信するだけでデータが削除されるわけではありません。',
  'disclosure': "Your message, selected app and optional reply email are sent through Octerv's HTTPS inquiry endpoint to external communications and message-storage providers used to receive and handle inquiries. A receipt reference and source-site information are added. Providers can store this information. Inquiry content is manually deleted around 90 days after receipt; if still being handled, deletion follows completion. Technical logs and independent provider records are separate. Do not include passwords, identity documents, payment details or unrelated sensitive information." if en else '本文、対象アプリ、任意の返信先を、OctervのHTTPS窓口から問い合わせの受付・対応に用いる外部の通信・メッセージ保存サービスへ送り、受付番号と送信元サイトの情報も付けます。提供者がこれらの情報を保存する場合があります。問い合わせ内容は受信から90日を目安に手動で削除し、対応中なら完了後に削除します。技術的なログや提供者が独立に管理する記録は別です。パスワード、本人確認書類、決済情報、無関係な機微情報は入力しないでください。',
 }
 options='<option value="general">'+('General / Another app' if en else '共通・その他のアプリ')+'</option>'+''.join('<option value="'+escape(a['slug'])+'">'+escape(a['name'])+'</option>' for a in DATA['apps'] if a.get('inquiry_category',a['slug'])!='general')
 script=posixpath.relpath('assets/inquiry.mjs',posixpath.dirname(current))
 csp="default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src https://www.octerv.com; form-action https://www.octerv.com; base-uri 'none'; object-src 'none'"
 parts=[
  '<nav><ul><li>'+link(current,target(lang),t['back'])+'</li><li>'+link(current,contact_target(other),t['lang'])+'</li></ul></nav>',
  '<h1>'+title+' — lizefield</h1>', '<p>'+text['intro']+'</p>',
  '<p id="inquiry-disclosure">'+text['disclosure']+'</p>',
  '<p>'+link(current,target(lang),'Privacy policy' if en else 'プライバシーポリシー')+'</p>',
  '<noscript><p>'+('JavaScript is required to send this inquiry. Enable JavaScript or use a browser that supports it.' if en else 'お問い合わせの送信にはJavaScriptが必要です。JavaScriptを有効にするか、対応したブラウザーをご利用ください。')+'</p></noscript>',
  '<form id="inquiry-form" action="'+INQUIRY_ENDPOINT+'" method="post" aria-describedby="inquiry-disclosure">',
  '<fieldset id="inquiry-fields" disabled><legend>'+('Inquiry details' if en else 'お問い合わせ内容')+'</legend>',
  '<label for="inquiry-app">'+('App' if en else '対象アプリ')+'</label><select id="inquiry-app" name="app">'+options+'</select>',
  '<label for="reply-email">'+('Reply email (optional)' if en else '返信先メールアドレス（任意）')+'</label><input id="reply-email" name="reply_email" type="email" autocomplete="email" inputmode="email" maxlength="254" aria-describedby="email-help">',
  '<p class="help" id="email-help">'+('Enter this only if you would like a reply. This form sends no automatic email.' if en else '返信が必要な場合だけ入力してください。このフォームから自動返信メールは送信しません。')+'</p>',
  '<label for="inquiry-message">'+('Message (required)' if en else '本文（必須）')+'</label><textarea id="inquiry-message" name="message" rows="8" maxlength="2000" required aria-describedby="message-help message-count"></textarea>',
  '<p class="help" id="message-help">'+('Up to 2,000 characters. If your app is not listed, select General / Another app and include its name in the message. For a previous submission, include its reference or approximate date and app; no identity document is needed in this form.' if en else '2,000文字以内。対象が一覧にない場合は「共通・その他のアプリ」を選び、本文にアプリ名を記載してください。以前の送信については受付番号、または送信日時とアプリ名を記載してください。このフォームに本人確認書類を添付する必要はありません。')+'</p><p class="help" id="message-count">0 / 2000</p>',
  '<div hidden aria-hidden="true"><label for="inquiry-website">Website</label><input id="inquiry-website" name="website" type="text" tabindex="-1" autocomplete="off" maxlength="200"></div>',
  '<button type="submit">'+('Send inquiry' if en else '送信する')+'</button></fieldset></form>',
  '<p id="inquiry-status" role="status" aria-live="polite" tabindex="-1"></p><p class="error" id="inquiry-error" role="alert" tabindex="-1"></p>',
  '<p class="help">'+('A reference is shown only after delivery is confirmed. If confirmation fails, the message may already have arrived; please avoid repeated submissions. A reference helps locate a message and is not proof of identity.' if en else '到着を確認できた場合のみ受付番号を表示します。確認できない場合でも届いている可能性があるため、繰り返し送信しないでください。受付番号は記録の特定に使うもので、本人確認を証明するものではありません。')+'</p>',
 ]
 return '<!DOCTYPE html>\n<html lang="'+lang+'"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="'+escape(csp,quote=True)+'"><meta name="referrer" content="no-referrer"><title>'+title+' | lizefield</title><style>'+CSS+'</style><script type="module" src="'+script+'"></script></head><body><main>\n'+'\n'.join(parts)+'\n</main></body></html>\n'

class Inspect(HTMLParser):
 VOID={'meta','link','br','hr','img','input','wbr'}
 def __init__(self):super().__init__();self.stack=[];self.links=[];self.ids=set();self.headings=0;self.scripts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag not in self.VOID:self.stack.append(tag)
  if 'id' in a:
   assert a['id'] not in self.ids,'duplicate id';self.ids.add(a['id'])
  if tag=='a':self.links.append(a['href'])
  if tag=='script':self.scripts.append(a.get('src',''))
  if tag=='h1':self.headings+=1
 def handle_endtag(self,tag):
  if tag not in self.VOID:assert self.stack and self.stack.pop()==tag,'unbalanced '+tag

def verify(pages):
 allowed=set(pages)|{'policies.json','scripts/build_policies.py','assets/inquiry.mjs','tests/inquiry.test.mjs','.gitignore'}
 actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts}
 assert not actual-allowed,'unexpected files in public project: '+', '.join(sorted(actual-allowed))
 parsed={}
 for path,expected in pages.items():
  actual=(ROOT/path).read_text();assert actual==expected,'stale output: '+path
  p=Inspect();p.feed(actual);p.close();assert not p.stack and p.headings==1,path
  assert not any('forms.gle/' in href for href in p.links),'legacy form offered as contact '+path
  if '/contact/' not in '/'+path:
   lang='ja' if path.startswith('ja/') else 'en'
   assert posixpath.relpath(contact_target(lang),posixpath.dirname(path) or '.') in p.links,'missing contact '+path
  if '/contact/' in '/'+path:
   assert p.scripts==[posixpath.relpath('assets/inquiry.mjs',posixpath.dirname(path))],path
   assert (ROOT/'assets/inquiry.mjs').is_file()
   assert 'id="inquiry-fields" disabled' in actual
  else:assert not p.scripts,'unexpected script '+path
  parsed[path]=p
 for path,p in parsed.items():
  for href in p.links:
   u=urlsplit(href)
   if u.scheme:
    assert u.scheme=='https' and u.netloc,href
    continue
   assert not href.startswith('/'),'root-absolute URL breaks project Pages: '+href
   dest=posixpath.normpath(posixpath.join(posixpath.dirname(path),unquote(u.path))) if u.path else path
   assert dest in parsed,(path,href,'missing page')
   if u.fragment:assert unquote(u.fragment) in parsed[dest].ids,(path,href,'missing anchor')
 print(f'Checked {len(pages)} bilingual pages: generated content, balanced HTML, one h1, unique IDs, contact links, relative links and language navigation.')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 pages={target(lang,app):render(lang,app) for lang in ['en','ja'] for app in [None,*DATA['apps']]}
 pages.update({contact_target(lang):render_contact(lang) for lang in ['en','ja']})
 if not args.check:
  for name,content in pages.items():
   p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
 verify(pages)
if __name__=='__main__':main()