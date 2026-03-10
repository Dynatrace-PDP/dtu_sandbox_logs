import yaml
from typing import Dict, List, Any
import sys


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class Config:
    """Handles loading and validating the log generator configuration"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.templates: List[Dict[str, Any]] = []
        self._load_and_validate()
    
    def _load_and_validate(self):
        """Load YAML config and validate structure"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigValidationError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in config file: {e}")
        
        if not self.config:
            raise ConfigValidationError("Config file is empty")
        
        if 'templates' not in self.config:
            raise ConfigValidationError("Config must contain 'templates' key")
        
        if not isinstance(self.config['templates'], list):
            raise ConfigValidationError("'templates' must be a list")
        
        if len(self.config['templates']) == 0:
            raise ConfigValidationError("'templates' list cannot be empty")
        
        self._validate_templates()
    
    def _validate_templates(self):
        """Validate each template in the configuration"""
        for idx, template in enumerate(self.config['templates']):
            self._validate_template(template, idx)
            self.templates.append(template)
    
    def _validate_template(self, template: Dict[str, Any], idx: int):
        """Validate a single template configuration"""
        prefix = f"Template {idx}"
        
        # Check required fields
        required_fields = ['name', 'template', 'type', 'frequency']
        for field in required_fields:
            if field not in template:
                raise ConfigValidationError(f"{prefix}: missing required field '{field}'")
        
        # Validate name
        if not isinstance(template['name'], str) or not template['name'].strip():
            raise ConfigValidationError(f"{prefix}: 'name' must be a non-empty string")
        
        # Validate template
        if not isinstance(template['template'], str) or not template['template'].strip():
            raise ConfigValidationError(f"{prefix}: 'template' must be a non-empty string")
        
        # Validate type
        valid_types = ['unstructured', 'json']
        if template['type'] not in valid_types:
            raise ConfigValidationError(
                f"{prefix}: 'type' must be one of {valid_types}, got '{template['type']}'"
            )
        
        # Validate frequency
        frequency = template.get('frequency', {})
        if not isinstance(frequency, dict):
            raise ConfigValidationError(f"{prefix}: 'frequency' must be a dictionary")
        
        if 'min_seconds' not in frequency or 'max_seconds' not in frequency:
            raise ConfigValidationError(
                f"{prefix}: 'frequency' must contain 'min_seconds' and 'max_seconds'"
            )
        
        try:
            min_sec = float(frequency['min_seconds'])
            max_sec = float(frequency['max_seconds'])
        except (ValueError, TypeError):
            raise ConfigValidationError(
                f"{prefix}: 'min_seconds' and 'max_seconds' must be numbers"
            )
        
        if min_sec < 0 or max_sec < 0:
            raise ConfigValidationError(
                f"{prefix}: 'min_seconds' and 'max_seconds' must be non-negative"
            )
        
        if min_sec > max_sec:
            raise ConfigValidationError(
                f"{prefix}: 'min_seconds' ({min_sec}) cannot be greater than "
                f"'max_seconds' ({max_sec})"
            )
        
        # Validate optional fields
        if 'grok_patterns' in template:
            if not isinstance(template['grok_patterns'], dict):
                raise ConfigValidationError(
                    f"{prefix}: 'grok_patterns' must be a dictionary mapping "
                    "pattern names to Grok patterns"
                )
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Return validated templates"""
        return self.templates
