import asyncio
import json
import os
import time
from datetime import datetime
from queue import Queue
from typing import Any, Dict, List, Optional, Tuple, Union

import websockets
from fastapi import WebSocket, WebSocketDisconnect

from .datamodel import Message, SocketMessage, Workflow
from .utils import (
    extract_successful_code_blocks,
    summarize_chat_history,
)
from .workflowmanager import WorkflowManager


class AutoGenChatManager:
    """
    This class handles the automated generation and management of chat interactions
    using an automated workflow configuration and message queue.
    """

    def __init__(self, message_queue: Queue) -> None:
        """
        Initializes the AutoGenChatManager with a message queue.

        :param message_queue: A queue to use for sending messages asynchronously.
        """
        self.message_queue = message_queue

    def send(self, message: str) -> None:
        """
        Sends a message by putting it into the message queue.

        :param message: The message string to be sent.
        """
        if self.message_queue is not None:
            self.message_queue.put_nowait(message)

    def chat(
        self,
        message: Message,
        history: List[Dict[str, Any]],
        workflow: Any = None,
        connection_id: Optional[str] = None,
        work_dir: Optional[str] = None,  # Updated to accept work_dir directly (aka user_dir),
        dest_dir: Optional[str] = None,
        **kwargs,
    ) -> Message:
        """
        Processes an incoming message according to the agent's workflow configuration
        and generates a response.

        :param message: An instance of `Message` representing an incoming message.
        :param history: A list of dictionaries, each representing a past interaction.
        :param workflow: The workflow configuration to follow.
        :param connection_id: An optional connection identifier.
        :param work_dir: The directory where the workflow's output will be saved.
        :param kwargs: Additional keyword arguments.
        :return: An instance of `Message` representing a response.
        """
        if work_dir is None:
            raise ValueError("work_dir must be provided and cannot be None.")

        os.makedirs(work_dir, exist_ok=True)

        #print(f"workflow: {workflow}") # ERROR: NO AGENTS FIELD PRESENT
        print(type(workflow))

        # Proceed with the workflow processing
        workflow_manager = WorkflowManager(
            workflow=workflow,
            history=history,
            work_dir=work_dir,
            send_message_function=self.send,
            connection_id=connection_id,
            dest_dir=dest_dir,
        )

        workflow = Workflow.model_validate(workflow)

        message_text = message.content.strip()

        start_time = time.time()
        workflow_manager.run(message=f"{message_text}", clear_history=False)
        end_time = time.time()

        metadata = {
            "messages": workflow_manager.agent_history,
            "summary_method": workflow.summary_method,
            "time": end_time - start_time,
        }

        output = self._generate_output(message_text, workflow_manager, workflow)

        output_message = Message(
            user_id=message.user_id,
            role="assistant",
            content=output,
            meta=json.dumps(metadata),
            session_id=message.session_id,
        )

        return output_message


    def _generate_output(
        self,
        message_text: str,
        workflow_manager: WorkflowManager,
        workflow: Workflow,
    ) -> str:
        """
        Generates the output response based on the workflow configuration and agent history.

        :param message_text: The text of the incoming message.
        :param flow: An instance of `WorkflowManager`.
        :param flow_config: An instance of `AgentWorkFlowConfig`.
        :return: The output response as a string.
        """

        output = ""
        if workflow.summary_method == "last":
            successful_code_blocks = extract_successful_code_blocks(workflow_manager.agent_history)
            last_message = (
                workflow_manager.agent_history[-1]["message"]["content"] if workflow_manager.agent_history else ""
            )
            successful_code_blocks = "\n\n".join(successful_code_blocks)
            output = (last_message + "\n" + successful_code_blocks) if successful_code_blocks else last_message
        elif workflow.summary_method == "llm":
            client = workflow_manager.receiver.client
            status_message = SocketMessage(
                type="agent_status",
                data={
                    "status": "summarizing",
                    "message": "Summarizing agent dialogue",
                },
                connection_id=workflow_manager.connection_id,
            )
            self.send(status_message.dict())
            output = summarize_chat_history(
                task=message_text,
                messages=workflow_manager.agent_history,
                client=client,
            )

        elif workflow.summary_method == "none":
            output = ""
        return output