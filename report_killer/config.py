"""Configuration management for Report Killer."""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Configuration for the Report Killer agent."""
    
    api_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    model: str = "anthropic/claude-3.5-sonnet"
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    custom_prompt: str = ""
    documents_dir: str = "documents"
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file or environment."""
        config = cls()
        
        # Load from config file if it exists
        if config_path is None:
            config_path = Path("config.json")
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        # Override with environment variables
        if os.getenv("OPENAI_API_URL"):
            config.api_url = os.getenv("OPENAI_API_URL")
        if os.getenv("OPENAI_API_KEY"):
            config.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_MODEL"):
            config.model = os.getenv("OPENAI_MODEL")
        if os.getenv("HTTP_PROXY"):
            config.http_proxy = os.getenv("HTTP_PROXY")
        if os.getenv("HTTPS_PROXY"):
            config.https_proxy = os.getenv("HTTPS_PROXY")
        
        return config
    
    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = Path("config.json")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
    
    def get_proxies(self) -> Optional[dict]:
        """Get proxy configuration for requests."""
        if not self.http_proxy and not self.https_proxy:
            return None
        
        return {
            "http": self.http_proxy,
            "https": self.https_proxy,
        }
