import json,sys,re,urllib.request
from html.parser import HTMLParser
DISTRICTS=['강남구','서초구','송파구','동작구','마포구','용산구','성동구','광진구']
def request(url):
    with urllib.request.urlopen(url,timeout=30) as r:return r.read(3000000)
class TableParser(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None;self.hrefs=[];self.incomment=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr':self.row=[];self.hrefs=[]
        if tag in ['td','th'] and self.row is not None:self.cell=[]
        if tag=='a' and self.row is not None and a.get('href','').startswith('https://'):self.hrefs.append(a['href'])
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ['td','th'] and self.row is not None and self.cell is not None:self.row.append(re.sub(r'\s+',' ',''.join(self.cell)).strip());self.cell=None
        if tag=='tr' and self.row is not None:
            if self.row:self.rows.append((self.row,self.hrefs))
            self.row=None

def parse_board(html,url,label):
    if '공고게시일' not in html or '공고명' not in html:raise ValueError('Public board structure changed')
    parser=TableParser();parser.feed(html);notices=[];count=0
    for cells,links in parser.rows:
        if len(cells)<7 or not re.fullmatch(r'\d+',cells[0]):continue
        count+=1;name=cells[2];source=next((u for u in links if 'i-sh.co.kr/' in u or 'apply.lh.or.kr/' in u),None)
        if not source:continue
        district=next((d for d in DISTRICTS if d in name or d[:-1] in name),None)
        # Unknown region remains visible only in the source log, not mixed into target results.
        if district is None:continue
        dates=[x for x in cells if re.fullmatch(r'\d{4}-\d{2}-\d{2}',x)]
        notices.append({'district':district,'name':name,'published':dates[0] if dates else None,'source':source,'publisher':label,'status':'접수일 원문 확인 필요'})
    if count==0 and not re.search(r'없습니다|0건|총\s*0',html):raise ValueError('Public board rows missing')
    return {'url':url,'publisher':label,'scannedRows':count,'notices':notices}

def main():
    out={'checks':[],'notices':[]}
    for label,url in [('SH 공공분양','https://housing.seoul.go.kr/site/main/sh/publicSale/01/list'),('LH 공공분양','https://housing.seoul.go.kr/site/main/lh/publicSale/05/list?cnpCdNm=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C')]:
        try:
            b=parse_board(request(url).decode('utf-8'),url,label);out['notices']+=b.pop('notices');out['checks'].append({**b,'status':'ok'})
        except Exception as e:out['checks'].append({'url':url,'publisher':label,'status':'error','message':type(e).__name__})
    out['announcementStatus']='partial' if any(x['status']=='ok' for x in out['checks']) else 'error'
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
