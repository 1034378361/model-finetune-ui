# AGENTS.md

Guidelines for AI agents working in this repository.

## Project Overview

**Model Finetune UI** - A Streamlit-based web application for water quality model fine-tuning and data processing. Supports CSV-to-encrypted-BIN conversion (encryption mode) and BIN-to-CSV extraction (decryption mode).

## Build/Lint/Test Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev
```

### Running the Application
```bash
# Recommended: Use project script
uv run model-finetune-ui

# Alternative: Direct streamlit
uv run streamlit run src/model_finetune_ui/app.py --server.port 8501

# Using run.py
uv run python run.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/unit/test_validator.py

# Run single test function
uv run pytest tests/unit/test_validator.py::TestDataValidator::test_init

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov

# Run specific test directory
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### Linting & Formatting
```bash
# Format code with Black
uv run black .

# Lint with Ruff
uv run ruff check .

# Auto-fix Ruff issues
uv run ruff check . --fix

# Type checking
uv run mypy .
```

### Generate Sample Data
```bash
uv run generate-sample-data
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local imports
- Use absolute imports from `src.model_finetune_ui` package
- Relative imports (`.utils`, `.core`) within the package are acceptable
- Unused imports in `__init__.py` are allowed (F401 ignored)

```python
# Correct order
import logging
import os
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.model_finetune_ui.core.processor import ModelProcessor
from .utils.validator import DataValidator
```

### Formatting
- **Line length**: 88 characters (Black default)
- **Python version**: 3.10+ (use modern type hints)
- **String quotes**: Single quotes preferred (`skip-string-normalization = true`)
- **Indentation**: 4 spaces

### Type Hints
- **Required** for all function signatures
- Use `dict[str, Any]` not `Dict[str, Any]` (Python 3.10+)
- Use `list[str]` not `List[str]`
- Use `X | None` not `Optional[X]`
- Return type annotations are mandatory

```python
def process_data(
    self, processed_data: dict[str, pd.DataFrame], model_type: int
) -> dict[str, Any] | None:
```

### Naming Conventions
- **Classes**: PascalCase (`ModelProcessor`, `DataValidator`)
- **Functions/Methods**: snake_case (`process_user_data`, `validate_data_format`)
- **Constants**: UPPER_SNAKE_CASE (`WATER_QUALITY_PARAMS`, `MAX_FILE_SIZE_MB`)
- **Private methods**: Leading underscore (`_validate_coefficient_matrices`)
- **Module files**: snake_case (`file_handler.py`, `template_generator.py`)

### Error Handling
- Use try/except with specific exception types when possible
- Always log errors with `logger.error()`
- Return `None` or `False` on failure, not exceptions (for validation methods)
- Include context in error messages

```python
try:
    result = self.processor.process_user_data(data, model_type)
except ValueError as e:
    logger.error(f"Processing failed: {str(e)}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {traceback.format_exc()}")
    return None
```

### Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log levels: `info` for success, `warning` for non-critical issues, `error` for failures
- Include relevant context in log messages

### Docstrings
- Use triple double-quotes
- Include Args, Returns sections for public methods
- Chinese comments are acceptable for domain-specific terms

```python
def validate_data_format(
    self, processed_data: dict[str, pd.DataFrame], model_type: int
) -> bool:
    """
    Validate data format.

    Args:
        processed_data: Dictionary of processed DataFrames
        model_type: Model type (0 or 1)

    Returns:
        Validation result
    """
```

### Class Structure
- Use `@classmethod` for factory methods and config accessors
- Use `@staticmethod` for utility functions without instance state
- Initialize instance attributes in `__init__`

## Project-Specific Patterns

### Water Quality Parameters
Standard 11 parameters (always in this order):
```python
["turbidity", "ss", "sd", "do", "codmn", "codcr", "chla", "tn", "tp", "chroma", "nh3n"]
```

### Feature Stations
26 features: `STZ1` through `STZ26`

### Model Types
- **Type 0**: Fine-tuning mode - requires `A` and `Range` files
- **Type 1**: Full modeling mode - requires `w`, `a`, `b`, `A`, and `Range` files

### DataFrame Conventions
- Row index: Water quality parameters or feature stations
- Column index: Feature stations, water parameters, or `min`/`max` for Range data
- All coefficient data should be numeric (float)

### Validation Thresholds
```python
MIN_SAMPLES_FOR_RANGE = 2
MAX_ZERO_RATIO = 0.9
MAX_NULL_RATIO = 0.5
COEFFICIENT_VALUE_RANGE = (-1000, 1000)
A_COEFFICIENT_RANGE = (-10, 10)
```

## Testing Patterns

### Fixtures (in conftest.py)
- `temp_dir`: Temporary directory for file operations
- `sample_water_params`: List of 11 water quality parameters
- `sample_feature_stations`: List of 26 STZ features
- `sample_coefficient_data`: Random coefficient DataFrame
- `sample_range_data`: Random range DataFrame with min/max
- `sample_a_coefficient`: Random A coefficient DataFrame

### Test Structure
```python
class TestClassName:
    """ClassName tests"""

    def test_method_name_scenario(self, fixture1, fixture2):
        """Test description"""
        # Arrange
        validator = DataValidator()
        
        # Act
        result = validator.method(data)
        
        # Assert
        assert result is True
```

## File Structure
```
src/model_finetune_ui/
├── app.py              # Main Streamlit application
├── config.py           # Configuration classes
├── core/
│   └── processor.py    # Data processing logic
└── utils/
    ├── decryption.py   # BIN file decryption
    ├── encryption.py   # Data encryption
    ├── file_handler.py # File I/O operations
    ├── template_generator.py
    ├── utils.py        # Shared utilities
    └── validator.py    # Data validation
```

## Git Workflow
- **main**: Stable releases (protected)
- **dev**: Development integration
- **feature/\***: New features
- **fix/\***: Bug fixes

Commit prefixes: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
