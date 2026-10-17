from __future__ import annotations
import pytest
from core.level import Level

LEGEND = {"#":"floor", ".":"void", "S":"start", "G":"goal", "F":"fragile",
          "B":"bridge", "o":"soft_switch", "x":"heavy_switch", "Y":"split_switch"}

def make_level(grid=None, bridges=None, switches=None):
    return Level.from_dict({"id":1,"name":"Test","grid":grid or ["S"+"#"*18+"G"]+["#"*20]*19,
                           "legend":LEGEND,"bridges":bridges or [],"switches":switches or []})

@pytest.fixture
def floor():
    return make_level()
