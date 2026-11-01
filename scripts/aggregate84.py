import json,datetime,sys
from pathlib import Path
SOURCES={'sale':'https://land.seoul.go.kr/land/rtms/transactionInfo.do','rent':'https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do'}
def aggregate(directory):
    now=datetime.datetime.now(datetime.timezone.utc);records=[];coverage=[]
    for p in (directory/'transactions84').glob('*.json'):
        j=json.loads(p.read_text());
        if not (p.name.startswith('saleExport_') or p.name.startswith('rentExport_') or p.name.startswith('rentArchive_')):continue
        coverage.append({k:j[k] for k in ['kind','district','year','checkedAt','complete']})
        for r in j['rows']:
            if r['kind']=='sale' and not r['id'].startswith('export-'):continue
            if r['kind']=='rent' and ((int(r['date'][:4])<now.year and not r['id'].startswith('archive-')) or (int(r['date'][:4])>=now.year and not r['id'].startswith('rent-export-'))):continue
            records.append(r)
    records=list({r['kind']+r['id']:r for r in records}.values());groups={}
    for r in records:
        key=(r['district'],r['date'][:7]);g=groups.setdefault(key,{'district':r['district'],'month':r['date'][:7],'sale':None,'rent':None,'saleCount':0,'rentCount':0,'saleSumManwon':0,'rentSumManwon':0,'source':SOURCES['sale'],'rentSource':SOURCES['rent']});k=r['kind'];g[k+'Count']+=1;g[k+'SumManwon']+=r['amountManwon']
    for g in groups.values():
        for k in ['sale','rent']:
            if g[k+'Count']:g[k]=round(g[k+'SumManwon']/g[k+'Count']/10000,6)
        g.update(metric='apt84_monthly_mean',unit='억원')
    monthly=sorted(groups.values(),key=lambda x:(x['district'],x['month']));out={'metric':'apt84_monthly_mean','unit':'억원','areaMin':84,'areaMaxExclusive':85,'monthly84':monthly,'coverage':coverage,'updated':now.isoformat(),'recordCount':len(records)}
    (directory/'monthly84.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));(directory/'transactions84.json').write_text(json.dumps(records,ensure_ascii=False));return out
if __name__=='__main__':
    out=aggregate(Path(sys.argv[1]));print(json.dumps({'rows':len(out['monthly84']),'records':out['recordCount']}))
