import re
import traceback

import chatgpt



def extract_markdown_code_blocks(s):
    return re.findall(r'```(?:python)?\n(.*?)\n```', s, re.DOTALL)


def generate_function(function_description, func_name, max_retries=3, debug=False):
    messages =[
        {'role': 'system', 'content': "Start by stating your assumptions and explaining your approach. Only write the `rev` function, no other code allowed. Include a single code block. Do not call `rev`."},
        {'role': 'user', 'content': f"Write a python function called `{func_name}`. Here's the description of the function:\n\n" + function_description}
    ]
    
    retries = 0
    while retries < max_retries:
        response = chatgpt.complete(messages=messages, model='gpt-4', use_cache=True)
        messages.append({'role': 'assistant', 'content': response})

        code = extract_markdown_code_blocks(response)
        if not code:
            messages.append({'role': 'user', 'content': "I couldn't find any executable code in your response, can you make sure to include a code block?"})
            retries += 1
            continue
        code = '\n\n'.join(code)
        if debug:
            print('#'*120)
            print(code)
            print('#'*120)

        namespace = {}
        try:
            exec(code, namespace)
        except Exception as e:
            error_message = traceback.format_exc()
            messages.append({'role': 'user', 'content': f"Error: {e}\n\nI got an error running your code. Here is the full error message:\n{error_message}\nCan you rewrite the entire code you wrote and try again?"})
            retries += 1
            continue
        break

    if retries >= max_retries:
        raise Exception("Failed to generate valid code after 3 retries")
    return namespace[func_name]


if __name__ == '__main__':
    ### Linked List Example Implementation ###
    class Node:
        def __init__(self, data=None):
            self.data = data
            self.next = None
            self.prev = None

        def __str__(self):
            return self.data

    node1 = Node('1')
    node2 = Node('2')
    node3 = Node('3')

    node1.next = node2
    node2.prev = node1
    node2.next = node3
    node3.prev = node2

    def print_list(node):
        while node is not None:
            print(node, end=" ")
            node = node.next
        print()
    ### Linked List Example Implementation ###

    print("Original List: ")
    print_list(node1)

    func = generate_function("This function reverses a linked list. The list will consist of nodes which have `next` and `prev` attributes. You will be given the head of the list. ", 'rev', debug=True)
    reversed_list = func(node1)

    print("Reversed List: ")
    print_list(reversed_list)
