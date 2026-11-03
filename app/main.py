"""KICS Cloud Native lab: safe, clickable Kubernetes experiments with live telemetry."""
import json
import logging
import os
import re
import threading
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field

from cluster import bootstrap, change_release, describe, get_traffic, hpa, inspect, logs, restart, scale, set_traffic, state

log = logging.getLogger('kics-lab')
logging.basicConfig(level=logging.INFO)
app = FastAPI(title='KICS Kubernetes Deployment Laboratory', docs_url=None, redoc_url=None)
BASE = Path(__file__).resolve().parent
BOOTSTRAPPED = threading.Event()
LAST_ERROR = ''
OPERATIONS = Counter('kics_lab_operations_total', 'Lab operations', ['action', 'result'])
REQUESTS = Counter('kics_lab_demo_requests_total', 'Demo requests by track and outcome', ['track', 'outcome'])
READY_PODS = Gauge('kics_lab_ready_pods', 'Kubernetes pods with ready containers')
TOTAL_PODS = Gauge('kics_lab_total_pods', 'Total Kubernetes pods in lab namespace')
CANARY = Gauge('kics_lab_green_traffic_weight_percent', 'Configured Nginx green upstream weight')
UP = Gauge('kics_lab_cluster_connected', 'Kubernetes API available')
DEMO_URL = os.environ.get('DEMO_INTERNAL_URL','http://k3s:30080/')


def init_loop():
    global LAST_ERROR
    while not BOOTSTRAPPED.is_set():
        try:
            bootstrap()
            state()  # verify seeded objects are readable
            BOOTSTRAPPED.set()
            LAST_ERROR = ''
            log.info('KICS Kubernetes classroom namespace provisioned')
        except Exception as exc:
            LAST_ERROR = str(exc)[:500]
            log.warning('Waiting for cluster / bootstrap: %s',LAST_ERROR)
        if not BOOTSTRAPPED.is_set():time.sleep(8)


@app.on_event('startup')
def on_startup():
    threading.Thread(target=init_loop,daemon=True,name='lab-bootstrap').start()


@app.get('/')
def home():
    return FileResponse(BASE/'static'/'index.html')


@app.get('/healthz')
def healthz():
    return {'status':'up','cluster_bootstrapped':BOOTSTRAPPED.is_set()}


@app.get('/api/status')
def status():
    if not BOOTSTRAPPED.is_set():return {'connected':False,'initializing':True,'reason':LAST_ERROR or 'K3s starting, kubeconfig or API not yet ready'}
    try:
        result=state()
        UP.set(1);READY_PODS.set(result['ready_pods']);TOTAL_PODS.set(result['total_pods']);CANARY.set(result['traffic_green'])
        return result
    except Exception as exc:
        UP.set(0)
        return {'connected':False,'initializing':False,'reason':str(exc)[:400]}


def require_ready():
    if not BOOTSTRAPPED.is_set():raise HTTPException(503,'Kubernetes cluster is still starting. Retry soon.')


def require_action(header):
    # Cross-site requests cannot attach this header unless CORS preflight is approved.
    if header!='1':raise HTTPException(403,'Browser action header required')
    require_ready()


class Action(BaseModel):
    operation: str
    track: str | None = None
    version: str | None = None
    percentage: int | None = Field(default=None,ge=0,le=100)
    replicas: int | None = Field(default=None,ge=1,le=4)
    enabled: bool | None = None


@app.post('/api/action')
def action(body:Action,x_kics_lab:str|None=Header(default=None)):
    require_action(x_kics_lab)
    op=body.operation
    try:
        if op=='traffic' and body.percentage is not None:
            result={'traffic_green':set_traffic(body.percentage)}
        elif op=='release' and body.version in ('v1','v2'):
            result={'blue_release':change_release(body.version)}
        elif op=='scale' and body.track in ('blue','green') and body.replicas is not None:
            result={'track':body.track,'replicas':scale(body.track,body.replicas)}
        elif op=='restart' and body.track in ('blue','green','router'):
            result={'deployment':restart('kics-'+body.track)}
        elif op=='hpa' and body.enabled is not None:
            result={'enabled':hpa(body.enabled)}
        else:raise HTTPException(400,'Unsupported predefined classroom action')
        OPERATIONS.labels(action=op,result='ok').inc()
        return {'ok':True,'result':result,'message':'Kubernetes change submitted; workloads may take a few seconds to converge.'}
    except HTTPException:raise
    except ValueError as exc:
        OPERATIONS.labels(action=op,result='invalid').inc()
        raise HTTPException(400,str(exc)) from exc
    except Exception as exc:
        OPERATIONS.labels(action=op,result='error').inc()
        log.exception('Kubernetes operation failed')
        raise HTTPException(502,'Kubernetes API operation failed: '+str(exc)[:250]) from exc


SECTIONS = {'nodes','namespaces','pods','deployments','services','replicasets','configmaps','secrets','events','hpa','top'}


@app.get('/api/inspect/{section}')
def inspect_route(section:str):
    require_ready()
    if section not in SECTIONS:raise HTTPException(404,'Section not available')
    try:return {'section':section,'data':inspect(section)}
    except Exception as exc:raise HTTPException(502,'Inspection failed: '+str(exc)[:250]) from exc


@app.get('/api/logs/{track}')
def logs_route(track:str):
    require_ready()
    if track not in {'blue','green','router'}:raise HTTPException(404,'Unknown workload')
    try:return PlainTextResponse(logs(track))
    except Exception as exc:raise HTTPException(502,'Logs unavailable: '+str(exc)[:200]) from exc


@app.get('/api/describe/{track}')
def describe_route(track:str):
    require_ready()
    if track not in {'blue','green','router'}:raise HTTPException(404,'Unknown workload')
    try:return describe(track)
    except Exception as exc:raise HTTPException(502,'Describe failed: '+str(exc)[:200]) from exc


@app.get('/api/sample')
def sample(count:int=Query(default=24,ge=1,le=100)):
    require_ready()
    results={'blue':0,'green':0,'failed':0,'other':0}
    errors=[]
    with httpx.Client(timeout=4.0,follow_redirects=False) as http:
        for _ in range(count):
            try:
                r=http.get(DEMO_URL, headers={'Cache-Control':'no-cache'})
                if r.status_code!=200:raise ValueError(f'HTTP {r.status_code}')
                mark=re.search('data-kics-track="(blue|green)"',r.text)
                track=mark.group(1) if mark else 'other'
                results[track]+=1
                REQUESTS.labels(track=track,outcome='ok').inc()
            except Exception as exc:
                results['failed']+=1
                REQUESTS.labels(track='unknown',outcome='error').inc()
                if len(errors)<3:errors.append(str(exc)[:120])
    return {'requests':count,'results':results,'errors':errors,'note':'Nginx upstream weights are approximate; short samples vary. Router restarts take time.'}


@app.get('/metrics')
def metrics():
    # Metrics are teaching telemetry. No student identifiers, passwords or tokens.
    return Response(content=generate_latest(),media_type=CONTENT_TYPE_LATEST)
