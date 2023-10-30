# Globe Agent Frameworks

This repo is a collection of useful LLM prompting/programming techniques that we've empirically found to be very useful.
All the examples use the OpenAI ChatGPT API using a [custom wrapper](https://github.com/Globe-Knowledge-Solutions/chatgpt-wrapper) that you can install with:

```bash
pip install chatgpt-wrapper
```

---
***RANT:***

We made this because open source LLM agent programming frameworks are becoming absurdly complicated and over-abstracted.
Libraries seem to be designed with virality as the primary objective rather than functionality, so they are extremely feature dense and bloated.
They are so abstracted away from the actual prompts being sent to LLMs that you can't possibly optimize for your usecase.

---

This repo is NOT a library in the sense that you can install it and use it via an API. Instead, we distill the most useful ideas we've found into minimal reproducable code examples that showcase useful concepts in the space of agent programming.

The goal is to encourage **forking** and **copy-pasting** of both code and ideas.

If you find this code useful or interesting, tag @ivan_yevenko and/or @sincethestudy on twitter and share your agent code. You should also join our [discord](https://discord.gg/79WH83sS3M) to share what you're working on. We run AI agent hackathons like [this one](https://colab.research.google.com/drive/1qxemv5_hCLxNu5NJUG4NuwE5_2Kh365Z?usp=sharing&authuser=1#scrollTo=wpiW9JIhoXpL) and discord is the best way to find out about them.

## Reasoners
In the `reasoners/` folder, we introduce the concepts of internal monologue, objective-oriented programming and structured outputs. It lets us write code that looks like this:

```python
reasoner.set_objective("do some task")
while not reasoner.objective_complete:
    thought = reasoner.internal_monlogue("I need to come up with a plan")
    plan = reasoner.extract_info("Here is my plan written in list form:\n{plan}", List[str])
    for step in plan:
        execute_step(step)
    reasoner.evaluate_objective()
```

## Context Management
The `context_management/` folder shows some examples of more advanced context management for LLMs

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

## Code Generation
Code generation is the new function calling. Check out the `code_gen/` folder for an example of function generation. We'll be adding to this folder over time.