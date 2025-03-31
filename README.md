# Feedback Processor AI Agent

## Overview
The **Feedback Processor AI Agent** is an AI-powered system that processes customer feedback based on API user instructions. It consists of two Lambda-based agents that analyze and categorize feedback while ensuring compliance with predefined guardrails.

![Cloud Architecture](./src/assets/AWS-Architecture-Diagram.svg)


## Architecture

### 1. **Guardrail Agent**
- **Deployed as:** AWS Lambda function
- **Function:** 
  - Evaluates user instructions for safety.
  - Routes messages to either the **Task Executor Queue** or **Send Response Queue** based on the `is_safe` attribute.

### 2. **Task Executor Agent**
- **Deployed as:** AWS Lambda function
- **Function:**
  - Executes various NLP tools to process feedback as per user instructions.
  - Plans tool sequence execution and runs tools concurrently.
  - Stores results in **Agent-State DynamoDB** with:
    - **Primary Key:** `request_id`
    - **Global Secondary Index (GSI):** `feedback_id`

#### **Available NLP Tools:**
- **Sentiment Analysis Tool:** Determines sentiment (Positive, Negative, Neutral).
- **Topic Categorization Tool:** Categorizes feedback into predefined topics (e.g., Product Quality, Delivery, Support).
- **Keyword Contextualization Tool:** Extracts relevant keywords with scores.
- **Summarization Tool:** Generates concise summaries and actionable insights.

### 3. **Send Response Agent**
- **Deployed as:** AWS Lambda function
- **Function:**
  - Reads from the **Send Response Queue**.
  - Fetches the processed feedback using `request_id` from DynamoDB.
  - Sends results to the WebSocket connection using `connection_id`.

## Cloud Architecture

## AWS Infrastructure
- **AWS Lambda Functions:** Guardrail, Task Executor, Send Response
- **DynamoDB:** Stores processed feedback
- **SQS Queues:** Task Executor Queue, Send Response Queue
- **API Gateway (WebSocket):** Single route (`request.body.action="process"`)
- **IAM Role:** Single role with permissions for Lambda execution, DynamoDB, and SQS

## Repository Structure
```
📂 src
 ├── 📂 lambda_functions
 │   ├── 📂 guardrail
 │   │   ├── lambda_function.py
 │   │   ├── prompts.py
 │   │   ├── tools.py
 │   ├── 📂 task_executor
 │   │   ├── lambda_function.py
 │   │   ├── prompts.py
 │   │   ├── tools.py
 │   ├── 📂 send_response
 │   │   ├── lambda_function.py
 │   │   ├── prompts.py
 │   │   ├── tools.py
 ├── 📂 experiments
 ├── .env
 ├── requirements.txt
```
## API Testing
### WebSocket API Endpoint:
```
wss://7q3r72lbzc.execute-api.ap-south-1.amazonaws.com/production/
```
### Sample API Request:
```json
{
    "action":"process",
    "instructions":"Categorize the topic and analyse the sentiment",
    "feedback_id":"12345",
    "feedback_text":"Amazing product but checkout process is difficult",
    "debug": true
}
```

## Local Setup Instructions
1. **Create Virtual Environment & Install Dependencies**
```sh
uv venv
```
```sh
uv sync
```

2. **Set Environment Variables**
- Define required variables in `.env` file.



## Future Improvements
- Implement more robust instruction validation for Guardrail Agent.
- Introduce additional NLP tools for enhanced feedback processing.
- Optimize concurrency management for better performance.

---
Feel free to contribute and enhance this project! 🚀

