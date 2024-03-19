import os
from typing import Dict
from dotenv import load_dotenv
import chainlit as cl
from openai import AsyncOpenAI
from openai.types.beta import Thread
from openai.types.beta.threads import (
    MessageContentImageFile,
    MessageContentText,
    ThreadMessage,
)

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")
client = AsyncOpenAI(api_key=api_key)


async def process_thread_message(
    message_references: Dict[str, cl.Message], thread_message: ThreadMessage
):
    for idx, content_message in enumerate(thread_message.content):
        id = thread_message.id + str(idx)
        if isinstance(content_message, MessageContentText):
            if id in message_references:
                msg = message_references[id]
                msg.content = content_message.text.value
                await msg.update()
            else:
                message_references[id] = cl.Message(
                    author=thread_message.role, content=content_message.text.value
                )
                await message_references[id].send()
        elif isinstance(content_message, MessageContentImageFile):
            image_id = content_message.image_file.file_id
            response = await client.files.with_raw_response.retrieve_content(image_id)
            elements = [
                cl.Image(
                    name=image_id,
                    content=response.content,
                    display="inline",
                    size="large",
                ),
            ]

            if id not in message_references:
                message_references[id] = cl.Message(
                    author=thread_message.role,
                    content="",
                    elements=elements,
                )
                await message_references[id].send()
        else:
            print("unknown message type", type(content_message))


@cl.on_chat_start
async def start_chat():
    thread = await client.beta.threads.create()
    cl.user_session.set("thread", thread)
    await cl.Message(author="assistant", content="How do you feel today?").send()


@cl.on_message
async def run_conversation(message_from_ui: cl.Message):
    thread = cl.user_session.get("thread")  # type: Thread
    # Add the message to the thread
    init_message = await client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message_from_ui.content
    )

    # Send empty message to display the loader
    loader_msg = cl.Message(author="assistant", content="")
    await loader_msg.send()

    # Create the run
    run = await client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant_id
    )
    message_references = {}  # type: Dict[str, cl.Message]

    # Periodically check for updates
    while True:
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )

        # Fetch the run steps
        run_steps = await client.beta.threads.runs.steps.list(
            thread_id=thread.id, run_id=run.id, order="asc"
        )

        # print(run_steps)

        for step in run_steps.data:
            # Fetch step details
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread.id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details
            # Update step content in the Chainlit UI
            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread.id,
                )
                await process_thread_message(message_references, thread_message)

        await cl.sleep(1)  # Refresh every second

        if run.status in ["cancelled", "failed", "completed", "expired"]:
            break
            