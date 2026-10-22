"""Pinned Qucs-S model catalog. See data/THIRD_PARTY.md for source and license."""
import json,gzip
from pathlib import Path
MODELS=json.loads(gzip.decompress((Path(__file__).parent/'data/qucs-devices.json.gz').read_bytes()))['models']

def device_model(kind,name):
    model=MODELS.get(name)
    if model is None or model['kind']!=kind:raise ValueError(f'Unknown {kind} library model: {name}')
    return model
