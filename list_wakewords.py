import openwakeword
from openwakeword.model import Model

# Downloads pretrained models on first run
openwakeword.utils.download_models()

model = Model()
print("Available wake word models:")
for name in model.models.keys():
    print(f"  - {name}")