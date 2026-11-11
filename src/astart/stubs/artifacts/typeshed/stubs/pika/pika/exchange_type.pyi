from enum import StrEnum

class ExchangeType(StrEnum):
    direct = "direct"
    fanout = "fanout"
    headers = "headers"
    topic = "topic"
