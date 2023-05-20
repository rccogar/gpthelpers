import datetime
import openai
import os
import re
import json
import copy
import dbm

class ChatGPT:
    def __init__(self, model='gpt-4', api_key_path='~/.openai', caching=False, cache_fn='openai.cache'):
        self.api_key = None
        self.model = model
        self.knowledge_cutoff = '2021-09-01'
        self.caching = caching
        self.cache_fn = cache_fn

        # Load credentials
        api_key_path = os.path.expanduser(api_key_path)
        with open(api_key_path, 'r') as fi:
            self.api_key = str(fi.read()).strip()

        # Authenticate
        openai.api_key = self.api_key
        openai.Model.list()

        self.setup_gpt()

    def add_context(self, role, content):
        self.context.append({'role': role, 'content': content})

    def add_system_context(self, content):
        self.add_context('system', content)

    def add_user_context(self, content):
        self.add_context('user', content)

    def add_assistant_context(self, content):
        self.add_context('assistant', content)

    def condense(self, content):
        return re.sub('[\s]+', ' ', content)

    def add_base_assistant_context(self):
        self.add_system_context(self.condense(f'''
                You are ChatGPT, a large language model trained by OpenAI.
                Answer as concisely as possible.
                Knowledge cutoff: {self.knowledge_cutoff}
                Current date: {datetime.date.today().isoformat()}
            ''')
        )

    def setup_gpt(self):
        self.context = []
        self.history = []
        self.add_base_assistant_context()
        self.base_context = copy.deepcopy(self.context)

    def ask(self, query, reset=False, skip_cache=False, update_cache=False, **kwargs):
        if reset:
            self.context = copy.deepcopy(self.base_context)

        self.add_user_context(query)
        
        req = {'model': self.model, 'messages': self.context}
        req.update(kwargs)

        if self.caching and not skip_cache and req.get('temperature', None) == 0:
            request_key = json.dumps(req)
            result_from_cache = False
            with dbm.open(self.cache_fn, 'c') as cache_db:
                cached_js = cache_db.get(request_key, None)
            if update_cache or cached_js is None:
                #print('Cache miss:', request_key)
                resp = openai.ChatCompletion.create(**req)
                resp_js = json.dumps(resp)
                with dbm.open(self.cache_fn, 'c') as cache_db:
                    cache_db[request_key] = resp_js
                cached_js = resp_js
            else:
                result_from_cache = True
                #print('Cache hit:', request_key)
            resp = json.loads(cached_js)
            if result_from_cache:
                resp['result_from_cache'] = True
        else:
            #print('No Cache')
            resp = openai.ChatCompletion.create(**req)

        resp_text = resp['choices'][0]['message']['content']
        
        self.history.append({'request': req, 'response': resp})
        self.add_assistant_context(resp_text)
        
        return resp_text

    def ask_print(self, query, **kwargs):
        full_text = self.ask(query, **kwargs)
        print(full_text)
        with open('openai.log', 'a+') as fo:
            fo.write(str({'query': query, 'response': full_text}))
        return full_text

    def ask_stream(self, query, reset=False, **kwargs):
        if reset:
            self.context = copy.deepcopy(self.base_context)

        self.add_user_context(query)
        
        req = {'model': self.model, 'messages': self.context, 'stream': True}
        req.update(kwargs)
        resp = openai.ChatCompletion.create(**req)
        
        self.history.append({'input': req, 'output': []})
        self.add_assistant_context('')
        #try:
        for chunk in resp:
            new_text = chunk['choices'][0]['delta'].get('content', '')
            self.history[-1]['output'] += chunk
            self.context[-1]['content'] = self.context[-1]['content'] + new_text
            yield new_text
        #except KeyboardInterrupt:
        #    print('\n\nKeyboardInterrupt: terminating...')

    def ask_stream_print(self, query, **kwargs):
        full_text = ''
        try:
            for text_chunk in self.ask_stream(query, **kwargs):
                full_text += text_chunk
                print(text_chunk, end='')
        except KeyboardInterrupt:
            print('\n<Terminated>')
        print('')
        with open('openai.log', 'a+') as fo:
            fo.write(str({'query': query, 'response': full_text}))
        return full_text
                
    
if __name__ == '__main__':
    asst = ChatGPT(model='gpt-3.5-turbo')

    # Test recall
    query1 = 'Please tell me 5 interesting facts.'
    print(f'User: {query1}', end='\n\n')
    print(f'Assistant: ', end='')
    response1 = asst.ask_print(query1)
    print('')
    
    query2 = 'Please restate only the third fact exactly as it is stated above without surrounding quotation marks.'
    print(f'User: {query2}', end='\n\n')
    print(f'Assistant: ', end='')
    response2 = asst.ask_print(query2)
    print('')

    assert response2 in response1

    # Test Streaming
    query3 = 'Please tell me 5 more interesting facts.'
    print(f'User: {query3}', end='\n\n')
    print('Assistant: ', end='')
    asst.ask_stream_print(query3)
    print('')

    # Test caching
    asst = ChatGPT(model='gpt-4')
    query4 = 'Please tell me 5 interesting facts.'
    print('Query:', query4)

    start_time = datetime.datetime.now()
    response4_1 = asst.ask(query4, reset=True, temperature=0, update_cache=True)
    end_time = datetime.datetime.now()
    print('Response 1:', response4_1)
    print('-> Duration:', (end_time - start_time).total_seconds(), 'seconds')

    start_time = datetime.datetime.now()
    response4_2 = asst.ask(query4, reset=True, temperature=0)
    end_time = datetime.datetime.now()
    print('Response 2:', response4_2)
    print('-> Duration:', (end_time - start_time).total_seconds(), 'seconds')
    
    print(response4_1[:10] + '___' + response4_1[-10:])
    print(response4_2[:10] + '___' + response4_2[-10:])
    assert response4_1 == response4_2
