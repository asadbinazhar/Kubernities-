from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'KICS_Kubernetes_Kubectl_One_Page_Cheat_Sheet.pdf'
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FM='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
for name,path in [('DejaVu',F),('DejaVuBold',FB),('DejaVuMono',FM)]:
 pdfmetrics.registerFont(TTFont(name,path))
W,H=A4
c=canvas.Canvas(str(OUT),pagesize=A4)
navy=HexColor('#0D1D35'); navy2=HexColor('#173351'); txt=HexColor('#16283d'); muted=HexColor('#61758a'); blue=HexColor('#0779BD'); line=HexColor('#D9E5EF')
c.setFillColor(navy);c.rect(0,H-102,W,102,stroke=0,fill=1)
c.setFillColor(HexColor('#68C6FF'));c.setFont('DejaVuBold',9);c.drawString(31,H-33,'KICS  |  UET LAHORE  |  HUAWEI HCCDA')
c.setFillColor(HexColor('#FFFFFF'));c.setFont('DejaVuBold',20);c.drawString(31,H-65,'Kubernetes: Essential kubectl')
c.setFillColor(HexColor('#BCD6EE'));c.setFont('DejaVu',9);c.drawString(31,H-86,'One-page classroom reference  |  Namespace: kics-lab')

colwidth=(W-75)/2
lx=31;rx=31+colwidth+13

def block(x,y,title,items):
 c.setFillColor(blue);c.roundRect(x,y-18,colwidth,21,5,stroke=0,fill=1)
 c.setFont('DejaVuBold',9);c.setFillColor(HexColor('#FFFFFF'));c.drawString(x+9,y-11.5,title)
 cy=y-31
 for cmd,note in items:
  c.setFont('DejaVuMono',7.1);c.setFillColor(txt);c.drawString(x+2,cy,cmd)
  cy-=11.4
  c.setFont('DejaVu',7.2);c.setFillColor(muted);c.drawString(x+2,cy,note)
  cy-=22
 return cy-2

left_sections=[
 ('01  Discover & Inspect',[
  ('kubectl get nodes -o wide','Cluster node status and IPs'),
  ('kubectl get ns','Show namespaces'),
  ('kubectl get pods -n kics-lab -o wide','Pods, nodes, IP and readiness'),
  ('kubectl get deploy,rs,svc -n kics-lab','Deployments, ReplicaSets, Services'),
  ('kubectl describe pod POD -n kics-lab','Pod details, events, probe failures')]),
 ('02  Troubleshooting',[
  ('kubectl logs POD -n kics-lab','Read container logs'),
  ('kubectl logs POD --previous -n kics-lab','Logs from crashed previous container'),
  ('kubectl get events -n kics-lab','Check recent warnings and failures'),
  ('kubectl top pods -n kics-lab','CPU / RAM (Metrics Server required)')]),
 ('03  Safe Updates',[
  ('kubectl rollout status deploy/kics-blue -n kics-lab','Wait for rolling deployment'),
  ('kubectl rollout history deploy/kics-blue -n kics-lab','Inspect previous rollout revisions'),
  ('kubectl rollout undo deploy/kics-blue -n kics-lab','Undo last Deployment revision')])]
right_sections=[
 ('04  Manage Deployments',[
  ('kubectl scale deploy/kics-blue -n kics-lab --replicas=2','Change desired replicas'),
  ('kubectl rollout restart deploy/kics-blue -n kics-lab','Recreate pods using rolling update'),
  ('kubectl get hpa -n kics-lab','Inspect Horizontal Pod Autoscaler'),
  ('kubectl get cm,secret -n kics-lab','List ConfigMaps and Secret names')]),
 ('05  Services & Connectivity',[
  ('kubectl get svc -n kics-lab','See ClusterIP and NodePort'),
  ('kubectl get endpoints -n kics-lab','Service backend endpoints'),
  ('kubectl port-forward svc/NAME 8080:80 -n kics-lab','Forward local port (keep terminal open)'),
  ('kubectl exec -it POD -n kics-lab -- sh','Open shell (if image contains sh)')]),
 ('06  YAML & Context',[
  ('kubectl apply -f app.yaml','Create/update resources declaratively'),
  ('kubectl diff -f app.yaml','Preview desired-state changes'),
  ('kubectl delete -f app.yaml','Delete resources in selected YAML'),
  ('kubectl config current-context','Identify active cluster context')])]

y0=H-123
leftend=y0
for title,items in left_sections:
 leftend=block(lx,leftend,title,items)
rightend=y0
for title,items in right_sections:
 rightend=block(rx,rightend,title,items)

# Bottom: classroom note and commands specific to ZIP.
footer_y=55
c.setFillColor(HexColor('#EAF5FF'));c.roundRect(31,footer_y,W-62,49,7,stroke=0,fill=1)
c.setFillColor(navy2);c.setFont('DejaVuBold',8.1);c.drawString(41,footer_y+33,'Using this lab ZIP? The ECS already has kubectl inside K3s.')
c.setFont('DejaVuMono',8);c.setFillColor(HexColor('#075E99'));c.drawString(41,footer_y+19,'./kubectl.sh get pods -n kics-lab -o wide')
c.setFont('DejaVu',7.5);c.setFillColor(muted);c.drawString(41,footer_y+8,'Run ./kubectl.sh followed by the remaining command; replace POD/NAME with real values.')
c.setFont('DejaVu',7.2);c.setFillColor(muted);c.drawString(31,34,'Safety: use -n kics-lab for namespace-scoped operations. Never paste unknown delete commands.')
c.drawRightString(W-31,34,'KICS classroom quick reference  •  2026')
if min(leftend,rightend)<113:print('WARNING: bottom content too low',leftend,rightend)
c.showPage();c.save()
print(OUT)
