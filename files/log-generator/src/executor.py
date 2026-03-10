import threading
import time
import json
import random
from typing import Dict, Any, List
from datetime import datetime
from .generator import GrokPatternGenerator


class LogTemplateRunner:
    """Runs a single log template at specified frequency"""
    
    def __init__(self, template_config: Dict[str, Any]):
        """
        Initialize a log template runner
        
        Args:
            template_config: Configuration dictionary for a template
        """
        self.name = template_config['name']
        self.template = template_config['template']
        self.log_type = template_config['type']
        self.min_seconds = float(template_config['frequency']['min_seconds'])
        self.max_seconds = float(template_config['frequency']['max_seconds'])
        self.count = int(template_config.get('count', 1))
        self.custom_patterns = template_config.get('grok_patterns', {})
        self.generator = GrokPatternGenerator(custom_patterns=self.custom_patterns)
        self.stop_event = threading.Event()
        self.thread = None
    
    def start(self):
        """Start the template runner in a background thread"""
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the template runner"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run(self):
        """Main loop that generates and outputs logs"""
        while not self.stop_event.is_set():
            # Generate count number of log instances
            for index in range(1, self.count + 1):
                if self.stop_event.is_set():
                    break
                # Generate the log line
                log_line = self.generator.generate_from_template(self.template, index=index)
                
                # Format output based on type
                if self.log_type == 'json':
                    try:
                        # If template is meant to be JSON, ensure it's valid
                        output = json.loads(log_line)
                        print(json.dumps(output))
                    except json.JSONDecodeError:
                        # If it fails to parse, output as-is
                        print(log_line)
                else:
                    # Unstructured logs are printed as-is
                    print(log_line)
            
            # Wait for random interval between min and max
            wait_time = random.uniform(self.min_seconds, self.max_seconds)
            # Use an event wait so signals/stop requests interrupt the sleep
            self.stop_event.wait(wait_time)


class TemplateExecutor:
    """Manages multiple log templates running concurrently"""
    
    def __init__(self, templates: List[Dict[str, Any]]):
        """
        Initialize the template executor
        
        Args:
            templates: List of template configurations
        """
        self.templates = templates
        self.runners: List[LogTemplateRunner] = []
        self._initialize_runners()
    
    def _initialize_runners(self):
        """Create runner instances for each template"""
        for template_config in self.templates:
            runner = LogTemplateRunner(template_config)
            self.runners.append(runner)
    
    def start(self):
        """Start all template runners"""
        for runner in self.runners:
            runner.start()
    
    def stop(self):
        """Stop all template runners"""
        for runner in self.runners:
            runner.stop()
    
    def wait(self):
        """Wait for all threads to finish"""
        for runner in self.runners:
            if runner.thread:
                runner.thread.join()
