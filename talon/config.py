import os
from typing import Any, Dict, List, Optional, Type, Tuple, Union
from pathlib import Path
import yaml

from pydantic import BaseModel, ConfigDict
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

class TransportConfig(BaseModel):
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    http2: bool = True

class RateLimitConfig(BaseModel):
    base_delay: float = 1.5
    jitter: float = 0.4
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    token_bucket_capacity: float = 10.0

class ProxyConfig(BaseModel):
    enabled: bool = False
    pool: List[str] = []
    rotation_strategy: str = "round_robin"
    rotate_every_n_requests: int = 5

class DnsConfig(BaseModel):
    enabled: bool = True
    resolvers: List[str] = ["8.8.8.8", "1.1.1.1"]
    record_types: List[str] = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

class CollectorsConfig(BaseModel):
    dns: DnsConfig = DnsConfig()
    whois_enabled: bool = True
    certs_enabled: bool = True
    archive_enabled: bool = True
    archive_limit: int = 100
    shodan_enabled: bool = False
    shodan_api_key: str = ""
    github_enabled: bool = False
    github_api_key: str = ""
    github_dorks: List[str] = ["password", "secret", "api_key", "private_key"]

class StorageConfig(BaseModel):
    db_path: str = "talon.db"
    export_formats: List[str] = ["json", "csv", "html"]

class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = "talon.log"

def deep_merge(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

class TalonConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TALON_",
        env_nested_delimiter="__",
        extra="ignore"
    )

    transport: TransportConfig = TransportConfig()
    rate_limiting: RateLimitConfig = RateLimitConfig()
    proxy: ProxyConfig = ProxyConfig()
    collectors: CollectorsConfig = CollectorsConfig()
    storage: StorageConfig = StorageConfig()
    logging: LoggingConfig = LoggingConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (env_settings, init_settings)

    @classmethod
    def load_config(cls, config_path: Optional[str] = None, **overrides) -> "TalonConfig":
        merged_data = {}

        # Load default.yaml
        default_path = Path("config/default.yaml")
        if default_path.exists():
            with open(default_path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    merged_data = data

        # Load user-supplied YAML
        if config_path:
            user_path = Path(config_path)
            if user_path.exists():
                with open(user_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        deep_merge(merged_data, data)

        # Merge overrides (CLI)
        if overrides:
            deep_merge(merged_data, overrides)

        return cls(**merged_data)
