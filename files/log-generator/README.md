# Log Generator

A Python application that generates templated logs in real-time based on YAML configuration. Supports both unstructured logs (like nginx) and structured JSON logs with grok pattern-based placeholder substitution.

## Features

- **Template-based log generation**: Define multiple log templates with grok patterns
- **Concurrent execution**: Each template runs independently at its specified frequency
- **Fake data generation**: Automatically generates realistic data for common patterns (IPs, hostnames, timestamps, etc.)
- **Flexible configuration**: YAML-based configuration with validation
- **Docker ready**: Includes Dockerfile and supports Kubernetes ConfigMap overrides
- **Multiple log types**: Support for both unstructured and JSON logs
- **Graceful shutdown**: Handles SIGINT/SIGTERM for clean shutdown

## Installation

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python -m src.main
```

The application will load the default configuration from `src/default_config.yaml`.

### Docker

Build the Docker image:
```bash
docker build -t log-generator .
```

Run the container:
```bash
docker run -it log-generator
```

### Kubernetes with ConfigMap

1. Create a ConfigMap with your configuration:
```bash
kubectl create configmap log-generator-config --from-file=config.yaml=your_config.yaml
```

2. Create a deployment that mounts the ConfigMap:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: log-generator
  template:
    metadata:
      labels:
        app: log-generator
    spec:
      containers:
      - name: log-generator
        image: log-generator:latest
        volumeMounts:
        - name: config
          mountPath: /etc/log-generator
      volumes:
      - name: config
        configMap:
          name: log-generator-config
```

## Configuration

Configuration is defined in YAML format. The application checks for config files in this order:

1. `/etc/log-generator/config.yaml` (Kubernetes ConfigMap mount)
2. `/app/config/config.yaml` (Docker volume mount)
3. Default bundled config at `src/default_config.yaml`

### Configuration Structure

```yaml
templates:
  - name: template_name
    type: unstructured|json
    template: "log template with %{PATTERN} placeholders"
    count: 1  # Optional: number of log instances per invocation (default: 1)
    frequency:
      min_seconds: 1
      max_seconds: 5
    grok_patterns:  # Optional custom patterns
      CUSTOM_PATTERN: "%{IP}:%{POSINT}"
```

### Special Tokens

In addition to grok patterns, templates support the following special tokens:

- **%{INDEX}**: Replaced with the current instance number (1-based) when using `count > 1`. For example, if count is 5, INDEX will be 1, 2, 3, 4, 5 respectively.

### Grok Patterns

The following grok patterns are built-in and automatically generate appropriate data:

- **Network**: `IP`, `HOSTNAME`, `EMAIL`, `URL`, `PATH`
- **User**: `USERNAME`, `EMAIL`
- **Numeric**: `INT`, `POSINT`, `NONNEGINT`, `NUMBER`, `BASE10NUM`, `BASE16NUM`, `HEX`
- **Text**: `WORD`, `DATA`, `GREEDYDATA`, `QUOTEDSTRING`
- **Identifiers**: `UUID`
- **Currency**: `DOLLAR` (random amount from $0.01 to $9999.99 with 2 decimals)
- **Products**: `PRODUCT_NAME` (random product name), `PRODUCT_CATEGORY` (category like Electronics, Clothing, etc.)
- **HTTP**: `HTTPMETHOD`, `HTTPSTATUS` (common status codes), `HTTPERROR` (error codes)
- **Timestamps**: 
  - `TIMESTAMP_ISO8601` (ISO 8601 format with Z suffix)
  - `TIMESTAMP_UNIX` (Unix timestamp)
  - `DATESTAMP_RFC2822` (RFC 2822 format)
  - `SYSLOGDATE` (Syslog format: "Mon DD HH:MM:SS")

### Example Configuration

```yaml
templates:
  - name: nginx_access_logs
    type: unstructured
    template: '%{IP} - %{USERNAME} [%{SYSLOGDATE}] "%{HTTPMETHOD} %{PATH} HTTP/1.1" %{HTTPERROR} %{INT} "%{URL}" "%{DATA}"'
    frequency:
      min_seconds: 1
      max_seconds: 3

  - name: application_json_logs
    type: json
    template: '{"timestamp": "%{TIMESTAMP_ISO8601}", "level": "INFO", "service": "%{WORD}", "user_id": "%{UUID}", "message": "%{GREEDYDATA}"}'
    frequency:
      min_seconds: 2
      max_seconds: 5

  - name: batch_processing_logs
    type: unstructured
    count: 5
    template: '[%{SYSLOGDATE}] Batch item %{INDEX}/5: Processing %{DATA}'
    frequency:
      min_seconds: 3
      max_seconds: 6

  - name: error_logs
    type: unstructured
    template: '[%{SYSLOGDATE}] ERROR in %{PATH}:%{POSINT} - %{GREEDYDATA}'
    frequency:
      min_seconds: 5
      max_seconds: 10
```

## How It Works

1. **Configuration Loading**: The application loads and validates the YAML configuration file
2. **Template Initialization**: Creates a runner for each template
3. **Concurrent Execution**: Each template runs in its own thread, generating logs at random intervals between min/max seconds
4. **Log Output**: All generated logs are written to stdout, allowing easy piping to log aggregation systems

## Validation

The application performs strict validation on startup and fails with clear error messages if configuration is invalid:

- Template names must be unique and non-empty
- Template text must be non-empty
- Type must be either "unstructured" or "json"
- Frequency must have both min_seconds and max_seconds
- min_seconds cannot be greater than max_seconds
- All numeric values must be valid numbers

## Output

All logs are written to standard output (stdout), one per line. JSON logs are validated and pretty-formatted when possible.

Example output:
```
192.168.1.45 - jennifer [Dec 29 14:23:45] "GET /api/users HTTP/1.1" 200 1024 "https://example.com" "Mozilla/5.0"
{"timestamp": "2025-12-29T14:23:46Z", "level": "INFO", "service": "payment", "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message": "Processed transaction successfully"}
[Dec 29 14:23:47] ERROR in /app/services/auth.py:156 - Connection timeout while validating user credentials
```

## Architecture

- **config.py**: Configuration loading and validation
- **generator.py**: Grok pattern replacement and fake data generation using Faker
- **executor.py**: Template runners and concurrent execution management
- **main.py**: Application entry point

## Troubleshooting

**Invalid YAML in config file**: Ensure your configuration file is valid YAML. Use tools like yamllint to validate.

**Template not generating expected data**: Check that all grok patterns are spelled correctly (case-sensitive). Common mistakes:
- `%{IP}` (correct) vs `%{ip}` (incorrect)
- Patterns must match exactly

**Logs not appearing**: Check stderr for validation errors. Ensure min/max frequency values are reasonable.

**Docker ConfigMap not found**: Verify the ConfigMap is created and mounted at `/etc/log-generator/config.yaml` in Kubernetes.