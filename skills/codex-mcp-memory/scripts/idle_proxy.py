"""Bounded idle lifecycle for explicitly reviewed local MCP profiles.

One event loop owns requests and parking; never replays tools/call. Not a
general MCP supervisor. Stateful capabilities disable parking for the session.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import uuid

class Proxy:
    def __init__(self, command, idle, profile=None):
        for stream in (sys.stdin, sys.stdout, sys.stderr):
            stream.reconfigure(encoding='utf-8')
        self.command, self.idle = command, idle
        self.profile = profile or {'name': 'fixture', 'allowed_capabilities': ['tools'], 'lifecycle': 'idle'}
        self.mode = self.profile.get('lifecycle', 'pinned')
        if self.mode not in ('idle', 'until-first-use', 'pinned'):
            raise ValueError('unknown lifecycle mode')
        self.log_path = None
        if self.profile.get('audit_dir'):
            audit = Path(self.profile['audit_dir'])
            audit.mkdir(parents=True, exist_ok=True)
            self.log_path = audit / (self.profile['name'] + '-' + str(os.getpid()) + '.jsonl')
        self.thread_id = None
        self.events = queue.Queue()
        self.child = None
        self.generation = 0
        self.pending, self.reverse_pending = set(), set()
        self.initial = self.initial_result = None
        self.discovery = None
        self.modern = False
        self.initialized = False
        self.boot_id = None
        self.boot_deadline = 0
        self.boot_started = 0
        self.stopping = False
        self.stop_started = 0
        self.terminate_sent = False
        self.stop_delayed = False
        self.deferred = []
        self.pinned = self.mode == 'pinned'
        self.last = time.monotonic()

    def reader(self, stream, source, generation):
        try:
            for raw in stream:
                self.events.put((source, generation, json.loads(raw)))
        except Exception:
            self.events.put(('invalid', generation, None))
        finally:
            if source == 'server':
                stream.close()  # The reader owns its stream; never close it under a read.
            self.events.put((source, generation, None))

    def log(self, event):
        try:
            print('mcp-idle-proxy[' + self.profile['name'] + ']: ' + event, file=sys.stderr, flush=True)
        except (OSError, ValueError):
            pass  # A closed diagnostics pipe must not interrupt child cleanup.
        if self.log_path:
            try:
                if self.log_path.exists() and self.log_path.stat().st_size > 65536:
                    self.log_path.replace(self.log_path.with_suffix('.previous.jsonl'))
                with self.log_path.open('a', encoding='utf-8') as output:
                    output.write(json.dumps({'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'proxy_pid': os.getpid(), 'parent_pid': os.getppid(),
                        'profile': self.profile['name'], 'thread_id': self.thread_id,
                        'event': event}, ensure_ascii=True) + '\n')
            except OSError:
                pass  # Diagnostics must not break a protocol connection.

    def emit(self, message):
        print(json.dumps(message, ensure_ascii=True), flush=True)

    def send(self, message):
        self.child.stdin.write(json.dumps(message, ensure_ascii=True) + '\n')
        self.child.stdin.flush()

    def start(self, waking=False):
        if self.child is not None or self.stopping:
            raise RuntimeError('previous child has not exited')
        self.generation += 1
        env = os.environ.copy()
        for key, value in self.profile.get('env_defaults', {}).items():
            if not env.get(key):
                env[key] = value
        # Recheck the reviewed source on every wake. A change pins the new child.
        for filename, expected in self.profile.get('fingerprints', {}).items():
            try:
                matches = hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
            except OSError:
                matches = False
            if not matches:
                self.pinned = True
                self.log('pinned: reviewed source changed')
        self.child = subprocess.Popen(self.command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=None, encoding='utf-8',
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            bufsize=1)
        threading.Thread(target=self.reader,
            args=(self.child.stdout, 'server', self.generation), daemon=True).start()
        self.log('started pid=' + str(self.child.pid))
        if waking:
            self.boot_id = 'proxy-init-' + uuid.uuid4().hex
            self.boot_started = time.monotonic()
            self.boot_deadline = self.boot_started + 30
            self.log('wake handshake started')
            self.send({**self.initial, 'id': self.boot_id})

    def begin_stop(self, reason):
        if self.child is None or self.stopping:
            return
        self.stopping = True
        self.stop_started = time.monotonic()
        self.terminate_sent = self.stop_delayed = False
        self.log('stop requested pid=' + str(self.child.pid) + ' reason=' + reason)
        try:
            self.child.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    def reject_deferred(self, message):
        queued, self.deferred = self.deferred, []
        for request in queued:
            if 'method' in request and 'id' in request:
                self.pending.discard(request['id'])
                self.emit({'jsonrpc': '2.0', 'id': request['id'],
                           'error': {'code': -32001, 'message': message}})

    def poll_stop(self):
        if not self.stopping:
            return
        child = self.child
        elapsed = time.monotonic() - self.stop_started
        if child.poll() is not None:
            self.log('stopped pid=' + str(child.pid) + ' exit=' + str(child.returncode) +
                     ' elapsed_ms=' + str(round(elapsed * 1000)))
            self.child = None  # Release ownership only AFTER confirmed process exit.
            self.stopping = False
            if self.deferred:
                self.start(waking=True)  # queued calls have never reached the old child
            return
        if elapsed >= 2 and not self.terminate_sent:
            self.terminate_sent = True
            self.log('terminate requested pid=' + str(child.pid))
            try:
                child.terminate()  # one asynchronous request on the exact owned handle
            except OSError:
                if child.poll() is None:
                    self.log('terminate failed pid=' + str(child.pid))
        if elapsed >= 15 and not self.stop_delayed:
            self.stop_delayed = True
            self.log('stop delayed: retaining child handle; no replacement started')
            self.reject_deferred('MCP child is still stopping; request was not sent. Try again later.')

    def stop(self):
        # Final EOF/error cleanup is bounded. It must never replace the primary error.
        self.deferred = []
        self.begin_stop('client-close')
        deadline = time.monotonic() + 17
        while self.stopping and time.monotonic() < deadline:
            self.poll_stop()
            if self.stopping:
                time.sleep(0.05)
        if self.stopping:
            self.log('cleanup deadline: owned child exit not confirmed')

    def client(self, message):
        method = message.get('method')
        # Catalog-only sessions have no reviewed user state yet. Pin BEFORE
        # forwarding any operation that could create state, even if it fails.
        catalog_methods = {'initialize', 'server/discover', 'ping', 'tools/list',
                           'resources/list', 'resources/templates/list', 'prompts/list',
                           'notifications/initialized', 'notifications/cancelled'}
        if self.mode == 'until-first-use' and method not in catalog_methods and method is not None:
            if not self.pinned:
                self.log('pinned: first non-catalog operation')
            self.pinned = True
        meta = message.get('params', {}).get('_meta', {})
        candidate = meta.get('threadId') if isinstance(meta, dict) else None
        if isinstance(candidate, str) and re.fullmatch(r'[0-9a-fA-F-]{36}', candidate):
            self.thread_id = candidate
        if method == 'initialize':
            if self.initial and not self.modern:
                raise RuntimeError('duplicate initialize')
            self.modern = False
            self.initial_result = None
            self.initialized = False
            self.initial = message
            # Dynamic roots and asynchronous task state are deliberately excluded.
            caps = message.get('params', {}).get('capabilities', {})
            self.log('client capabilities=' + ','.join(sorted(caps)))
            # Client support alone does not create a task. Server capabilities,
            # task requests/results and reverse requests guard asynchronous work.
            self.pinned |= 'roots' in caps and self.profile.get('pin_client_roots', True)
        elif method == 'server/discover':
            self.discovery = message
        elif method not in (None, 'ping', 'tools/list', 'tools/call',
                            'resources/list', 'resources/templates/list', 'resources/read',
                            'prompts/list', 'prompts/get',
                            'notifications/initialized', 'notifications/cancelled'):
            if not self.pinned:
                self.log('pinned: method=' + str(method))
            self.pinned = True
        if method == 'tools/call':
            self.log('tool request received')
        if method == 'notifications/cancelled':
            cancelled = message.get('params', {}).get('requestId')
            if any(r.get('id') == cancelled for r in self.deferred):
                self.deferred = [r for r in self.deferred if r.get('id') != cancelled]
                self.pending.discard(cancelled)
                return  # Never execute a call cancelled before it was forwarded.
        if message.get('params', {}).get('task') is not None:
            self.pinned = True
        if method == 'notifications/initialized':
            self.initialized = True
        if method is None:
            self.reverse_pending.discard(message.get('id'))
        elif 'id' in message:
            if method == 'ping' and self.initial_result:
                self.emit({'jsonrpc': '2.0', 'id': message['id'], 'result': {}})
                return
            self.pending.add(message['id'])
        if self.stopping:
            self.deferred.append(message)
            if self.stop_delayed:
                self.reject_deferred('MCP child is still stopping; request was not sent. Try again later.')
            return
        if self.child is None:
            self.start(waking=self.initial_result is not None)
        if self.boot_id:
            self.deferred.append(message)
        else:
            self.send(message)

    def server(self, message):
        if self.boot_id and message.get('id') == self.boot_id and 'method' not in message:
            if message.get('result') != self.initial_result:
                raise RuntimeError('server handshake changed; reconnect required')
            self.boot_id = None
            self.log('wake handshake completed elapsed_ms=' +
                     str(round((time.monotonic() - self.boot_started) * 1000)))
            if not self.modern:
                self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            queued, self.deferred = self.deferred, []
            for request in queued:
                self.send(request)
            return
        if 'method' not in message:
            self.pending.discard(message.get('id'))
            result = message.get('result', {})
            if isinstance(result, dict) and 'task' in result:
                self.pinned = True
            if (self.discovery and message.get('id') == self.discovery['id'] and
                isinstance(result, dict) and '2026-07-28' in result.get('supportedVersions', [])):
                self.initial = self.discovery
                self.modern = True
                self.initialized = True
                self.log('modern discovery negotiated')
            if self.initial and message.get('id') == self.initial['id'] and not self.initial_result:
                self.initial_result = message.get('result')
                caps = (self.initial_result or {}).get('capabilities', {})
                self.log('server capabilities=' + ','.join(sorted(caps)))
                self.pinned |= any(k not in self.profile['allowed_capabilities'] and
                                   not (k == 'experimental' and v == {}) for k, v in caps.items())
                if self.pinned:
                    self.log('pinned: capability or source guard')
        elif 'id' in message:
            self.reverse_pending.add(message['id'])
            self.pinned = True
        elif message.get('method') not in ('notifications/message', 'notifications/progress'):
            # Unknown server notifications can announce state we cannot restore.
            self.pinned = True
            self.log('pinned: server notification')
        self.emit(message)

    def run(self):
        threading.Thread(target=self.reader, args=(sys.stdin, 'client', 0), daemon=True).start()
        try:
            while True:
                try:
                    source, generation, message = self.events.get(timeout=0.1)
                except queue.Empty:
                    source = None
                if source:
                    if source != 'client' and generation != self.generation:
                        continue
                    if source == 'client' and message is None:
                        return
                    if source == 'invalid':
                        raise RuntimeError('invalid protocol stream')
                    if source == 'server' and message is None:
                        if self.child is not None and not self.stopping:
                            raise RuntimeError('child exited unexpectedly; no request replay')
                        continue
                    if source == 'server' and self.stopping:
                        continue  # No outstanding work belongs to a deliberately retired child.
                    # Transport health checks must not keep an unused server alive.
                    if not (source == 'client' and message.get('method') == 'ping' and self.initial_result):
                        self.last = time.monotonic()
                    (self.client if source == 'client' else self.server)(message)
                if self.boot_id and time.monotonic() > self.boot_deadline:
                    self.log('wake handshake timed out; queued requests not forwarded')
                    self.boot_id = None
                    self.reject_deferred('MCP startup timed out; request was not sent. Try again later.')
                    self.begin_stop('wake-timeout')
                self.poll_stop()
                if (self.child and not self.stopping and self.initialized and self.initial_result and
                    not self.pinned and not self.pending and not self.reverse_pending and
                    not self.boot_id and time.monotonic() - self.last >= self.idle):
                    self.begin_stop('idle')
        except Exception as error:
            # Log the original stage BEFORE cleanup; do not log request/command data.
            self.log('primary failure=' + type(error).__name__)
            raise
        finally:
            try:
                self.stop()
            except Exception as error:
                self.log('cleanup failure=' + type(error).__name__)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--profiles-file', type=Path, default=Path(__file__).with_name('mcp-idle-profiles.json'))
    parser.add_argument('--idle-seconds', type=float, default=180)
    args = parser.parse_args()
    if not 1 <= args.idle_seconds <= 3600:
        parser.error('idle-seconds must be 1..3600')
    profiles = json.loads(args.profiles_file.read_text(encoding='utf-8'))
    if args.profile not in profiles:
        parser.error('profile not found')
    profile = profiles[args.profile]
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', args.profile):
        parser.error('invalid profile name')
    if not isinstance(profile.get('command'), list) or not profile['command'] or not all(isinstance(x, str) for x in profile['command']):
        parser.error('profile needs a nonempty command array')
    if profile.get('lifecycle', 'pinned') != 'pinned' and not profile.get('fingerprints'):
        parser.error('sleep requires reviewed source fingerprints')
    if not isinstance(profile.get('allowed_capabilities'), list):
        parser.error('profile needs allowed_capabilities')
    profile['name'] = args.profile
    proxy = Proxy(profile['command'], args.idle_seconds, profile)
    try:
        proxy.run()
    except Exception as error:
        proxy.log(type(error).__name__ + ': connection closed without replay')
        sys.exit(1)
