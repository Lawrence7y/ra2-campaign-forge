import threading

class Client:
    def __init__(self):
        self.seq = 10
        self.running = False
        self.selected = {'provider': 'mock', 'model': 'small'}
        self.text = ''
        self.error = False

    def find(self, sid):
        return {'sessionId': sid, 'running': self.running, 'projections': {'asOfSeq': self.seq, 'values': {'modelSelection': {'next': self.selected}}}}

    def rpc(self, method, args):
        if method == 'session/selectModel':
            self.selected = {k: v for k, v in args['request'].items() if k != 'sessionId'}
            return {'selected': self.selected}
        raise ValueError('Unknown mock RPC')

class Bridge:
    def __init__(self, state=None):
        self.client = Client()

    def selection(self, provider, model, effort=None):
        if provider in ('deepseek-official', 'deepseek-account'):
            raise ValueError('Forbidden provider')
        return {'provider': provider, 'model': model, **({'reasoningEffort': effort} if effort else {})}

    def call(self, name, args):
        c = self.client
        if name == 'dsh_status':
            return {'connected': True}
        if name == 'dsh_models':
            return {'default': {'provider': 'mock', 'model': 'small'}, 'groups': [{'id': 'mock', 'models': [{'id': 'small'}]}]}
        if name == 'dsh_create_session':
            c.selected = self.selection(args['provider'], args['model'], args.get('reasoning_effort'))
            return {'session_id': 'session_mock'}
        if name == 'dsh_send':
            c.running = True
            c.seq += 1
            c.text = 'DSH: ' + args['prompt']
            c.error = args['prompt'] == 'error'
            def done():
                c.running = False
                c.seq += 2
            threading.Timer(0.05, done).start()
            return {'state': 'accepted'}
        if name == 'dsh_read':
            return {'running': c.running, 'as_of_seq': c.seq, 'assistant_text': c.text, 'errors': ['mock error'] if c.error else [], 'last_turn_reason': {'kind': 'error' if c.error else 'completed'}, 'history': {'records': [{'event': {'seq': c.seq, 'type': 'turn/end'}}]}}
        if name == 'dsh_cancel':
            c.running = False
            c.seq += 1
            return {}
        raise ValueError('Unknown mock tool')
