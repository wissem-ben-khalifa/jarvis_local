import sounddevice as sd

print("=== All audio devices ===")
print(sd.query_devices())

print("\n=== Current defaults ===")
print("Default input device:", sd.default.device[0], "-", sd.query_devices(sd.default.device[0])["name"])
print("Default output device:", sd.default.device[1], "-", sd.query_devices(sd.default.device[1])["name"])