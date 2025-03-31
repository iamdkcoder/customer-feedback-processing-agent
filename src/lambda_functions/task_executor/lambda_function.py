import logging
import json
from agents import Runner
import asyncio
from tools import (
    sentiment_analysis_tool,
    topic_categorization_tool,
    keyword_contextualization_tool,
    summary_generation_tool,
    task_planner_tool,
)
import boto3
import os
from dotenv import load_dotenv
from utils import send_response

load_dotenv(override=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AWS_REGION = os.getenv("AWS_REGION")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
SEND_RESPONSE_QUEUE_URL = os.getenv("SEND_RESPONSE_QUEUE_URL")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs = boto3.resource("sqs", region_name=AWS_REGION)
agent_result_table = dynamodb.Table(TABLE_NAME)
send_response_queue = sqs.Queue(SEND_RESPONSE_QUEUE_URL)


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_lambda_handler(event, context))


async def async_lambda_handler(event, context):
    try:
        for record in event.get("Records", []):
            raw_body = record.get("body")
            body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
            connection_id = body.get("connection_id")
            request_id = body.get("request_id")
            debug = body.get("debug", False)
        try:
            agent_result_entries = agent_result_table.get_item(
                Key={"request_id": request_id}
            )
            if "Item" not in agent_result_entries:
                response_message = (
                    f"Agent result entries not found for request_id: {request_id}"
                )
                logger.error(response_message)
                response = {
                    "statusCode": 404,
                    "body": json.dumps({"message": response_message}),
                }
                await send_response(connection_id, response, debug)
                return response
        except Exception as e:
            response_message = f"Error getting agent result entries: {str(e)}"
            logger.error(response_message)
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
            await send_response(connection_id, response)
            return response
        data = agent_result_entries.get("Item")
        original_input = data.get("original_input")
        feedback_text = original_input.get("feedback_text")
        instructions = original_input.get("instructions")

        # Get the task planner output
        try:
            task_planner_output = await Runner.run(
                starting_agent=task_planner_tool, input=instructions
            )

        except Exception as e:
            response_message = f"Error executing task planner: {str(e)}"
            logger.error(response_message)
            await send_response(connection_id, response_message, debug)
            return {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
        try:
            tool_results = await execute_task(
                task_planner_output.final_output.use_tools, feedback_text
            )
            result = {
                "use_tools": task_planner_output.final_output.use_tools,
                "tool_results": tool_results,
                "message": task_planner_output.final_output.message,
            }
        except Exception as e:
            response_message = f"Error executing tasks: {str(e)}"
            logger.error(response_message)
            await send_response(connection_id, response_message, debug)
            return {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
        try:
            logger.info(f"Result: {result}")
            agent_result_table.update_item(
                Key={"request_id": request_id},
                UpdateExpression="set task_execution_result = :result, processing_status = :status",
                ExpressionAttributeValues={
                    ":result": result,
                    ":status": "completed",
                },
            )
        except Exception as e:
            response_message = f"Error updating agent result table: {str(e)}"
            logger.error(response_message)
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
            await send_response(connection_id, response, debug)
            return response
        try:
            send_response_queue.send_message(
                MessageBody=json.dumps(
                    {
                        "connection_id": connection_id,
                        "request_id": request_id,
                    }
                )
            )
        except Exception as e:
            response_message = f"Error sending response queue: {str(e)}"
            logger.error(response_message)
            response = {
                "statusCode": 500,
                "body": json.dumps({"message": response_message}),
            }
            await send_response(connection_id, response, debug)
            return response
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Task Executor Lambda executed successfully!"}
            ),
        }
    except Exception as e:
        response_message = f"Error in task executor lambda: {str(e)}"
        logger.error(response_message)
        await send_response(connection_id, response_message, debug)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": response_message}),
        }


async def execute_task(use_tools: list[str], input: str) -> list:
    tool_map = {
        "sentiment_analysis": sentiment_analysis_tool,
        "topic_categorization": topic_categorization_tool,
        "keyword_contextualization": keyword_contextualization_tool,
        "summary_generation": summary_generation_tool,
    }

    agent_tasks = []
    tool_names = []  # Store tool names for mapping results later

    for tool_name in use_tools:
        try:
            tool = tool_map[tool_name]
            tool_names.append(tool_name)  # Keep track of tool names in order
            agent_tasks.append(Runner.run(starting_agent=tool, input=input))
        except KeyError:
            raise KeyError(f"Invalid tool name: {tool_name}")

    try:
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        processed_results = {}
        for tool_name, result in zip(tool_names, results):
            if isinstance(result, Exception):
                response_message = (
                    f"Task execution failed for {tool_name}: {str(result)}"
                )
                logger.error(response_message)
                processed_results[tool_name] = {
                    "error": response_message
                }  # Store errors as well
            else:
                processed_results[tool_name] = (
                    result.final_output.model_dump() if result.final_output else None
                )

        return processed_results
    except Exception as e:
        response_message = f"Error executing tasks: {str(e)}"
        logger.error(response_message)
        raise
