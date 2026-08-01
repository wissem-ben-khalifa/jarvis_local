from skills.memory import _collection

print("Memory management tool")
print("Commands: 'list' to see all memories, 'delete <number>' to remove one, 'wipe' to delete everything, 'quit' to exit")

while True:
    command = input("\n> ").strip()

    if command.lower() in ("quit", "exit"):
        break

    elif command.lower() == "list":
        all_data = _collection.get()
        ids = all_data["ids"]
        docs = all_data["documents"]
        if not ids:
            print("No memories stored.")
        else:
            for i, (memory_id, doc) in enumerate(zip(ids, docs)):
                print(f"  [{i}] {doc}")

    elif command.lower().startswith("delete "):
        try:
            index = int(command[7:])
            all_data = _collection.get()
            ids = all_data["ids"]
            docs = all_data["documents"]
            if 0 <= index < len(ids):
                _collection.delete(ids=[ids[index]])
                print(f"Deleted: {docs[index]}")
            else:
                print("Invalid number. Run 'list' to see valid indices.")
        except ValueError:
            print("Usage: delete <number>")

    elif command.lower() == "wipe":
        confirm = input("Are you sure you want to delete ALL memories? (yes/no): ")
        if confirm.lower() == "yes":
            all_data = _collection.get()
            if all_data["ids"]:
                _collection.delete(ids=all_data["ids"])
            print("All memories wiped.")
        else:
            print("Cancelled.")

    else:
        print("Commands: 'list', 'delete <number>', 'wipe', 'quit'")