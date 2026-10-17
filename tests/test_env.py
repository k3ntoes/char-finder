import fastapi
import uvicorn
import jinja2
import apscheduler
import httpx
import pytest

def test_imports():
    assert fastapi.__version__ is not None
    assert uvicorn.__version__ is not None
    assert jinja2.__version__ is not None
    assert apscheduler.__version__ is not None
    assert httpx.__version__ is not None
    assert pytest.__version__ is not None
