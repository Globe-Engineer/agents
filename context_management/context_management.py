import chatgpt

class Context():
    def __init__(self, messages=None):
        self.messages = messages or []
        
    def add_message(self, role, content, name=None, idx=None):
        message = {'role': role, 'content': content}
        if name:
            message['name'] = name
        if idx is None:
            self.messages.append(message)
        else:
            self.messages.insert(idx, message)

    def clear(self):
        self.messages = []

    def branch(self) -> 'ContextBranch':
        return ContextBranch(self)


class ContextBranch(Context):
    def __init__(self, context: Context):
        self.context = context

    def __enter__(self):
        self.old_messages = self.context.messages
        self.context.messages = self.context.messages.copy()

    def __exit__(self, exc_type, exc_value, traceback):
        self.context.messages = self.old_messages


if __name__ == '__main__':
    context = Context()
    context.add_message('user', "What should I do with my life?")

    for sys_msg in [
        "You are a based twitter user. Your influences are Paul Graham, Peter Thiel, and Elon Musk.",
        "You are a typical engineering student. You are not too intelligent and mostly follow the herd.",
    ]:
        with context.branch():
            context.add_message('system', sys_msg, idx=0)
            response = chatgpt.complete(context.messages, model='gpt-4', use_cache=True)
        print(response)
        print('\n***\n')