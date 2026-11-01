import unittest,tempfile,json,datetime,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from aggregate84 import aggregate
class MeanTest(unittest.TestCase):
 def test_sources_and_currency(self):
  year=datetime.datetime.now().year
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);c=p/'transactions84';c.mkdir()
   def save(name,kind,rows):
    (c/name).write_text(json.dumps({'kind':kind,'district':'송파구','year':year,'checkedAt':'now','complete':True,'rows':rows}))
   def row(id,kind,amount):return {'id':id,'kind':kind,'district':'송파구','date':str(year)+'-01-01','area':84.9,'amountManwon':amount}
   save('saleExport_송파구.json','sale',[row('export-1','sale',100000),row('export-2','sale',200000)])
   save('rentExport_송파구.json','rent',[row('rent-export-1','rent',50000)])
   save('old-public-query.json','sale',[row('old-1','sale',900000)])
   x=aggregate(p)['monthly84'][0]
   self.assertEqual(x['saleCount'],2);self.assertEqual(x['sale'],15);self.assertEqual(x['rent'],5)
if __name__=='__main__':unittest.main()
