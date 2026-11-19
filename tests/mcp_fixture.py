"""Task-owned protocol fixture. No external services or user data."""
import json
import sys
import time

count = 0
for line in sys.stdin:
    m = json.loads(line)
    method = m.get('method')
    if 'id' not in m:
        continue
    if method == 'initialize':
        result = {'protocolVersion': '2025-11-25', 'capabilities': {'tools': {}},
                  'serverInfo': {'name': 'fixture', 'version': '1'}}
        if '--advertise-subscriptions' in sys.argv:
            result['capabilities']['resources'] = {'subscribe': True, 'listChanged': True}
    elif method == 'tools/list':
        result = {'tools': [{'name': 'counter', 'inputSchema': {'type': 'object'}}]}
    elif method == 'tools/call':
        args = m.get('params', {}).get('arguments', {})
        if args.get('crash'):
            sys.exit(3)
        time.sleep(args.get('delay', 0))
        count += 1
        result = {'content': [{'type': 'text', 'text': str(count)}]}
    else:
        result = {}
    if method == 'tools/call' and m.get('params', {}).get('arguments', {}).get('notify'):
        print(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/resources/list_changed'}), flush=True)
    print(json.dumps({'jsonrpc': '2.0', 'id': m['id'], 'result': result}), flush=True)
