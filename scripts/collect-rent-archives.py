import urllib.request,urllib.parse,zipfile,csv,io,json,datetime,re,concurrent.futures,sys
from pathlib import Path
DISTRICTS=['강남구','서초구','송파구','동작구','마포구','용산구','성동구','광진구'];ROOT=Path(__file__).resolve().parent.parent
PAGE='https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do'
def run(directory):
    cache=directory/'transactions84';cache.mkdir(parents=True,exist_ok=True)
    html=urllib.request.urlopen(PAGE,timeout=30).read(2_000_000).decode('utf-8')
    matches=re.findall(r'title="서울특별시_전월세가_(20\d\d)\.zip"\s+onclick="javascript:downloadFile\(\'(\d+)\'\)',html)
    yearnow=datetime.datetime.now().year;items=[(int(y),seq) for y,seq in matches if yearnow-10<=int(y)<yearnow]
    def process(item):
        year,seq=item;out=cache/f'rentArchive_{year}.json'
        if out.exists():return year,'cached'
        req=urllib.request.Request('https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?useCache=false',data=urllib.parse.urlencode({'infId':'OA-21276','infSeq':'3','seq':seq,'seqNo':''}).encode())
        blob=urllib.request.urlopen(req,timeout=90).read(80_000_001)
        if len(blob)>80_000_000:raise ValueError('Archive too large')
        z=zipfile.ZipFile(io.BytesIO(blob));names=[n for n in z.namelist() if n.lower().endswith(('.txt','.csv'))]
        if len(names)!=1:raise ValueError('Archive file structure changed')
        with z.open(names[0]) as raw:
            first=raw.readline()
        try:first.decode('utf-8-sig');enc='utf-8-sig'
        except UnicodeDecodeError:enc='cp949'
        rows=[]
        with z.open(names[0]) as raw:
            reader=csv.DictReader(io.TextIOWrapper(raw,encoding=enc,newline=''))
            headers=reader.fieldnames
            required=['자치구명','계약일','임대면적','보증금(만원)','임대료(만원)','건물용도']
            if not all(x in headers for x in required):raise ValueError('Archive fields changed: '+str(headers))
            for i,x in enumerate(reader):
                if x['자치구명'] not in DISTRICTS or x['건물용도'].strip()!='아파트':continue
                a=float(x['임대면적'] or 0)
                if not 84<=a<85 or float(x['임대료(만원)'] or 0)!=0:continue
                dt=x['계약일'].replace('-','').strip();amt=float(x['보증금(만원)'] or 0)
                if len(dt)!=8 or amt<=0 or not str(yearnow-10)<=dt[:4]<str(yearnow):continue
                rows.append({'id':f'archive-{year}-{i}','district':x['자치구명'],'kind':'rent','date':f'{dt[:4]}-{dt[4:6]}-{dt[6:]}','area':a,'amountManwon':amt,'name':x.get('건물명','').strip(),'dong':x.get('법정동명',''),'floor':x.get('층'),'source':PAGE})
        j={'kind':'rent','district':'서울8구','year':year,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'complete':True,'rows':rows};out.write_text(json.dumps(j,ensure_ascii=False));return year,len(rows)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for item in pool.map(process,items):print(item,flush=True)
if __name__=='__main__':run(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data')
