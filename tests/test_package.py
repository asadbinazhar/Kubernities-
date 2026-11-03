"""Offline source validations; runtime acceptance requires Docker on dedicated Ubuntu ECS."""
import ast
import json
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]

class PackageTests(unittest.TestCase):
    def test_python_parses(self):
        for path in (ROOT/'app').rglob('*.py'):ast.parse(path.read_text())

    def test_valid_yaml(self):
        for path in [ROOT/'compose.yaml',ROOT/'monitoring/prometheus.yml',*list((ROOT/'monitoring/grafana/provisioning').rglob('*.yaml')),*list((ROOT/'manifests').glob('*.yaml'))]:
            self.assertIsNotNone(yaml.safe_load_all(path.read_text()))
            self.assertTrue(list(yaml.safe_load_all(path.read_text())),str(path))

    def test_services(self):
        c=yaml.safe_load((ROOT/'compose.yaml').read_text())
        self.assertEqual(set(c['services']),{'k3s','dashboard','prometheus','grafana','portainer'})
        self.assertNotIn('6443',str(c['services']['k3s'].get('ports')))
        self.assertTrue(c['services']['k3s'].get('privileged'))
        self.assertEqual(c['services']['dashboard']['volumes'],['lab_kubeconfig:/secrets:ro'])

    def test_percent_validation_and_dns(self):
        source=ast.parse((ROOT/'app/cluster.py').read_text())
        funcs=[node for node in source.body if isinstance(node,ast.FunctionDef) and node.name=='nginx_conf']
        self.assertEqual(len(funcs),1)
        env={'ALLOWED_WEIGHTS':{0,10,25,50,75,90,100}}
        exec(compile(ast.Module(body=funcs,type_ignores=[]),'nginx_conf','exec'),env)
        f=env['nginx_conf']
        for pc in [0,10,25,50,75,90,100]:
            conf=f(pc)
            self.assertIn('upstream classroom_releases',conf)
            self.assertIn('listen 8080',conf)
            self.assertIn('kics-'+('blue' if pc==0 else 'green'),conf)
        self.assertNotIn('kics-green.',f(0))
        self.assertNotIn('kics-blue.',f(100))
        self.assertIn('weight=75',f(25))
        self.assertIn('weight=25',f(25))
        with self.assertRaises(ValueError):f(33)

    def test_grafana_panel_queries(self):
        d=json.loads((ROOT/'monitoring/grafana/dashboards/kics.json').read_text())
        self.assertGreaterEqual(len(d['panels']),5)
        for panel in d['panels']:
            self.assertEqual(panel['datasource']['uid'],'kics-prometheus')
            self.assertTrue(panel['targets'])

    def test_browser_no_auth_or_shell(self):
        ui=(ROOT/'app/static/index.html').read_text()
        self.assertIn('Send 100% to Blue',ui)
        self.assertIn('Switch 100% to Green',ui)
        self.assertIn('Send 24 Test Requests',ui)
        main=(ROOT/'app/main.py').read_text()
        self.assertNotIn('subprocess.',main)
        self.assertNotIn('eval(',main)
        self.assertIn("x_kics_lab:str|None",main)

if __name__=='__main__':unittest.main()
