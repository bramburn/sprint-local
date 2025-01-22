# Logging and Error Handling Guide

## Overview

This project uses a comprehensive logging and error handling system to ensure robust tracking, debugging, and auditing of workflow processes.

## Logging Configuration

### Logger Types

1. **Workflow Logger**: Tracks general workflow progress and key events
   - Location: `src/logging_config.py`
   - Log File: `logs/workflow.log`
   - Log Level: INFO

2. **Audit Logger**: Records critical actions for audit purposes
   - Location: `src/logging_config.py`
   - Log File: `logs/audit.log`
   - Log Level: INFO

3. **Error Logger**: Captures error events and exceptions
   - Location: `src/logging_config.py`
   - Log File: `logs/error.log`
   - Log Level: ERROR

## Custom Exceptions

### Available Exception Classes

1. **WorkflowBaseError**: Base exception for all workflow-related errors
   - Provides context and detailed error information

2. **WorkflowExecutionError**: Raised during workflow execution
   - Includes step and error type information

3. **FileAnalysisError**: Raised during file-related operations
   - Includes file path information

4. **ConfigurationError**: Raised for configuration-related issues
   - Includes configuration key information

## Logging Best Practices

### When to Log

- Log the start and end of critical workflow steps
- Log important state changes
- Log any unexpected conditions or potential issues
- Log user actions for audit purposes

### How to Log

```python
from src.logging_config import workflow_logger, audit_logger, error_logger
from src.exceptions import WorkflowExecutionError

# Workflow logging
workflow_logger.info("Starting data processing step")

# Audit logging
audit_logger.info("User action", extra={
    'user': 'username',
    'action': 'login',
    'details': 'Successful login'
})

# Error logging
try:
    # Some operation that might fail
    result = perform_critical_operation()
except Exception as e:
    error_logger.error(
        "Operation failed", 
        exc_info=True,  # Include traceback
        extra={
            'operation': 'perform_critical_operation',
            'error_details': str(e)
        }
    )
    raise WorkflowExecutionError(
        "Critical operation failed", 
        step="data_processing", 
        error_type="runtime_error"
    )
```

## Log File Management

- Log files are automatically rotated
- Maximum log file size: 10 MB
- Maximum backup files: 5
- Log files are stored in the `logs/` directory

## Troubleshooting

1. Check log files in the `logs/` directory
2. Look for detailed error messages and stack traces
3. Identify the specific step or component where the error occurred

## Performance Considerations

- Logging is designed to have minimal performance impact
- Use appropriate log levels to control verbosity
- Avoid logging sensitive information

## Security

- Log files are stored with restricted permissions
- Sensitive data should never be logged
- Use extra care when logging in production environments
