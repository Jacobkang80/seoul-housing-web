import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const git=(args)=>execFileSync('git',args,{stdio:'inherit',timeout:45000});
export async function pushWithRetry({push=()=>git(['push','origin','HEAD:main']),wait=ms=>new Promise(resolve=>setTimeout(resolve,ms)),log=console.warn,delays=[2000,5000,15000]}={}){
  for(let attempt=0;;attempt++){
    try{return await push()}
    catch(error){
      if(attempt>=delays.length)throw error;
      log(`Git push failed; retry ${attempt+1}/${delays.length} in ${delays[attempt]/1000}s`);
      await wait(delays[attempt]);
    }
  }
}
export async function savePublishedData(){
  git(['config','user.name','github-actions[bot]']);
  git(['config','user.email','41898282+github-actions[bot]@users.noreply.github.com']);
  git(['add','data/snapshot.json','public']);
  try{git(['diff','--cached','--quiet']);return}
  catch(error){if(error.status!==1)throw error}
  git(['commit','-m','Refresh public web dashboard']);
  await pushWithRetry();
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await savePublishedData();
