import json
import asyncio
import boto3
import os
from dotenv import load_dotenv
import logging
from utils import send_response

load_dotenv(override=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WEBSOCKET_ENDPOINT_URL = os.getenv("WEBSOCKET_ENDPOINT_URL")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
AWS_REGION = os.getenv("AWS_REGION")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

agent_result_table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_lambda_handler(event, context))


async def async_lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        connection_id = body["connection_id"]
        request_id = body["request_id"]

        response = agent_result_table.get_item(Key={"request_id": request_id})

        if "Item" in response:
            data = response["Item"]

            try:
                # Send message to client via WebSocket API Gateway
                await send_response(connection_id, data, True)
            except Exception as e:
                response_message = f"Error sending response to client: {e}"
                logger.error(response_message)
                await send_response(connection_id, response_message, True)
                return {
                    "statusCode": 500,
                    "body": json.dumps({"message": response_message}),
                }

    return {"statusCode": 200, "body": json.dumps({"message": "Response sent"})}
