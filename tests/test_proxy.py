"""End-to-end tests through real stdio; only processes created by this test."""
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROXY = ROOT / 'skills/codex-mcp-memory/scripts/idle_proxy.py'
FIXTURE = Path(__file__).with_name('mcp_fixture.py')


class Client:
    def __init__(self, mode='idle', fingerprint=None, advertise=False):
        self.temp = tempfile.TemporaryDirectory()
        profile = {'command': [sys.executable, '-u', str(FIXTURE)],
                   'lifecycle': mode, 'allowed_capabilities': ['tools'],
                   'fingerprints': {str(FIXTURE): fingerprint or hashlib.sha256(FIXTURE.read_bytes()).hexdigest()}}
        config = Path(self.temp.name) / 'profiles.json'
        if advertise:
            profile['command'].append('--advertise-subscriptions')
            profile['allowed_capabilities'].append('resources')
        config.write_text(json.dumps({'fixture': profile}), encoding='utf-8')
        self.p = subprocess.Popen([sys.executable, '-u', str(PROXY), '--profile', 'fixture',
                                   '--profiles-file', str(config), '--idle-seconds', '1'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        self.messages = queue.Queue()
        self.events = []
        self.seq = 0
        self.threads = [threading.Thread(target=self.read, daemon=True),
                        threading.Thread(target=self.errors, daemon=True)]
        for t in self.threads:
            t.start()

    def read(self):
        for line in self.p.stdout:
            message = json.loads(line)
            if 'method' not in message:
                self.messages.put(message)

    def errors(self):
        for line in self.p.stderr:
            self.events.append(line.strip())

    def send(self, method, params=None, notification=False):
        self.seq += 1
        msg = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notification:
            msg['id'] = self.seq
        self.p.stdin.write(json.dumps(msg) + '\n')
        self.p.stdin.flush()
        return self.seq

    def request(self, method, params=None):
        req = self.send(method, params)
        response = self.messages.get(timeout=12)
        assert response['id'] == req, response
        assert 'error' not in response, response
        return response['result']

    def init(self):
        self.request('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                                    'clientInfo': {'name': 'test', 'version': '1'}})
        self.send('notifications/initialized', notification=True)
        return self.request('tools/list')

    def wait(self, predicate, timeout=12):
        end = time.monotonic() + timeout
        while not predicate():
            if time.monotonic() > end:
                raise AssertionError(self.events)
            time.sleep(.03)

    def stops(self):
        return sum('stopped pid=' in e for e in self.events)

    def close(self):
        self.p.stdin.close()
        try:
            self.p.wait(timeout=20)
        finally:
            if self.p.poll() is None:
                self.p.kill()  # this exact test-owned proxy only
                self.p.wait(timeout=5)
            for t in self.threads:
                t.join(timeout=3)
            self.p.stdout.close()
            self.p.stderr.close()
            self.temp.cleanup()


class ProxyTests(unittest.TestCase):
    def client(self, **kwargs):
        c = Client(**kwargs)
        self.addCleanup(c.close)
        return c

    def test_repeated_catalog_sleep_wake_same_connection(self):
        c = self.client(mode='until-first-use')
        catalog = c.init()
        for i in range(3):
            c.wait(lambda: c.stops() == i + 1)
            self.assertIsNone(c.p.poll())
            self.assertEqual(c.request('tools/list'), catalog)
        self.assertEqual(sum('started pid=' in e for e in c.events), 4)

    def test_first_use_pins_and_preserves_state(self):
        c = self.client(mode='until-first-use')
        c.init()
        c.wait(lambda: c.stops() == 1)
        self.assertEqual(c.request('tools/call')['content'][0]['text'], '1')
        time.sleep(1.5)
        self.assertEqual(c.stops(), 1)
        self.assertEqual(c.request('tools/call')['content'][0]['text'], '2')

    def test_long_call_is_not_parked(self):
        c = self.client()
        c.init()
        self.assertEqual(c.request('tools/call', {'arguments': {'delay': 1.6}})['content'][0]['text'], '1')
        self.assertEqual(c.stops(), 0)
        c.wait(lambda: c.stops() == 1)

    def test_pings_do_not_prevent_sleep_or_wake_server(self):
        c = self.client()
        c.init()
        for _ in range(12):
            time.sleep(.15)
            self.assertEqual(c.request('ping'), {})
        c.wait(lambda: c.stops() == 1)
        starts = sum('started pid=' in e for e in c.events)
        c.request('ping')
        self.assertEqual(sum('started pid=' in e for e in c.events), starts)

    def test_changed_source_pins(self):
        c = self.client(fingerprint='0' * 64)
        c.init()
        time.sleep(1.5)
        self.assertEqual(c.stops(), 0)
        self.assertTrue(any('reviewed source changed' in e for e in c.events))

    def test_explicit_pinned_mode_never_sleeps(self):
        c = self.client(mode='pinned')
        c.init()
        time.sleep(1.5)
        self.assertEqual(c.stops(), 0)

    def test_unknown_operation_pins(self):
        c = self.client(mode='until-first-use')
        c.init()
        c.request('future/subscribe')
        time.sleep(1.5)
        self.assertEqual(c.stops(), 0)

    def test_advertised_subscription_is_not_actual_state(self):
        c = self.client(advertise=True)
        catalog = c.init()
        c.wait(lambda: c.stops() == 1)
        self.assertEqual(c.request('tools/list'), catalog)
        c.request('resources/subscribe', {'uri': 'fixture://only'})
        time.sleep(1.5)
        self.assertEqual(c.stops(), 1)

    def test_server_state_notification_pins(self):
        c = self.client()
        c.init()
        c.request('tools/call', {'arguments': {'notify': True}})
        time.sleep(1.5)
        self.assertEqual(c.stops(), 0)
        self.assertTrue(any('pinned: server notification' in e for e in c.events))

    def test_crash_does_not_replay_or_restart(self):
        c = self.client()
        c.init()
        c.send('tools/call', {'arguments': {'crash': True}})
        c.wait(lambda: c.p.poll() is not None)
        self.assertNotEqual(c.p.returncode, 0)
        self.assertEqual(sum('started pid=' in e for e in c.events), 1)

    def test_eof_reaps_owned_server(self):
        c = Client()
        c.init()
        c.close()
        self.assertEqual(c.p.returncode, 0)
        self.assertEqual(c.stops(), 1)


if __name__ == '__main__':
    unittest.main()
