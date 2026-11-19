import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
ROOT=next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
spec=importlib.util.spec_from_file_location('marketplace',ROOT/'scripts/marketplace.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
class MarketplaceTestsFixture:
    pass
