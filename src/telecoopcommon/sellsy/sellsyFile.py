from .sellsyError import SellsyApiError


class SellsyFile:
    def upload(
        self,
        sellsyConnector,
        logger,
        filePath,
        fileName,
        fileMimetype,
        resource,
        resourceId,
    ):
        files = {
            "file": (fileName, open(filePath, "rb"), fileMimetype, {"Expires": "0"}),
        }

        response = None
        try:
            response = sellsyConnector.api2Post(
                f"/v2/{resource}/{resourceId}/files", files=files
            )
        except SellsyApiError as SAE:
            logger.warning(SAE)

        return response
