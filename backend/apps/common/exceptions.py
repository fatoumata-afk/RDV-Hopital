"""Normalisation des erreurs API : toujours {detail, code, errors?}."""

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class BusinessRuleError(APIException):
    """Erreur de règle métier renvoyée au client avec un code exploitable."""

    status_code = 400
    default_detail = "Opération impossible."
    default_code = "business_rule_error"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


class ConflictError(BusinessRuleError):
    status_code = 409
    default_detail = "Conflit avec l'état actuel de la ressource."
    default_code = "conflict"


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    code = getattr(exc, "default_code", "error")
    if isinstance(exc, APIException):
        detail = exc.detail
        if isinstance(detail, dict) or isinstance(detail, list):
            response.data = {
                "detail": "Données invalides.",
                "code": "invalid",
                "errors": data,
            }
            return response
        code = getattr(detail, "code", code)
        response.data = {"detail": str(detail), "code": code}
    return response
