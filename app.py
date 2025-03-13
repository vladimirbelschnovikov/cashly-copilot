import chainlit as cl
import requests

WEBHOOK_URL = "https://n8n.gocashly.io/webhook/cashly-copilot"  # Replace with your actual webhook URL


def process_response(response_json) -> str:
    """
    Extracts and formats the 'combinedOutput' field as a Markdown-friendly response.
    """
    if isinstance(response_json, list) and len(response_json) > 0:
        response_json = response_json[0]  # Extract the first dictionary

    # Extract text
    raw_text = response_json.get("Output", "No response from webhook")

    # Format the text properly
    formatted_text = (
            raw_text.replace("## ", "\n\n## ")  # Ensure section headings have spacing
                .replace("- ", "\n- ")      # Ensure each bullet point appears on a new line
                .replace("1. ", "\n1. ")    # Ensure ordered lists start on a new line
                .replace("2. ", "\n2. ")
                .replace("3. ", "\n3. ")
                .replace("4. ", "\n4. ")
    )

    return formatted_text

@cl.on_chat_start
def on_chat_start():
    cl.Message(content="Welcome to Cashly Copilot! How can I assist you today?").send()

@cl.on_message
async def on_message(msg: cl.Message):
    user_message = msg.content.strip()
    try:
        response = requests.post(WEBHOOK_URL, json={"message": user_message})
        print(f"Webhook status: {response.status_code}")
        print(f"Webhook response: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            reply_message = process_response(response_json)
        else:
            reply_message = f"Error: Webhook returned status code {response.status_code}"
    except Exception as e:
        reply_message = f"Error occurred: {str(e)}"

    # Send the processed text with Markdown formatting
    await cl.Message(content=reply_message, author="Assistant", avatar="assistant.png").send()



@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")

@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")

@cl.on_chat_resume
async def on_chat_resume(thread: dict):  # Use 'dict' instead of 'ThreadDict'
    print("The user resumed a previous chat session!")
    # Optionally, handle chat resumption (load state, etc.)
