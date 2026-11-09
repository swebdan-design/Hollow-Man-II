import sys, os, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'assets', 'gba'))
from PIL import Image
name = sys.argv[1]
mod = importlib.import_module(name)
keys = list(mod.T)
cols = 10
sheet = Image.new('RGB', (cols * 18, ((len(keys) + cols - 1) // cols) * 18), (255, 0, 255))
for i, k in enumerate(keys):
    sheet.paste(mod.T[k]().im, ((i % cols) * 18, (i // cols) * 18))
sheet.resize((sheet.size[0] * 4, sheet.size[1] * 4), Image.NEAREST).save(sys.argv[2])
print(len(keys), 'tiles:', ''.join(keys))
