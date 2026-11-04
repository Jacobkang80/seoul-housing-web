import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import vm from 'node:vm';
import {pushWithRetry} from '../scripts/save-published-data.mjs';
import {isRecentVerification} from '../lib/domain.mjs';

test('a real Git rejection is retried and the generated commit reaches the remote',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'housing-push-'));
  const remote=path.join(root,'remote.git'),local=path.join(root,'local');
  const git=(args)=>execFileSync('git',args,{encoding:'utf8',stdio:'pipe'});
  try{
    git(['init','--bare','--initial-branch=main',remote]);git(['init','--initial-branch=main',local]);
    git(['-C',local,'config','user.name','test']);git(['-C',local,'config','user.email','test@example.invalid']);
    await fs.writeFile(path.join(local,'snapshot.json'),'{}');git(['-C',local,'add','.']);git(['-C',local,'commit','-m','generated snapshot']);git(['-C',local,'remote','add','origin',remote]);
    const hook=path.join(remote,'hooks/pre-receive');
    await fs.writeFile(hook,'#!/bin/sh\nif [ ! -e rejected-once ]; then touch rejected-once; echo "temporary rejection" >&2; exit 1; fi\n',{mode:0o755});
    let attempts=0;
    await pushWithRetry({push:()=>{attempts++;return git(['-C',local,'push','origin','HEAD:main'])},wait:async()=>{},log:()=>{}});
    assert.equal(attempts,2);assert.equal(git(['--git-dir',remote,'rev-parse','main']),git(['-C',local,'rev-parse','HEAD']));
  }finally{await fs.rm(root,{recursive:true,force:true})}
});

test('persistent save errors stop after four attempts without force-pushing',async()=>{
  let attempts=0;const delays=[];
  await assert.rejects(pushWithRetry({push:()=>{attempts++;throw Error('remote unavailable')},wait:async ms=>delays.push(ms),log:()=>{}}),/remote unavailable/);
  assert.equal(attempts,4);assert.deepEqual(delays,[2000,5000,15000]);
});

test('date-only verification follows Korean calendar dates before 09:00',()=>{
  const morning=new Date('2026-11-03T20:22:00Z'); // Nov 4, 05:22 KST
  assert(isRecentVerification('2026-11-04',morning));
  assert(isRecentVerification('2026-10-21',morning));
  assert(!isRecentVerification('2026-10-20',morning));
  assert(!isRecentVerification('2026-11-05',morning));
  assert(!isRecentVerification('2026-02-30',morning));
  assert(!isRecentVerification('2026-11-04T00:00:00Z',morning));
});

async function workerHarness({storageDisabled=false,writeFails=false}={}){
  let response=new Response('{"sale":20}',{headers:{'Content-Type':'application/json'}});
  const stored=new Map(),handlers={};
  const cache={put:async(key,value)=>{if(writeFails)throw Error('quota');stored.set(key.url||String(key),value)},match:async key=>stored.get(key.url||String(key))?.clone()};
  const context={self:{location:{origin:'https://example.com',href:'https://example.com/seoul-housing-web/sw.js'},addEventListener:(name,fn)=>handlers[name]=fn},caches:{open:async()=>{if(storageDisabled)throw Error('storage disabled');return cache}},URL,Request,Response,Headers,fetch:async()=>response.clone()};
  vm.runInNewContext(await fs.readFile(new URL('../web/pwa/sw.js',import.meta.url),'utf8'),context);
  return {setResponse:r=>response=r,load:async n=>{let result;handlers.fetch({request:new Request('https://example.com/seoul-housing-web/data/snapshot.json?ts='+n),respondWith:p=>result=p});return result}};
}

test('temporary HTTP 503 uses cached data and marks it as a fallback',async()=>{
  const worker=await workerHarness();await worker.load(1);worker.setResponse(new Response('unavailable',{status:503}));
  const response=await worker.load(2);assert.equal(response.headers.get('X-Seoul-Offline'),'1');assert.equal((await response.json()).sale,20);
});

test('cache quota failure never replaces a good online response with old data',async()=>{
  const worker=await workerHarness({writeFails:true});const response=await worker.load(1);
  assert.equal((await response.json()).sale,20);assert.equal(response.headers.get('X-Seoul-Offline'),null);
});

test('disabled browser storage still allows online viewing',async()=>{
  const worker=await workerHarness({storageDisabled:true});assert.equal((await(await worker.load(1)).json()).sale,20);
});
