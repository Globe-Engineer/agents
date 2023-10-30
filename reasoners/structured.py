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


class StructuredReasoner(Reasoner):
    def __init__(self, system_prompt=None, model='gpt-4'):
        super().__init__(system_prompt=system_prompt, model=model)

    def parse_response_options(self):
        json_schema = {
            "name": "store_response_options",
            "description": "Stores a list of possible response options in memory to choose from later. E.g. ['attempt to explain mathematically', 'explain using an analogy', 'list resources to learn more']",
            "parameters": {
                "type": "object",
                "properties": {
                    "responses": {
                        "description": "The list of possible response options. Each element should be a short summary, not a full response.",
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["responses"]
            }
        }
        response = chatgpt.complete(messages=self.messages, model=self.model, functions=[json_schema], function_call={'name': 'store_response_options'})
        if response['role'] != 'function':
            raise Exception(f"Expected a function call, but got: {response['content']}")
        repsonse_options = response['args']['responses']
        self.add_message(response['role'], 'Stored response options:' + '\n'.join(repsonse_options), name=response['name'])
        return repsonse_options
        

    def choose(self, options):
        self.add_message('assistant', 
            '[Internal Monologue]: I need to record my choice as one of the following, '
            'by calling the choose() function with the corresponding choice number:\n' + 
            "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
        )
        json_schema = {
            "name": "choose",
            "description": "Chooses one of the options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "choice_index": {
                        "description": f"The index of the option you chose. An integer from 1 to {len(options)}",
                        "type": "integer",
                    }
                },
                "required": ["options"]
            }
        }
        response = chatgpt.complete(messages=self.messages, model=self.model, functions=[json_schema], function_call={'name': 'choose'})
        if response['role'] != 'function':
            raise Exception(f"Expected a function call, but got: {response['content']}")
        self.messages.pop() # remove the message that prompted the user to choose
        choice = response['args']['choice_index'] - 1
        self.add_message(response['role'], f'Chose option: {options}', name=response['name'])
        return choice


from colorama import Fore, Style
def printc(*args, color='reset', **kwargs):
    color_code = getattr(Fore, color.upper(), Fore.RESET)
    text = ' '.join(str(arg) for arg in args)
    print(color_code + text + Style.RESET_ALL, **kwargs)


if __name__ == '__main__':
    THINK_FIRST = True
    system_prompt = (
        "You use your internal monologue to reason before responding to the user. "
        "You try to maximize how funny your response is."
    )
    reasoner = StructuredReasoner(system_prompt=system_prompt, model='gpt-4')

    while True:
        message = input("\nUser: ")
        if message == "quit":
            break
        
        reasoner.add_message('user', message)

        if THINK_FIRST:
            thought = reasoner.internal_monologue("I should brainstorm some funny ways to respond.")
            printc('\n' + thought, color='blue')
        else:
            reasoner.add_message('assistant', '[Internal Monologue]: I should brainstorm a list of funny ways to respond.')
        options = reasoner.parse_response_options()
        printc('\nOptions:\n- ' + '\n- '.join(options), color='yellow')

        if THINK_FIRST:
            thought = reasoner.internal_monologue("I need to choose the funniest response, I can only choose one. My options are:\n" + '\n'.join(options))
            printc('\n' + thought, color='blue')
        else:
            reasoner.add_message('assistant', '[Internal Monologue]: I need to choose the funniest response')
        choice = reasoner.choose(options)
        printc('\nChose response: ' + options[choice], color='yellow')

        response = reasoner.external_dialogue(f"I'll respond to the user using the response I chose.")
        print('\n' + response)
