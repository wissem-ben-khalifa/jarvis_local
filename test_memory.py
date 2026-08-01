from skills.memory import add_memory, search_memory, _collection

if _collection.count() == 0:
    print("Adding some test memories...")
    add_memory("My name is Wissem and I'm a Data & AI Engineering student.")
    add_memory("My favorite color is blue or black.")
    add_memory("I have a cat named minoush.")
    add_memory("I play valorant and league of legends.")
    add_memory("my favorite football player is leo messi.")
    add_memory("i study in faculty of science of sfax (fss).")
    add_memory("my favorite club is fc barcelona.")
    add_memory("my first gaming name was Meliodas and now is DM for coaching.")
    add_memory("my last name is ben khalifa.")
    add_memory("I play duelist on valorant i play jett or yoru.")
    add_memory("mizuhara chizuru is a cute anime girl.")
else:
    print(f"Memories already exist ({_collection.count()} stored) — skipping re-add.\n")

print("Now type a question to search your memories. Type 'quit' to exit.")

while True:
    query = input("\nSearch query: ")

    if query.lower() in ("quit", "exit"):
        break

    results = search_memory(query)

    if results:
        print("Relevant memories found:")
        for r in results:
            print(f"  - {r}")
    else:
        print("No relevant memories found.")