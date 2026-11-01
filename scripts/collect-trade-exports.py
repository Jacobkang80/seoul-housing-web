import urllib.request,urllib.parse,xlrd,concurrent.futures,json,datetime,sys,os
from pathlib import Path
CODES={'강남구':'11680','서초구':'11650','송파구':'11710','동작구':'11590','마포구':'11440','용산구':'11170','성동구':'11200','광진구':'11215'}
SOURCE='https://land.seoul.go.kr/land/rtms/transactionInfo.do'
def run(directory):
    now=datetime.datetime.now(datetime.timezone.utc);cache=directory/'transactions84';cache.mkdir(parents=True,exist_ok=True);tasks=[]
    for year in range(now.year,now.year-11,-1):
        for district,code in CODES.items():
            p=cache/f'saleExport_{district}_{year}.json'
            if p.exists() and (year<now.year-1 or (year<now.year and json.loads(p.read_text())['checkedAt'][:10]==now.isoformat()[:10])):continue
            tasks.append((year,district,code,p))
    errors=[]
    def process(task):
        year,district,code,path=task
        try:
            params={'sggCd':code,'bjdong10Cd':'','selectGubun':'1','rnCd':'','startDate':str(year)+'0101','endDate':now.strftime('%Y%m%d') if year==now.year else str(year)+'1231','bldgGbn':'AP','frmArea':'66','toArea':'99','rightGbnGrp':'RTMS'}
            url='https://land.seoul.go.kr/land/rtms/getRtmsTransactionList.do?'+urllib.parse.urlencode(params)
            b=urllib.request.urlopen(url,timeout=70).read(25_000_001)
            if not b.startswith(b'\xd0\xcf\x11\xe0') or len(b)>25_000_000:raise ValueError('Official annual XLS response changed')
            book=xlrd.open_workbook(file_contents=b);sheet=book.sheet_by_index(0);headers=sheet.row_values(0);required=['시군구','건물명','계약일','거래금액(만원)','건물전용면적(㎡)']
            if not all(k in headers for k in required):raise ValueError('Annual XLS fields changed')
            rows=[]
            for i in range(1,sheet.nrows):
                r=dict(zip(headers,sheet.row_values(i)));area=float(str(r['건물전용면적(㎡)']).replace(',','') or 0)
                if not 84<=area<85 or str(r.get('계약해제일','')).strip():continue
                location=str(r['시군구']).strip();dt=str(r['계약일']).replace('-','').replace('.0','');amount=float(str(r['거래금액(만원)']).replace(',','') or 0)
                if district not in location or not dt.startswith(str(year)) or len(dt)!=8:raise ValueError('Annual XLS scope mismatch')
                if amount<=0:continue
                rows.append({'id':f'export-{code}-{year}-{i}','district':district,'kind':'sale','date':f'{dt[:4]}-{dt[4:6]}-{dt[6:]}','area':area,'amountManwon':amount,'name':str(r['건물명']).strip(),'dong':location.replace(district,'').strip(),'floor':r.get('층'),'source':SOURCE})
            payload={'kind':'sale','district':district,'year':year,'checkedAt':now.isoformat(),'complete':True,'rows':rows,'download':url};tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(payload,ensure_ascii=False));os.replace(tmp,path);return f'{district} {year}: {len(rows)}'
        except Exception as e:errors.append({'kind':'sale','district':district,'year':year,'error':type(e).__name__});return f'{district} {year}: unavailable ({type(e).__name__})'
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for msg in pool.map(process,tasks):print(msg,flush=True)
    (directory/'trade-export-errors.json').write_text(json.dumps(errors,ensure_ascii=False));return errors
if __name__=='__main__':sys.exit(1 if run(Path(sys.argv[1])) else 0)
