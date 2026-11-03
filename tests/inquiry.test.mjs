import assert from 'node:assert/strict';
import test from 'node:test';
import {INQUIRY_ENDPOINT, mountInquiry} from '../assets/inquiry.mjs';
const reference='12345678-1234-4234-8234-123456789abc';
function fixture({lang='en', valid=true, action=INQUIRY_ENDPOINT}={}) {
  let focused, resets=0;
  const node=(value='')=>({value,textContent:'',disabled:true,listeners:{},addEventListener(name,callback){this.listeners[name]=callback;},focus(){focused=this;}});
  const fields={app:node('purea'),message:node('Synthetic inquiry'),reply_email:node('example@example.invalid'),website:node('')};
  const form={...node(),action,elements:{namedItem:name=>fields[name]},reportValidity:()=>valid,reset(){resets++;for(const field of Object.values(fields))field.value='';fields.app.value='general';}};
  const nodes={'inquiry-form':form,'inquiry-fields':node(),'inquiry-status':node(),'inquiry-error':node(),'message-count':node()};
  const doc={documentElement:{lang},getElementById:id=>nodes[id]};
  return {doc,nodes,fields,form,get resets(){return resets;},get focused(){return focused;},submit(){return form.listeners.submit({preventDefault(){}});}};
}
test('confirmed delivery sends only to fixed API without cookies/referrer, then clears and focuses receipt',async()=>{
  const f=fixture(),calls=[];
  mountInquiry(f.doc,async(url,init)=>{calls.push({url,init});return Response.json({ok:true,reference});});
  assert.equal(f.nodes['inquiry-fields'].disabled,false);
  await f.submit();
  assert.equal(calls.length,1);assert.equal(calls[0].url,INQUIRY_ENDPOINT);
  assert.equal(calls[0].init.credentials,'omit');assert.equal(calls[0].init.mode,'cors');assert.equal(calls[0].init.referrerPolicy,'no-referrer');assert.equal(calls[0].init.redirect,'error');
  assert.deepEqual(JSON.parse(calls[0].init.body),{app:'purea',message:'Synthetic inquiry',reply_email:'example@example.invalid',website:''});
  assert.equal(f.resets,1);assert.ok(f.nodes['inquiry-status'].textContent.includes(reference));assert.equal(f.focused,f.nodes['inquiry-status']);
});
test('invalid browser form and whitespace-only messages do not send',async()=>{
  const f=fixture({valid:false});mountInquiry(f.doc,()=>{throw Error('Must not send');});await f.submit();assert.equal(f.resets,0);
  const blank=fixture({lang:'ja'});blank.fields.message.value='   ';mountInquiry(blank.doc,()=>{throw Error('Must not send');});await blank.submit();assert.match(blank.nodes['inquiry-error'].textContent,/空白/);
});
test('pending state prevents duplicate submissions and disables controls',async()=>{
  const f=fixture();let done,calls=0;const pending=new Promise(resolve=>{done=resolve;});
  mountInquiry(f.doc,async()=>{calls++;return pending;});const first=f.submit();assert.equal(f.nodes['inquiry-fields'].disabled,true);await f.submit();assert.equal(calls,1);
  done(Response.json({ok:true,reference}));await first;assert.equal(f.nodes['inquiry-fields'].disabled,false);
});
for(const [label,send] of [
  ['rate limit',async()=>new Response(null,{status:429})],['validation',async()=>new Response(null,{status:400})],
  ['server failure',async()=>new Response(null,{status:502})],['network/timeout',async()=>{throw new Error('synthetic transport failure');}],
  ['malformed success',async()=>Response.json({ok:true})],['unsafe receipt',async()=>Response.json({ok:true,reference:'<img src=x onerror=alert(1)>'})],
])test('unconfirmed '+label+' keeps input and never retries',async()=>{
  const f=fixture({lang:'ja'});let calls=0;mountInquiry(f.doc,async(...args)=>{calls++;return send(...args);});await f.submit();
  assert.equal(calls,1);assert.equal(f.resets,0);assert.equal(f.fields.message.value,'Synthetic inquiry');assert.equal(f.fields.reply_email.value,'example@example.invalid');
  assert.ok(f.nodes['inquiry-error'].textContent);assert.equal(f.nodes['inquiry-status'].textContent,'');assert.equal(f.nodes['inquiry-fields'].disabled,false);
});
test('endpoint tampering never enables or sends the form',()=>{
  const f=fixture({action:'https://evil.invalid'});mountInquiry(f.doc,()=>{throw Error('Must not send');});
  assert.equal(f.nodes['inquiry-fields'].disabled,true);assert.equal(f.form.listeners.submit,undefined);
});

test('unconfirmed delivery never redirects either language to the retired Google Form',async()=>{
  for(const lang of ['en','ja']){
    const f=fixture({lang});let calls=0;
    mountInquiry(f.doc,async()=>{calls++;throw Error('synthetic failure');});await f.submit();
    assert.equal(calls,1);assert.equal(f.resets,0);assert.equal(f.fields.message.value,'Synthetic inquiry');
    assert.doesNotMatch(f.nodes['inquiry-error'].textContent,/Google|forms\.gle|グーグル/);
  }
});
