import pytest
import os
from config import Config

def test_config_singleton():
    """Test that Config returns the same instance."""
    config1 = Config()
    config2 = Config()
    assert config1 is config2

def test_missing_api_key(monkeypatch):
    """Test that missing API key raises ValueError."""
    # Temporarily unset the environment variable
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    
    with pytest.raises(ValueError, match="Invalid or missing OPENAI_API_KEY"):
        Config()

def test_invalid_api_key(monkeypatch):
    """Test that an invalid API key raises ValueError."""
    # Set an invalid API key
    monkeypatch.setenv('OPENAI_API_KEY', 'short')
    
    with pytest.raises(ValueError, match="OpenAI API key appears to be invalid"):
        Config()

def test_valid_api_key(monkeypatch):
    """Test that a valid API key is accepted."""
    # Set a mock valid API key
    mock_key = 'sk_test_validapikeywithsufficientlength'
    monkeypatch.setenv('OPENAI_API_KEY', mock_key)
    
    config = Config()
    assert config.openai_key == mock_key
