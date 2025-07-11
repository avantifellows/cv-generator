"""
Custom exceptions for CV Generator application
"""


class CVGeneratorException(Exception):
    """Base exception for CV Generator application"""
    pass


class CVGenerationError(CVGeneratorException):
    """Raised when CV generation fails"""
    pass


class CVNotFoundError(CVGeneratorException):
    """Raised when CV is not found"""
    pass


class ValidationError(CVGeneratorException):
    """Raised when data validation fails"""
    pass


class TemplateError(CVGeneratorException):
    """Raised when template rendering fails"""
    pass


class PDFGenerationError(CVGeneratorException):
    """Raised when PDF generation fails"""
    pass