import re
import json
from typing import Any, Dict
from datetime import datetime, timezone
from faker import Faker


class GrokPatternGenerator:
    """Generates data for grok pattern placeholders and timestamps"""
    
    # Predefined product categories
    PRODUCT_CATEGORIES = [
        'Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors',
        'Books', 'Toys & Games', 'Beauty & Personal Care', 'Food & Beverages',
        'Furniture', 'Office Supplies', 'Automotive', 'Pet Supplies',
        'Health & Wellness', 'Jewelry', 'Tools & Hardware', 'Music & Media'
    ]
    
    # Common grok patterns and their corresponding data generators
    PATTERN_GENERATORS = {
        'IP': lambda faker: faker.ipv4(),
        'HOSTNAME': lambda faker: faker.hostname(),
        'USERNAME': lambda faker: faker.user_name(),
        'INT': lambda faker: str(faker.random_int(min=0, max=65535)),
        'NUMBER': lambda faker: str(faker.random.uniform(0, 1000)),
        'WORD': lambda faker: faker.word(),
        'DATA': lambda faker: faker.sentence(),
        'GREEDYDATA': lambda faker: faker.text(max_nb_chars=100),
        'QUOTEDSTRING': lambda faker: f'"{faker.sentence()}"',
        'UUID': lambda faker: faker.uuid4(),
        'EMAIL': lambda faker: faker.email(),
        'URL': lambda faker: faker.url(),
        'PATH': lambda faker: faker.file_path(),
        'BASE10NUM': lambda faker: str(faker.random_int(0, 999999)),
        'BASE16NUM': lambda faker: hex(faker.random_int(0, 65535)),
        'POSINT': lambda faker: str(faker.random_int(min=1, max=65535)),
        'NONNEGINT': lambda faker: str(faker.random_int(min=0, max=65535)),
        'HEX': lambda faker: hex(faker.random_int(0, 255))[2:],
        'HTTPSTATUS': lambda faker: str(faker.random_element([200, 202, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503])),
        'HTTPERROR': lambda faker: str(faker.random_element([400, 401, 403, 404, 500, 502, 503])),
        'HTTPMETHOD': lambda faker: faker.random_element(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']),
        'TIMESTAMP_ISO8601': lambda faker: datetime.utcnow().isoformat() + 'Z',
        'TIMESTAMP_UNIX': lambda faker: str(int(datetime.utcnow().timestamp())),
        'DATESTAMP_RFC2822': lambda faker: datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000'),
        'SYSLOGDATE': lambda faker: datetime.utcnow().strftime('%b %d %H:%M:%S'),
        'DOLLAR': lambda faker: f"{faker.random.uniform(0.01, 9999.99):.2f}",
        'PRODUCT_NAME': lambda faker: faker.word().capitalize() + ' ' + faker.word().capitalize(),
        'PRODUCT_CATEGORY': lambda faker: faker.random_element(GrokPatternGenerator.PRODUCT_CATEGORIES),
    }
    
    def __init__(self, custom_patterns: Dict[str, str] = None):
        """
        Initialize the grok pattern generator
        
        Args:
            custom_patterns: Dictionary of custom pattern names to grok patterns
        """
        self.faker = Faker()
        self.custom_patterns = custom_patterns or {}
    
    def generate_from_template(self, template: str, index: int = None) -> str:
        """
        Generate a log line by replacing grok pattern placeholders
        
        Args:
            template: String containing %{PATTERN_NAME} placeholders
            index: Optional index number to replace %{INDEX} token (1-based)
        
        Returns:
            Generated log line with placeholders replaced
        """
        result = template
        
        # Replace INDEX placeholder first if provided
        if index is not None:
            result = result.replace('%{INDEX}', str(index))
        
        # Find all grok pattern placeholders: %{PATTERN_NAME}
        pattern_regex = r'%\{([A-Z_][A-Z0-9_]*)\}'
        matches = re.finditer(pattern_regex, result)
        
        for match in matches:
            pattern_name = match.group(1)
            replacement = self._get_pattern_value(pattern_name)
            result = result.replace(match.group(0), replacement, 1)
        
        return result
    
    def _get_pattern_value(self, pattern_name: str) -> str:
        """
        Get a generated value for a specific grok pattern
        
        Args:
            pattern_name: Name of the grok pattern (e.g., 'IP', 'HOSTNAME')
        
        Returns:
            Generated value as string
        """
        if pattern_name in self.PATTERN_GENERATORS:
            return self.PATTERN_GENERATORS[pattern_name](self.faker)
        elif pattern_name in self.custom_patterns:
            # Recursively process custom patterns
            custom_template = self.custom_patterns[pattern_name]
            return self.generate_from_template(custom_template)
        else:
            # If pattern is not found, return a placeholder with random data
            return self.faker.word()
    
    def generate_timestamp(self) -> str:
        """Generate current ISO8601 timestamp"""
        return datetime.utcnow().isoformat() + 'Z'
    
    def generate_int(self, min_val: int = 0, max_val: int = 65535) -> int:
        """Generate a random integer within range"""
        return self.faker.random_int(min=min_val, max=max_val)
