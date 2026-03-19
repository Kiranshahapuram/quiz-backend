from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, NotAuthenticated, PermissionDenied, NotFound, AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.http import Http404

class CustomAPIException(APIException):
    status_code = 400
    default_code = 'error'
    
    def __init__(self, message, code=None, status_code=None, field=None, details=None):
        self.message = message
        self.code = code or self.default_code
        if status_code is not None:
            self.status_code = status_code
        self.field = field
        self.details = details
        super().__init__(detail=self.message)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, (ObjectDoesNotExist, Http404)):
            exc = NotFound('Not found.')
        elif isinstance(exc, DjangoValidationError):
            exc = ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else list(exc))
        else:
            return None # Fallback to 500

    # DRF generated a response, let's normalize it
    code = 'ERROR'
    message = str(exc)
    field = None
    details = None

    if hasattr(exc, 'get_codes'):
        drf_codes = exc.get_codes()
    else:
        drf_codes = getattr(exc, 'default_code', 'error')

    from rest_framework_simplejwt.exceptions import InvalidToken
    
    if isinstance(exc, CustomAPIException):
        code = exc.code
        message = exc.message
        field = exc.field
        details = exc.details

    elif isinstance(exc, InvalidToken):
        err_msg = str(getattr(exc, 'detail', ''))
        if 'expired' in err_msg.lower() or (hasattr(exc, 'detail') and isinstance(exc.detail, dict) and exc.detail.get('messages', [{}])[0].get('message', '').lower().find('expired') != -1):
            code = 'TOKEN_EXPIRED'
            message = 'Token has expired.'
        else:
            code = 'TOKEN_INVALID'
            message = 'Token is invalid or expired.'

    elif isinstance(exc, AuthenticationFailed):
        code = 'INVALID_CREDENTIALS'
        message = 'Invalid credentials.'

    elif isinstance(exc, NotAuthenticated):
        code = 'TOKEN_INVALID'
        message = 'Authentication token was not provided or is invalid.'

    elif isinstance(exc, PermissionDenied):
        code = 'PERMISSION_DENIED'
        message = 'You do not have permission to perform this action.'

    elif isinstance(exc, NotFound):
        code = 'NOT_FOUND'
        message = 'The requested resource was not found.'

    elif isinstance(exc, ValidationError):
        code = 'VALIDATION_ERROR'
        message = 'Validation error occurred.'
        if isinstance(exc.detail, dict):
            details = exc.detail
            # Just pick the first field as the 'field' attribute
            field = next(iter(exc.detail.keys()), None)
            # Simplify detail format
            for k, v in details.items():
                details[k] = [str(item) for item in v] if isinstance(v, list) else str(v)
            if field and details[field]:
                message = f"{field}: {details[field][0]}"
        elif isinstance(exc.detail, list):
            details = {"non_field_errors": [str(i) for i in exc.detail]}
            message = str(exc.detail[0])
        else:
            details = {"non_field_errors": [str(exc.detail)]}

    payload = {
        "code": code,
        "message": message,
    }
    if field is not None:
        payload["field"] = field
    if details is not None:
        payload["details"] = details

    if response is not None:
        response.data = payload

    return response
