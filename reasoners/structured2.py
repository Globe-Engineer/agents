from string import Formatter
from typing import Union, Type
from pydantic import BaseModel
from pydantic.main import create_model

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
        response = chatgpt.complete(messages=self.messages, model=self.model, use_cache=True)
        response = response.replace('[Internal Monologue]: ', '')
        self.add_message('assistant', '[Internal Monologue]: ' + response)
        return response


class StructuredReasoner(Reasoner):
    def __init__(self, system_prompt=None, model='gpt-4'):
        super().__init__(system_prompt, model)
    
    def extract_info(self, info_format, output_type: Union[BaseModel, Type]):
        """
        Extracts a piece of information in a specific format.
        This is done by using the function calling API to create a remember_{field_name} function and executing it.

        This function is useful when you want to extract the outcome of an internal monologue in a specific format. 
        It doesn't work so well for reasoning, so stick to the paradigm of internal monologue -> extract_info.
        The format string is a python format string that determines the format of the stored information.

        Parameters:
        info_format (str):
            The format string that determines the format of the stored information. 
        output_type (Union[BaseModel, Type]):
            The type of the field to be extracted. 
            If a pydantic BaseModel is provided, the field is extracted as a pydantic model.
            If a python Type is provided, the field is extracted as an instance of that type.

        Returns:
        The value of the field remembered by the reasoner

        Examples:
        --------
        Extracting an integer:
        >>> reasoner.add_message('user', "My name's Bill, I'm a 42 y.o. male from New York.")
        >>> reasoner.extract_info("The user is {age} years old.", int)
        25

        Extracting an enum:
        >>> from enum import Enum
        >>> reasoner.add_message("assistant", "I have logically deduced that I am happy.")
        >>> reasoner.extract_info("I am {state}", Enum('MentalState', 'HAPPY SAD'))
        "HAPPY"

        Extracting a pydantic model:
        >>> from pydantic import BaseModel
        >>> class Person(BaseModel):
        ...     name: str
        ...     twitter_handle: str
        ...     is_based: bool = False
        >>> reasoner.add_message("user", "Add Ivan Yevenko (@ivan_yevenko) to the database, he's pretty based.")
        >>> reasoner.extract_info("Added {person} to the database.", Person)
        Person(name='Ivan Yevenko', twitter_handle='@ivan_yevenko', is_based=True)
        """
        formatter = Formatter()
        parsed = [x for x in formatter.parse(info_format) if x[1] is not None]
        assert len(parsed) == 1, "Only one format field is allowed."

        _, field_name, _, _ = parsed[0]
        
        use_pydantic = type(output_type) is type and issubclass(output_type, BaseModel)
        if use_pydantic:
            params = output_type.model_json_schema()
        else:
            SingleFieldModel = create_model("SingleFieldModel", **{field_name: (output_type, ...)})
            params = SingleFieldModel.model_json_schema()

        func_name = "remember_" + field_name
        json_schema = {
            "name": func_name,
            "description": f"This function stores a piece of information in the format: '{info_format}'.",
            "parameters": params
        }

        response = chatgpt.complete(messages=self.messages, model=self.model, functions=[json_schema], function_call={'name': func_name}, use_cache=True)
        if response['role'] != 'function':
            raise Exception(f"Expected a function call, but got: {response['content']}")
        
        value = response['args']
        if use_pydantic:
            value = output_type.model_construct(value)
        else:
            try:
                value = value[field_name]
            except KeyError:
                # Generated JSON schema is sometimes incorrect, so we try to extract the field anyway
                value = value.popitem()[1]

        info = info_format.format(**{field_name: value})
        self.add_message('function', f'Stored information: "{info}"', name=response['name'])
        return value
    

from colorama import Fore, Style
def printc(*args, color='reset', **kwargs):
    color_code = getattr(Fore, color.upper(), Fore.RESET)
    text = ' '.join(str(arg) for arg in args)
    print(color_code + text + Style.RESET_ALL, **kwargs)


if __name__ == '__main__':
    from typing import List

    THINK_FIRST = False
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
            thought = reasoner.internal_monologue("I should brainstorm a list of funny ways to respond.")
            printc('\n' + thought, color='blue')
        else:
            reasoner.add_message('assistant', '[Internal Monologue]: I should brainstorm a list of funny ways to respond.')
        options = reasoner.extract_info("I came up with the following options:\n{options}", List[str])
        printc('\nOptions:\n- ' + '\n- '.join(options), color='yellow')

        if THINK_FIRST:
            thought = reasoner.internal_monologue("I need to choose the funniest response, I can only choose one. My options are:\n" + '\n'.join(options))
            printc('\n' + thought, color='blue')
        else:
            numbered_options = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
            reasoner.add_message('assistant', '[Internal Monologue]: I need to choose the funniest response. My options are:\n' + numbered_options)
        choice = reasoner.extract_info("I chose Option {choice_index}.", int)
        printc('\nChose response: ' + options[choice-1], color='yellow')

        response = reasoner.external_dialogue(f"I'll respond to the user using the response I chose.")
        print('\n' + response)
