# agent_engine.py
import asyncio
import os
from PySide6.QtCore import QThread, Signal
from browser_use import Agent, Browser, ChatGoogle

from agent_state_manager import AgentStateManager


class AgentExecutionWorker(QThread):
    step_updated = Signal(str)
    task_finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        task,
        api_key,
        headless=False,
        cdp_url="http://127.0.0.1:9222",
    ):
        super().__init__()

        self.task = task
        self.api_key = api_key
        self.headless = headless
        self.cdp_url = cdp_url

        self.state_manager = AgentStateManager(task)

        # Cooperative cancellation flag.
        self._cancel_requested = False

    def get_status(self) -> dict:
        """API/UI Endpoint method to query current agent state at any time."""
        return self.state_manager.get_status()
    def cancel(self) -> None:
        """
        Request cooperative cancellation of the current task.

        This does not forcibly terminate the QThread.
        The running coroutine checks this request and exits cleanly.
        """

        self._cancel_requested = True

    async def _on_step_end_callback(self, agent: Agent):
        """
        Lifecycle hook executed after every agent step.

        The callback only reports execution information.
        The Task remains the canonical state container.
        """

        if self._cancel_requested:
            return

        formatted_step_msg = self.state_manager.record_step(agent)

        self.step_updated.emit(formatted_step_msg)

    def run(self):
        # Create a clean asyncio event loop for this QThread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._execute_agent_task())
        except Exception as e:
            err_msg = str(e)
            self.state_manager.mark_failed(err_msg)
            self.error_occurred.emit(err_msg)
        finally:
            loop.close()

    async def _execute_agent_task(self):
        try:
            self.state_manager.start_task()
            self.step_updated.emit(
                f"🚀 Starting task: '{self.task.prompt}'"
            )

            # Pass API key into environment for ChatGoogle
            os.environ["GOOGLE_API_KEY"] = self.api_key

            # Initialize LLM with high-throughput free-tier model
            llm = ChatGoogle(model="gemini-3.5-flash-lite")

            # Connect to existing embedded Qt WebEngine browser via CDP if provided
            if self.cdp_url:
                browser = Browser(cdp_url=self.cdp_url)
            else:
                browser = Browser(headless=self.headless)

            # Instantiate Agent with fail-safes and step hooks
            agent = Agent(
                task=self.task.prompt,
                llm=llm,
                browser=browser,
                llm_timeout=30,  # Max 30s for LLM API response
                step_timeout=60,  # Max 60s per DOM action
                max_failures=3,  # Max consecutive retries on error
                final_response_after_failure=True,  # Return best-effort summary if max_failures reached
            )

            self.step_updated.emit(
                f"🚀 Initializing Agent for task: '{self.task.prompt}'"
            )

            # Run loop with step monitoring callback
            result = await agent.run(
                on_step_end=self._on_step_end_callback
            )

            if self._cancel_requested:
                self.state_manager.mark_cancelled()

                self.error_occurred.emit(
                    "Task cancelled by user."
                )

                return

            self.state_manager.mark_completed(result)

            self.task_finished.emit(str(result))

        except asyncio.TimeoutError:
            err_msg = "Agent execution timed out while waiting for model or browser response."
            self.state_manager.mark_failed(err_msg)
            self.error_occurred.emit(err_msg)

        except Exception as e:
            err_msg = f"Agent Execution Failure: {str(e)}"
            self.state_manager.mark_failed(err_msg)
            self.error_occurred.emit(err_msg)