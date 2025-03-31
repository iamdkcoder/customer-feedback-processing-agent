import json
import asyncio
from agents import Runner
from tools import guardrail_tool
from uuid import uuid4
import boto3
import os
from dotenv import load_dotenv
from utils import send_response
import logging
import time

load_dotenv(override=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


TASK_EXECUTOR_QUEUE_URL = os.getenv("TASK_EXECUTOR_QUEUE_URL")
SEND_RESPONSE_QUEUE_URL = os.getenv("SEND_RESPONSE_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")

sqs = boto3.resource("sqs", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

agent_result_table = dynamodb.Table(DYNAMODB_TABLE_NAME)
task_executor_queue = sqs.Queue(TASK_EXECUTOR_QUEUE_URL)
send_response_queue = sqs.Queue(SEND_RESPONSE_QUEUE_URL)


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_lambda_handler(event, context))


async def async_lambda_handler(event, context):
    try:
        connection_id = event["requestContext"]["connectionId"]
        request_id = str(uuid4())
        raw_body = event["body"]
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        debug = body.get("debug", False)
        if body.get("instructions"):
            try:
                start_time = time.time()
                guardrail_agent_result = await Runner.run(
                    starting_agent=guardrail_tool, input=body.get("instructions")
                )
                guardrail_agent_result_dict = (
                    guardrail_agent_result.final_output.model_dump()
                )
                end_time = time.time()
                logger.info(
                    f"Guardrail agent execution time: {end_time - start_time} seconds"
                )
                guardrail_agent_result_dict["execution_time"] = str(
                    end_time - start_time
                )
            except Exception as e:
                response_message = f"Error running guardrail agent LLM API: {e}"
                logger.error(response_message)
                await send_response(connection_id, response_message, debug)
                return {
                    "statusCode": 500,
                    "body": json.dumps({"message": response_message}),
                }
        else:
            guardrail_agent_result_dict = {
                "is_safe": False,
                "reason": "No instruction provided",
                "execution_time": "0",
            }

        logger.info(f"Guardrail result: {guardrail_agent_result_dict}")

        try:
            agent_result_table.put_item(
                Item={
                    "request_id": request_id,
                    "feedback_id": body.get("feedback_id"),
                    "instruction": body.get("instructions"),
                    "original_input": body,
                    "guardrail_result": guardrail_agent_result_dict,
                }
            )
        except Exception as e:
            response_message = f"Error saving guardrail result to DynamoDB: {e}"
            logger.error(response_message)
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
            await send_response(connection_id, response, debug)
            return response

        if guardrail_agent_result_dict.get("is_safe"):
            try:
                task_executor_queue.send_message(
                    MessageBody=json.dumps(
                        {
                            "request_id": request_id,
                            "connection_id": connection_id,
                            "debug": debug,
                        }
                    )
                )
            except Exception as e:
                response_message = f"Error sending message to task_executor_queue: {e}"
                logger.error(response_message)
                response = {
                    "statusCode": 500,
                    "body": json.dumps({"message": response_message}),
                }
                await send_response(connection_id, response, debug)
                return response
        else:
            try:
                send_response_queue.send_message(
                    MessageBody=json.dumps(
                        {
                            "request_id": request_id,
                            "connection_id": connection_id,
                            "debug": debug,
                        }
                    )
                )
            except Exception as e:
                response_message = f"Error sending response to send_response_queue: {e}"
                logger.error(response_message)
                response = {
                    "statusCode": 500,
                    "body": json.dumps({"message": response_message}),
                }
                await send_response(connection_id, response, debug)
                return response
        response = {
            "statusCode": 200,
            "body": json.dumps({"message": " Guardrail Lambda executed successfully!"}),
        }
        await send_response(connection_id, response, debug)
        return response
    except Exception as e:
        response_message = f"Error in guardrail lambda: {e}"
        logger.error(response_message)
        response = {
            "statusCode": 500,
            "body": json.dumps({"message": response_message}),
        }
        await send_response(connection_id, response, debug)
        return response
