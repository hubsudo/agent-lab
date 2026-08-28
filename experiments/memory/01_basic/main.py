from agent_lab.memory import InMemoryStore, MemoryItem


store = InMemoryStore()
store.add(MemoryItem(content="The user prefers concise explanations", kind="preference"))

for memory in store.list():
    print(f"[{memory.kind}] {memory.content}")
