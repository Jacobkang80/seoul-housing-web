import urllib.request,urllib.parse,xlrd,concurrent.futures,json,datetime,sys,os
from pathlib import Path
CODES={'강남구':'11680','서초구':'11650','송파구':'11710','동작구':'11590','마포구':'11440','용산구':'11170','성동구':'11200','광진구':'11215'}
SOURCE='https://land.seoul.go.kr/land/rtms/transactionInfo.do'
def run(directory):
    now=datetime.datetime.now(datetime.timezone.utc);year=now.year;cache=directory/'transactions84';cache.mkdir(parents=True,exist_ok=True);errors=[]
    def f(item):
        district,code=item
        try:
            params={'sggCd':code,'bjdongCd':'','selectGubun':'2','rentGbn':'1','rnCd':'','startDate':str(year)+'0101','endDate':now.strftime('%Y%m%d'),'bldgGbn':'AP','frmArea':'66','toArea':'99'}
            url='https://land.seoul.go.kr/land/rent/getRentTransactionList.do?'+urllib.parse.urlencode(params);b=urllib.request.urlopen(url,timeout=70).read(30_000_001)
            if not b.startswith(b'\xd0\xcf\x11\xe0') or len(b)>30_000_000:raise ValueError('Rent XLS response changed')
            s=xlrd.open_workbook(file_contents=b).sheet_by_index(0);h=s.row_values(0);needed=['시군구','단지명','전월세구분','계약일','보증금(만원)','임대료(만원)','전용면적(㎡)']
            if not all(k in h for k in needed):raise ValueError('Rent XLS fields changed')
            rows=[]
            for i in range(1,s.nrows):
                r=dict(zip(h,s.row_values(i)));a=float(str(r['전용면적(㎡)']).replace(',','') or 0);rent=float(str(r['임대료(만원)']).replace(',','') or 0)
                if not 84<=a<85 or rent!=0 or str(r['전월세구분']).strip()!='전세':continue
                dt=str(r['계약일']).replace('-','').replace('.0','');location=str(r['시군구']).strip();amt=float(str(r['보증금(만원)']).replace(',','') or 0)
                if district not in location or not dt.startswith(str(year)) or len(dt)!=8:raise ValueError('Rent XLS scope mismatch')
                if amt<=0:continue
                rows.append({'id':f'rent-export-{code}-{year}-{i}','district':district,'kind':'rent','date':f'{dt[:4]}-{dt[4:6]}-{dt[6:]}','area':a,'amountManwon':amt,'name':str(r['단지명']).strip(),'dong':location.replace(district,'').strip(),'floor':r.get('층'),'source':SOURCE})
            out=cache/f'rentExport_{district}_{year}.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps({'kind':'rent','district':district,'year':year,'checkedAt':now.isoformat(),'complete':True,'rows':rows,'download':url},ensure_ascii=False));os.replace(tmp,out);return district,len(rows)
        except Exception as e:errors.append({'kind':'rent','district':district,'year':year,'error':type(e).__name__});return district,type(e).__name__
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for x in pool.map(f,CODES.items()):print(x,flush=True)
    (directory/'rent-export-errors.json').write_text(json.dumps(errors,ensure_ascii=False));return errors
if __name__=='__main__':sys.exit(1 if run(Path(sys.argv[1])) else 0)
