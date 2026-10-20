from typing import Tuple

from .sellsyConnectorBase import TcSellsyConnectorBase


class SellsyFile:
    def __init__(self, sellsyConnector: TcSellsyConnectorBase) -> None:
        self.connector = sellsyConnector

    def upload(
        self,
        filePath: str,
        fileName: str,
        fileMimetype: str,
        resource: str,
        resourceId: str,
    ) -> Tuple[bool, dict]:
        return self.connector.fileUpload(
            fileName=fileName,
            filePath=filePath,
            fileMimetype=fileMimetype,
            resource=resource,
            resourceId=resourceId,
        )

    def delete(self, fileId: str) -> bool:
        return self.connector.fileDelete(fileId)
