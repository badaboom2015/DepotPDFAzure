import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class DeploymentTests(unittest.TestCase):
    def run_script(self, case):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'infra/terraform').mkdir(parents=True)
            (root / 'app').mkdir()
            (root / 'bin').mkdir()
            original = Path(__file__).resolve().parents[1] / 'scripts/deploy-azure.sh'
            shutil.copy2(original, root / 'scripts/deploy-azure.sh')
            terraform = root / 'bin/terraform'
            terraform.write_text('#!' + sys.executable + '\n' + '''import json,os,sys
args=sys.argv[1:]
with open(os.environ['CALLS'],'a') as f:f.write(' '.join(args)+'\\n')
if 'pull' in args:
    case=os.environ['CASE']
    if case=='error':raise SystemExit(1)
    if case=='empty':raise SystemExit(0)
    subscription='other' if case.startswith('mismatch') else 'target'
    resource_type='azurerm_container_registry' if case=='mismatch_without_group' else 'azurerm_resource_group'
    print(json.dumps({'resources':[{'type':resource_type,'instances':[{'attributes':{'id':'/subscriptions/'+subscription+'/resourceGroups/test'}}]}]}))
if 'output' in args:
    print('registry.azurecr.io' if 'acr_login_server' in args else 'https://app.example')
''')
            az = root / 'bin/az'
            az.write_text('#!/bin/sh\nexit 0\n')
            terraform.chmod(0o755)
            az.chmod(0o755)
            calls = root / 'calls'
            env = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'],
                       CASE=case, CALLS=str(calls))
            result = subprocess.run(['bash', str(root / 'scripts/deploy-azure.sh'), 'target'],
                                    env=env, capture_output=True, text=True, timeout=20)
            return result, calls.read_text(), (root / 'infra/terraform/deployment.auto.tfvars.json').exists()

    def test_fresh_empty_state_deploys(self):
        result, calls, configured = self.run_script('empty')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('apply', calls)
        self.assertTrue(configured)

    def test_matching_state_deploys(self):
        result, calls, configured = self.run_script('matching')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(configured)

    def test_wrong_subscription_stops_before_apply(self):
        result, calls, configured = self.run_script('mismatch')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('apply', calls)
        self.assertFalse(configured)

    def test_wrong_subscription_without_group_stops_before_apply(self):
        result, calls, configured = self.run_script('mismatch_without_group')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('apply', calls)
        self.assertFalse(configured)

    def test_state_read_failure_stops_before_apply(self):
        result, calls, configured = self.run_script('error')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('apply', calls)
        self.assertFalse(configured)
