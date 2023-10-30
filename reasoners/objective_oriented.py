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


class ObjectiveReasoner(Reasoner):
    def __init__(self, objective=None, system_prompt=None, model='gpt-4'):
        super().__init__(system_prompt=system_prompt, model=model)
        if objective is not None:
            self.set_objective(objective)
        self.objective_complete = False

    def set_objective(self, objective):
        self.objective = objective
        objective_prompt = f'Your current objective is to: {objective}'
        if self.messages and self.messages[0]['role'] == 'system':
            self.messages[0]['content'] = objective_prompt + self.messages[0]['content']
        else:
            self.messages.insert(0, {'role': 'system', 'content': objective_prompt})

    def evaluate_objective(self):
        assert self.objective is not None, "Can't evaluate objective, no objective set. Use set_objective() to set an objective before calling evaluate_objective()."
        json_schema = {
            "name": "set_objective_status",
            "description": "Sets the status of the objective by setting the objective_complete flag to True or False.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective_complete": {
                        "description": "The status of the objective. True for complete, False for incomplete.",
                        "type": "boolean",
                    }
                },
                "required": ["objective_complete"]
            }
        }
        response = chatgpt.complete(messages=self.messages, model=self.model, functions=[json_schema], function_call={'name': 'set_objective_status'})
        if response['role'] != 'function':
            raise Exception(f"Expected a function call, but got: {response['content']}")
        self.objective_complete = response['args']['objective_complete']
        self.add_message(response['role'], f'Set flag: OBJECTIVE_COMPLETE={str(self.objective_complete).upper()}', name=response['name'])


from colorama import Fore, Style
def printc(*args, color='reset', **kwargs):
    color_code = getattr(Fore, color.upper(), Fore.RESET)
    text = ' '.join(str(arg) for arg in args)
    print(color_code + text + Style.RESET_ALL, **kwargs)


if __name__ == '__main__':
    REFLECT = True
    system_prompt = (
        "You use your internal monologue to reason before responding to the user. "
        "You try to maximize how funny your response is."
    )
    objective = "Make the user laugh. The objective is complete when the user expreses laughter using 'haha' or 'lol', or similar."
    reasoner = ObjectiveReasoner(objective=objective, system_prompt=system_prompt, model='gpt-4')

    while True:
        message = input("\nUser: ")
        if message == "quit":
            break
        
        reasoner.add_message('user', message)

        if REFLECT:
            thought = reasoner.internal_monologue(f"My current objective is to: {objective}. I should reflect on my objective and evaluate my progress.")

        reasoner.evaluate_objective()
        if reasoner.objective_complete:
            printc('\nObjective complete!', color='green')
            break
        printc('\nObjective NOT complete.', color='red')

        thought = reasoner.internal_monologue("I should brainstorm some funny ways to respond.")
        printc('\n' + thought, color='blue')

        thought = reasoner.internal_monologue("I need to choose the funniest response. I can only choose one.")
        printc('\n' + thought, color='blue')

        response = reasoner.external_dialogue(f"I'll respond to the user using the response I chose.")
        print('\n' + response)
