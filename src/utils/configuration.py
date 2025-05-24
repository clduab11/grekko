"""
Centralised configuration core for Grekko.

- All settings classes (Pydantic v2+)
- Root GrekkoSettings
- get_settings(): singleton, precedence: env vars > .env.{env} > .env > YAML > defaults
- YAML merging via _load_yaml_config()
"""

import os
import glob
import yaml
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

# --- Settings Classes ---

class DatabaseSettings(BaseSettings):
    url: str = Field(default="sqlite:///grekko.db")
    pool_size: int = Field(default=5)
    timeout: int = Field(default=30)

    model_config = SettingsConfigDict(env_prefix="DB_")

class ExchangeSettings(BaseSettings):
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None
    uniswap_private_key: Optional[str] = None

    model_config = SettingsConfigDict(env_prefix="EXCHANGE_")

class LLMSettings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    cohere_api_key: Optional[str] = None
    cohere_model: str = "command-r"

    model_config = SettingsConfigDict(env_prefix="LLM_")

class RiskSettings(BaseSettings):
    position_limit: float = 100000.0
    max_drawdown: float = 0.2
    stop_loss_pct: float = 0.05

    model_config = SettingsConfigDict(env_prefix="RISK_")

class APISettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(env_prefix="API_")

class LoggingSettings(BaseSettings):
    level: str = "INFO"
    json_format: bool = False

    model_config = SettingsConfigDict(env_prefix="LOG_")

# --- Root Settings ---

class GrekkoSettings(BaseSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    exchange: ExchangeSettings = Field(default_factory=ExchangeSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    model_config = SettingsConfigDict(env_prefix="GREKKO_")

# --- YAML Loader Helper ---

def _load_yaml_config() -> Dict[str, Any]:
    """
    Merge all YAML files under config/ into a single dict.
    Later files override earlier ones.
    """
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
    config_data: Dict[str, Any] = {}
    if not os.path.isdir(config_dir):
        return config_data
    yaml_files = sorted(glob.glob(os.path.join(config_dir, "*.yaml")))
    for yfile in yaml_files:
        with open(yfile, "r") as f:
            data = yaml.safe_load(f) or {}
            config_data = _deep_merge_dicts(config_data, data)
    return config_data

def _deep_merge_dicts(a: Dict, b: Dict) -> Dict:
    """Recursively merge two dicts (b overrides a)."""
    result = dict(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge_dicts(result[k], v)
        else:
            result[k] = v
    return result

# --- Settings Loader ---

@lru_cache(maxsize=1)
def get_settings(env: Optional[str] = None) -> GrekkoSettings:
    """
    Load settings with precedence:
    1. Environment variables
    2. .env.{env} (if env provided)
    3. .env
    4. YAML files under config/
    5. Defaults
    """
    from pydantic_settings import SettingsConfigDict
    from pydantic_settings import BaseSettings as PydanticBaseSettings

    # 1. Load YAML config as base
    yaml_config = _load_yaml_config()

    # 2. Prepare .env files
    dotenv_paths = []
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if env:
        dotenv_env = os.path.join(root_dir, f".env.{env}")
        if os.path.isfile(dotenv_env):
            dotenv_paths.append(dotenv_env)
    dotenv_default = os.path.join(root_dir, ".env")
    if os.path.isfile(dotenv_default):
        dotenv_paths.append(dotenv_default)

    # 3. Compose settings, letting env vars and .env override YAML/defaults
    class _GrekkoSettings(GrekkoSettings):
        model_config = SettingsConfigDict(
            env_prefix="GREKKO_",
            env_file=dotenv_paths,
            env_file_encoding="utf-8"
        )

    # 4. Instantiate with YAML as base, env/.env override
    return _GrekkoSettings.model_validate(yaml_config or {})