from src.utils.configuration import get_settings

def test_settings_load():
    assert get_settings()