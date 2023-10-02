from geosnap.io import get_gadm
import pytest

GADM_DOWN=False

@pytest.mark.skipif(GADM_DOWN, reason="GADM is down at the moment")
def test_get_gadm():
    dr = get_gadm(code="DOM")
    assert dr.shape == (1, 3)
