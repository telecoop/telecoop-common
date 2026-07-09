class SellsyApiError(Exception):
    statusCode: int
    textError: str
    pass


class TcSellsyError(Exception):
    pass
