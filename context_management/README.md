# Context Management
One of the biggest problems with creating prompting abstractions is it's very easy to lose track of what's being put in to the language model's context. This is very bad! If you don't carefully manage what the LLM sees on a given completion, you'll quickly run out of context length, dilute the model's reasoning or confuse it to the point that it outputs complete garbage.

One piece of code we found ourselves writing over and over again was copying message histories, doing some operations, then restoring the old copied message history. This usually simple enough, but when you require more complex scoping, this is a PITA.

Our attempt at a pythonic solution to prompt scoping looks like this:

```python
context = Context()
with context.branch():
    context.add_message('user', 'Relevant context for tasks 1-3')
    result = do_task1()
    context.add_message('assistant', result)
    with context.branch():
        context.add_message('user', 'Relevant context for task 2')
        result = do_task2()
    # task2 relevant context not included
    result = do_task3()

# Context is empty outside the branch
```
One of the most powerful applications of context branching is *parallelization*. For example, for a given input, you might want 10 different LLM's with different system prompts to answer independently (and in parrallel), then compare the results. `context_management.py` gives a simpler (synchronous) example of this.

## Memory
The natural extension of context management is *memory*. It's often the case that you have a set of resuable information that is useful to give to the LLM. For example, you might want to store an explanation of some rules, a list of facts known about the user, semantic search results, a list of previous actions, etc...

We implemented this with a simple dictionary of memories, that you can selectively load. This looks like this:

```python
context = Context()

memory_manager = MemoryManager(context)
memory_manager.add_memory("date", lambda: datetime.datetime.now().strftime("%B %d, %Y"))
memory_manager.add_memory("user's birthday", "January 1st")
memory_manager.add_memory("gift recommendations", "A, B, C, D...")

with context.branch():
    memory_manager.load_memories("date", "user's birthday", "gift recommendations")
    plan = plan_birthday()
```

See `memory.py` for the implementation.