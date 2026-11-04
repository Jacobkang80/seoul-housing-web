export const DISTRICTS=['강남구','서초구','송파구','동작구','마포구','용산구','성동구','광진구'];
export function prevMonth(s){const[y,m]=s.split('-').map(Number);return(m===1?y-1:y)+'-'+String(m===1?12:m-1).padStart(2,'0')}
export function change(rows,field){const r=rows.filter(x=>Number.isFinite(x[field])&&x[field]>0).sort((a,b)=>a.month.localeCompare(b.month));const latest=r.at(-1);if(!latest)return null;const before=r.find(x=>x.month===prevMonth(latest.month));return{month:latest.month,value:latest[field],count:latest[field+'Count']??null,pct:before?(latest[field]/before[field]-1)*100:null}}
export function isRecentVerification(value,now=new Date()){
  if(typeof value!=='string'||!Number.isFinite(+now))return false;
  if(/^\d{4}-\d{2}-\d{2}$/.test(value)){
    const date=Date.parse(value+'T00:00:00Z');
    if(!Number.isFinite(date)||new Date(date).toISOString().slice(0,10)!==value)return false;
    const today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Seoul'}).format(now);
    const days=(Date.parse(today+'T00:00:00Z')-date)/86400000;
    return days>=0&&days<=14;
  }
  const age=+now-Date.parse(value);
  return Number.isFinite(age)&&age>=0&&age<=14*86400000;
}
export function filterListings(rows,s,now=new Date()){return rows.filter(x=>DISTRICTS.includes(x.district)&&Number.isFinite(x.price)&&x.price>0&&x.price<s.budget&&x.price<25&&Number.isFinite(x.subwayMin)&&x.subwayMin>=0&&x.subwayMin<=s.walk&&x.subwayStation&&(s.includeUnknownShuttle?(!Number.isFinite(x.shuttleMin)||(x.shuttleMin>=0&&x.shuttleMin<=s.walk)):(Number.isFinite(x.shuttleMin)&&x.shuttleMin>=0&&x.shuttleMin<=s.walk&&x.shuttleStop))&&/^https?:\/\//.test(x.source||'')&&isRecentVerification(x.verifiedDate,now)).sort((a,b)=>s.sort==='walk'?a.subwayMin-b.subwayMin||a.price-b.price:a.price-b.price||a.subwayMin-b.subwayMin)}
