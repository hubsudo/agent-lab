from agent_lab.memory import InMemoryStore, MemoryService


service = MemoryService(InMemoryStore())
service.remember(
    "The user prefers concise explanations",
    type="preference",
    source="conversation",
)

for memory in service.recall():
    print(f"[{memory.type}] {memory.content}")
