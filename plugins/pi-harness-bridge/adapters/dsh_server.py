"""JSON-RPC worker reusing the audited local DSH bridge. No credentials in stdout."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid

config = json.loads(os.environ['HARNESS_NATIVE_CONFIG'])
spec = importlib.util.spec_from_file_location('dsh_existing_bridge', config['bridgePath'])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
bridge = module.Bridge(state=Path.home() / '.pi' / 'agent' / 'dsh-bridge-requests')
client = bridge.client
write_lock = threading.Lock()
sid = None
selection = None
running = False
closing = threading.Event()
worker = None
last_seq = 0
generation = 0


def send(value):
    with write_lock:
        print(json.dumps(value, ensure_ascii=False), flush=True)


def event(value):
    send({'method': 'bridge/event', 'params': value})


def finish(text='', error=None, cancelled=False):
    global running
    running = False
    event({'type': 'bridge_finished', 'text': text, 'error': error, 'cancelled': cancelled})


def ensure():
    global sid, selection, last_seq
    if sid:
        return
    if selection is None:
        catalog = bridge.call('dsh_models', {})
        default = catalog.get('default')
        if not isinstance(default, dict):
            raise ValueError('DSH 缺少默认模型，请先显式选择 provider/modelId')
        selection = bridge.selection(default['provider'], default['model'], default.get('reasoningEffort'))
    result = bridge.call('dsh_create_session', {'cwd': os.getcwd(), 'provider': selection['provider'], 'model': selection['model'], **({'reasoning_effort': selection['reasoningEffort']} if selection.get('reasoningEffort') else {})})
    sid = result['session_id']
    last_seq = client.find(sid)['projections']['asOfSeq']


def poll(baseline, run_id):
    global last_seq
    deadline = time.monotonic() + config.get('taskTimeoutSeconds', 7200)
    try:
        while not closing.wait(1):
            if run_id != generation:
                return
            if time.monotonic() > deadline:
                bridge.call('dsh_cancel', {'session_id': sid})
                finish(error='DSH task deadline exceeded')
                return
            result = bridge.call('dsh_read', {'session_id': sid, 'max_messages': 100})
            if run_id != generation:
                return
            records = result.get('history', {}).get('records', [])
            # Keep full snapshots; final completion must be from a NEW turn/end after this prompt.
            event({'type': 'native_snapshot', 'adapter': 'dsh', 'snapshot': result})
            new_end = any(r.get('event', {}).get('seq', 0) > baseline and r.get('event', {}).get('type') == 'turn/end' for r in records)
            last_seq = result['as_of_seq']
            if not result.get('running') and new_end:
                errors = result.get('errors')
                reason = result.get('last_turn_reason')
                finish(result.get('assistant_text', ''), json.dumps(errors) if errors else None, isinstance(reason, dict) and reason.get('kind') in ('cancelled', 'aborted'))
                return
    except Exception as exc:
        if run_id != generation:
            return
        try:
            bridge.call('dsh_cancel', {'session_id': sid})
        except Exception:
            pass
        finish(error=str(exc))


def handle(method, params):
    global selection, running, worker, generation
    if method == 'get_state':
        status = bridge.call('dsh_status', {})
        return {'adapter': 'dsh', 'sessionId': sid, 'isStreaming': running, 'model': selection, 'connection': status, 'remote': client.find(sid) if sid else None, 'capabilities': {'resume': True, 'model': True, 'models': True, 'thinking': True}}
    if method == 'get_available_models':
        return bridge.call('dsh_models', {})
    if method == 'set_model':
        if running:
            raise ValueError('Session busy')
        chosen = bridge.selection(params['provider'], params['modelId'])
        if sid:
            client.rpc('session/selectModel', {'request': {'sessionId': sid, **chosen}})
            actual = client.find(sid).get('projections', {}).get('values', {}).get('modelSelection', {}).get('next')
            if actual != chosen:
                raise ValueError('DSH model readback mismatch')
        selection = chosen
        return {'selected': chosen, 'verified': bool(sid), 'effective': 'current-session' if sid else 'session-create'}
    if method == 'set_thinking_level':
        if running:
            raise ValueError('Session busy')
        ensure()
        chosen = bridge.selection(selection['provider'], selection['model'], params['level'])
        client.rpc('session/selectModel', {'request': {'sessionId': sid, **chosen}})
        if client.find(sid).get('projections', {}).get('values', {}).get('modelSelection', {}).get('next') != chosen:
            raise ValueError('DSH thinking readback mismatch')
        selection = chosen
        return chosen
    if method == 'prompt':
        if running:
            raise ValueError('Session busy')
        ensure()
        baseline = client.find(sid)['projections']['asOfSeq']
        result = bridge.call('dsh_send', {'session_id': sid, 'prompt': params['message'], 'request_id': str(uuid.uuid4())})
        if result['state'] != 'accepted':
            raise ValueError('DSH acceptance uncertain, not retried')
        running = True
        generation += 1
        worker = threading.Thread(target=poll, args=(baseline, generation), daemon=True)
        worker.start()
        return {'disposition': 'started'}
    if method == 'abort':
        if sid and running:
            bridge.call('dsh_cancel', {'session_id': sid})
            # Do not kill the shared GUI server. Wait for the owned session to stop.
            for _ in range(40):
                if not client.find(sid).get('running'):
                    generation += 1
                    finish(cancelled=True)
                    return {}
                time.sleep(0.2)
            raise ValueError('DSH cancel not confirmed; inspect remote session')
        return {}
    raise ValueError('Unsupported DSH command: ' + method)


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
try:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = handle(request['method'], request.get('params', {}))
            send({'id': request['id'], 'result': result})
        except Exception as exc:
            send({'id': request.get('id'), 'error': {'code': -32000, 'message': str(exc)}})
finally:
    closing.set()
    if sid and running:
        try:
            bridge.call('dsh_cancel', {'session_id': sid})
        except Exception:
            pass
