import json
import logging
import boto3
import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv(override=True)

AWS_REGION = os.getenv("AWS_REGION")
WEBSOCKET_ENDPOINT_URL = os.getenv("WEBSOCKET_ENDPOINT_URL")
apigateway = boto3.client(
    "apigatewaymanagementapi",
    endpoint_url=WEBSOCKET_ENDPOINT_URL,
    region_name=AWS_REGION,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def send_response(connection_id: str, data: dict, debug: bool = False):
    if debug:
        try:
            apigateway.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(
                    data, default=lambda x: float(x) if isinstance(x, Decimal) else x
                ),
            )
        except Exception as e:
            response_message = f"Error sending response to client: {e}"
            logger.error(response_message)
            await send_response(connection_id, {"message": response_message}, True)
            return {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
