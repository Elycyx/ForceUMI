# Contributing to ForceUMI

Thank you for your interest in contributing to ForceUMI!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/forceumi.git
cd forceumi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in editable mode with all dependencies:
```bash
pip install -e .
```

4. Install development tools (optional):
```bash
pip install pytest pytest-cov  # For testing
```

## Running Tests

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_devices.py
```

Run with coverage:
```bash
pytest --cov=forceumi --cov-report=html
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and modular

## Adding New Features

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Implement your feature with tests

3. Ensure all tests pass:
```bash
pytest
```

4. Submit a pull request with:
   - Clear description of the changes
   - Any related issue numbers
   - Example usage if applicable

## Adding New Devices

To add support for a new device:

1. Create a new file in `forceumi/devices/`
2. Inherit from `BaseDevice`
3. Implement required methods: `connect()`, `disconnect()`, `read()`, `is_connected()`
4. Add tests in `tests/test_devices.py`
5. Update documentation

Example:
```python
from forceumi.devices.base import BaseDevice

class NewDevice(BaseDevice):
    def connect(self) -> bool:
        # Implementation
        pass
    
    def disconnect(self) -> bool:
        # Implementation
        pass
    
    def read(self):
        # Implementation
        pass
```

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

## Questions?

Feel free to open an issue for questions or discussions!

