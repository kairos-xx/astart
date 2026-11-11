from typing import Final

from _typeshed import Incomplete
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult

class BankAccountInstantVerificationGateway:
    gateway: Incomplete
    config: Incomplete
    graphql_client: Incomplete
    CREATE_JWT_MUTATION: Final[str]
    def __init__(self, gateway) -> None: ...
    def create_jwt(self, request) -> SuccessfulResult | ErrorResult: ...
