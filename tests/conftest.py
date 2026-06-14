import sys
from pathlib import Path

# Allow `import tracks` etc. from scripts/ in tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
