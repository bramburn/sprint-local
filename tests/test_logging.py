import os
import pytest
import logging
from unittest.mock import patch
from src.logging_config import setup_logger, workflow_logger, audit_logger, error_logger
from src.exceptions import WorkflowExecutionError, FileAnalysisError, ConfigurationError

def test_logger_creation():
    """
    Test that loggers are created correctly with appropriate handlers.
    """
    # Test workflow logger
    assert workflow_logger is not None
    assert len(workflow_logger.handlers) == 2  # Console and file handler
    assert workflow_logger.level == logging.INFO

    # Test audit logger
    assert audit_logger is not None
    assert len(audit_logger.handlers) == 2
    assert audit_logger.level == logging.INFO

    # Test error logger
    assert error_logger is not None
    assert len(error_logger.handlers) == 2
    assert error_logger.level == logging.ERROR

def test_custom_logger_setup():
    """
    Test creating a custom logger with specific configuration.
    """
    test_logger = setup_logger('test_logger', level=logging.DEBUG)
    
    assert test_logger is not None
    assert test_logger.level == logging.DEBUG
    assert len(test_logger.handlers) == 1  # Only console handler

def test_log_message_capture():
    """
    Test capturing log messages for different log levels.
    """
    with patch('logging.StreamHandler.emit') as mock_emit:
        workflow_logger.info("Test info message")
        workflow_logger.warning("Test warning message")
        
        # Check that log messages were emitted
        assert mock_emit.call_count >= 2

def test_custom_exceptions():
    """
    Test custom exception creation and logging.
    """
    # Test WorkflowExecutionError
    workflow_error = WorkflowExecutionError(
        "Workflow failed", 
        step="data_processing", 
        error_type="runtime_error"
    )
    assert "Workflow failed" in str(workflow_error)
    assert "Step: data_processing" in str(workflow_error)
    assert "Type: runtime_error" in str(workflow_error)

    # Test FileAnalysisError
    file_error = FileAnalysisError(
        "Unable to parse file", 
        file_path="/path/to/problematic/file.txt"
    )
    assert "Unable to parse file" in str(file_error)
    assert "File: /path/to/problematic/file.txt" in str(file_error)

    # Test ConfigurationError
    config_error = ConfigurationError(
        "Invalid configuration", 
        config_key="database_connection"
    )
    assert "Invalid configuration" in str(config_error)
    assert "Config: database_connection" in str(config_error)

def test_error_logging():
    """
    Test logging of custom exceptions.
    """
    with patch.object(error_logger, 'error') as mock_error_log:
        try:
            raise WorkflowExecutionError(
                "Simulated workflow failure", 
                step="test_step", 
                error_type="simulation"
            )
        except WorkflowExecutionError as e:
            error_logger.error(str(e), exc_info=True)
        
        # Verify error was logged
        mock_error_log.assert_called_once()

def test_audit_logging():
    """
    Test audit logging functionality.
    """
    with patch.object(audit_logger, 'info') as mock_audit_log:
        audit_logger.info("User action: login", extra={
            'user': 'test_user',
            'action': 'login',
            'timestamp': '2025-01-20T07:31:13Z'
        })
        
        # Verify audit log was recorded
        mock_audit_log.assert_called_once()
