import openai
import os
from chatgpt_base import ChatGPT
from pprint import pprint
import sys

### Start conversation loop ###
welcome_message = '''
Starting conversation...
Type 'end' to submit your query.
Type 'reset' to start a new conversation.
Type 'exit' to terminate the conversation.
'''

print(welcome_message)
														
asst = ChatGPT()

while True:
    print('*** User ***', end='\n\n')
    query_lines = []
    while True:
        line = input()
        cmd = line.strip().lower()
        if query_lines and cmd == 'end':
            break
        elif not query_lines and cmd.split(' ')[0] in ['exit', 'reset', 'context', 'prune', 'model']:
            if cmd == 'exit':
                print('Exiting...')
                sys.exit()
                
            elif cmd == 'reset':
                print('Resetting conversation...')
                print(welcome_message)
                asst.setup_gpt()
                continue
                
            elif cmd == 'model 3.5':
                print('Resetting switching to gpt-3.5...')
                asst.model = 'gpt-3.5-turbo'
                print(welcome_message)
                asst.setup_gpt()
                continue
                
            elif cmd == 'model 4':
                print('Resetting conversation...')
                asst.model = 'gpt-4'
                print(welcome_message)
                asst.setup_gpt()
                continue
            
            elif cmd == 'context':
                print(f'Printing context ({str(len(asst.context))} messages)...')
                pprint(asst.context)
                continue
            
            elif cmd == 'prune recent':
                num_new_msgs = len(asst.context) - len(asst.base_context)
                if num_new_msgs >= 6:
                    start_to_keep = len(asst.base_context) + 4
                elif num_new_msgs >= 4:
                    start_to_keep = len(asst.base_context) + 2
                else:
                    start_to_keep = len(asst.base_context)
                print(f'Pruning conversation: keeping first {str(start_to_keep)} of {len(asst.context)} messages (pruning {str(len(asst.context)-start_to_keep)})...')
                asst.context = asst.context[:start_to_keep]
                continue
            
            elif cmd == 'prune':
                num_new_msgs = len(asst.context) - len(asst.base_context)
                if num_new_msgs >= 8:
                    start_to_keep = len(asst.base_context) + 4
                    end_to_keep = 2
                elif num_new_msgs >= 6:
                    start_to_keep = len(asst.base_context) + 2
                    end_to_keep = 2
                elif num_new_msgs > 2:
                    start_to_keep = len(asst.base_context) + 0
                    end_to_keep = 2
                else:
                    start_to_keep = len(asst.base_context) + 0
                    end_to_keep = 0
                print(f'Pruning conversation: keeping first {str(start_to_keep)} and last {str(end_to_keep)} of {len(asst.context)} messages (pruning {str(len(asst.context)-start_to_keep-end_to_keep)}, keeping {str(start_to_keep+end_to_keep)})...')
                if start_to_keep > 0 and end_to_keep > 0:
                    asst.context = asst.context[:start_to_keep] + asst.context[0-end_to_keep:]
                elif start_to_keep > 0:
                    asst.context = asst.context[:start_to_keep]
                elif end_to_keep > 0:
                    asst.context = asst.context[0-end_to_keep:]
                else:
                    self.context = []
                continue
            
            else:
                raise Exception('Uncaught command: ', cmd)
        else:
            query_lines.append(line)
            
    query = '\n'.join(query_lines)

    print('\n*** Assistant ***\n')
    response = asst.ask_stream_print(query)
    print('', end='\n\n')




