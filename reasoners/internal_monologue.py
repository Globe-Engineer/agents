import chatgpt


class Reasoner:
    def __init__(self, system_prompt=None, model='gpt-4'):
        self.model = model
        self.messages = []
        if system_prompt:
            self.messages.append({'role': 'system', 'content': system_prompt})
        self._is_internal = False

    def add_message(self, role, message, name=None):
        msg = {'role': role, 'content': message}
        if name:
            msg['name'] = name
        self.messages.append(msg)

    def external_dialogue(self, thought):
        # thought should describe how to respond, e.g. "I should respond to the user with the joke I came up with."
        self.add_message('assistant', '[Internal Monologue]: ' + thought)
        if self._is_internal:
            self._is_internal = False
            self.add_message('assistant', '[Internal Monologue]: I am now entering the external dialogue state. Everything I say there will be seen.')
            self.add_message('function', '[Exited Internal Monologue]', 'exit_monologue')
        response = chatgpt.complete(messages=self.messages, model=self.model)
        self.add_message('assistant', response)
        return response

    def internal_monologue(self, thought):
        if not self._is_internal:
            self._is_internal = True
            self.add_message('function', '[Entered Internal Monologue]', 'enter_monologue')
            self.add_message('assistant', "[Internal Monologue]: I am now in the internal monologue state. I won't be able to respond here, so I'll use this space to think, reflect, and plan.")
        self.add_message('assistant', '[Internal Monologue]: ' + thought)
        response = chatgpt.complete(messages=self.messages, model=self.model)
        response = response.replace('[Internal Monologue]: ', '')
        self.add_message('assistant', '[Internal Monologue]: ' + response)
        return response
    
from colorama import Fore, Style
def printc(*args, color='reset', **kwargs):
    color_code = getattr(Fore, color.upper(), Fore.RESET)
    text = ' '.join(str(arg) for arg in args)
    print(color_code + text + Style.RESET_ALL, **kwargs)


if __name__ == '__main__':
    system_prompt = (
        "You use your internal monologue to reason before responding to the user. "
        "You try to maximize how funny your response is."
    )
    reasoner = Reasoner(system_prompt=system_prompt, model='gpt-4')

    while True:
        message = input("\nUser: ")
        if message == "quit":
            break
        
        reasoner.add_message('user', message)

        thought = reasoner.internal_monologue("I should brainstorm some funny ways to respond.")
        printc('\n' + thought, color='blue')

        thought = reasoner.internal_monologue("I need to choose the funniest response. I can only choose one.")
        printc('\n' + thought, color='blue')

        response = reasoner.external_dialogue(f"I'll respond to the user using the response I chose.")
        print('\n' + response)
