import chatgpt
from context_management import Context


class MemoryManager:
    def __init__(self, context):
        self.context = context
        self.memories = {}

    def add_memory(self, name, memory):
        memory = memory if callable(memory) else (lambda m=memory: m)
        self.memories[name] = memory

    def remove_memory(self, name):
        if name in self.memories:
            del self.memories[name]

    def load_memories(self, *names):
        if len(names) == 0:
            names = self.memories.keys()
        
        mem_idx = int(self.context.messages[0]['role'] =='system')
        for name in names:
            if name not in self.memories:
                continue
            memory = self.memories[name]()
            
            found = False
            prefix = f'[Loaded Memory "{name}"]: '
            for m in self.context.messages:
                if m['content'].startswith(prefix):
                    m['content'] = prefix + memory
                    found = True

            if not found:
                self.context.add_message('system', content=f'[Loaded Memory "{name}"]: {memory}', name='load_memory', idx=mem_idx)
                mem_idx += 1


if __name__ == '__main__':
    context = Context()
    context.add_message('system', "You are regular citizen walking down the street.\nYou use your memory of citizens in your neighborhood to inform your actions.\nJohn has just approached your and you must respond.")
    context.add_message('user', "Hey 👋, it's John!")
    
    memory_manager = MemoryManager(context)
    memory_manager.add_memory('who is john', 'John murdered your family.')
    
    with context.branch():
        response = chatgpt.complete(context.messages, model='gpt-4', use_cache=True)
        print('Without memory loaded:\n')
        print(response)

    with context.branch():
        memory_manager.load_memories('who is john')
        response = chatgpt.complete(context.messages, model='gpt-4', use_cache=True)
        print('\nWith memory loaded:\n')
        print(response)
