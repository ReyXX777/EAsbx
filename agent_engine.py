# agent_engine.py
import asyncio
import os
from PySide6.QtCore import QThread, Signal
from browser_use import Agent, Browser, ChatGoogle

from agent_state_manager import AgentStateManager
from agent_result_parser import AgentResultParser

class AgentExecutionWorker(QThread):
    step_updated = Signal(str)
    task_finished = Signal(object)
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
        """
        QThread entry point.

        Creates and owns the asyncio event loop for this worker thread.
        The worker thread never shares an event loop with the Qt main thread.
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                self._execute_agent_task()
            )

        except Exception as e:
            err_msg = f"Agent worker failure: {e}"

            self.state_manager.mark_failed(err_msg)
            self.error_occurred.emit(err_msg)

        finally:
            try:
                loop.run_until_complete(
                    asyncio.sleep(0)
                )
            except Exception:
                pass

            asyncio.set_event_loop(None)
            loop.close()


    async def _execute_agent_task(self):
        """
        Execute the browser agent and convert its raw execution history
        into our application-level AgentResult.

        """

        browser = None

        try:
            # ---------------------------------------------------------
            # 1. Start canonical task lifecycle
            # ---------------------------------------------------------

            self.state_manager.start_task()

            self.step_updated.emit(
                f"🚀 Starting task: '{self.task.prompt}'"
            )

            # ---------------------------------------------------------
            # 2. Configure API credentials
            # ---------------------------------------------------------

            if not self.api_key:
                raise ValueError(
                "   Google API key is missing."
                )

            os.environ["GOOGLE_API_KEY"] = self.api_key

            # ---------------------------------------------------------
            # 3. Initialize LLM
            # ---------------------------------------------------------

            llm = ChatGoogle(
                model="gemini-3.5-flash-lite"
            )

            # ---------------------------------------------------------
            # 4. Connect to browser
            # ---------------------------------------------------------

            if self.cdp_url:
                self.step_updated.emit(
                    f"🌐 Connecting to embedded browser via CDP "
                    f"({self.cdp_url})..."
                )

                browser = Browser(
                    cdp_url=self.cdp_url
                )

            else:
                self.step_updated.emit(
                    "🌐 Starting standalone browser..."
                )

                browser = Browser(
                    headless=self.headless
                )

            # ---------------------------------------------------------
            # 5. Create agent
            # ---------------------------------------------------------

            agent = Agent(
                task=self.task.prompt,
                llm=llm,
                browser=browser,
                llm_timeout=30,
                step_timeout=60,
                max_failures=3,
                final_response_after_failure=True,
            )

            self.step_updated.emit(
                f"🚀 Initializing Agent for task: "
                f"'{self.task.prompt}'"
            )

            # ---------------------------------------------------------
            # 6. Execute agent
            # ---------------------------------------------------------

            history = await agent.run(
                on_step_end=self._on_step_end_callback
            )

            # ---------------------------------------------------------
            # 7. Check cancellation before processing result
            # ---------------------------------------------------------

            if self._cancel_requested:
                self.state_manager.mark_cancelled()

                self.error_occurred.emit(
                    "Task cancelled by user."
                )

                return

            # ---------------------------------------------------------
            # 8. Convert browser-use history into our domain result
            # ---------------------------------------------------------

            parsed_result = AgentResultParser.parse(
                history
            )

            # ---------------------------------------------------------
            # 9. Determine actual execution outcome
            # ---------------------------------------------------------

            if parsed_result.succeeded:

                self.state_manager.mark_completed(
                    parsed_result.final_text
                )

                self.task_finished.emit(
                    parsed_result
                )

                return

            # ---------------------------------------------------------
            # 10. Agent finished but did not report success
            # ---------------------------------------------------------

            error_message = (
                parsed_result.errors[-1]
                if parsed_result.errors
                else (
                    "The browser agent finished without "
                    "reporting successful completion."
                )
            )

            self.state_manager.mark_failed(
                error_message
            )

            self.error_occurred.emit(
                error_message
            )

        except asyncio.TimeoutError:

            err_msg = (
                "Agent execution timed out while waiting "
                "for the model or browser response."
            )

            self.state_manager.mark_failed(
                err_msg
            )

            self.error_occurred.emit(
                err_msg
            )

        except asyncio.CancelledError:

            self.state_manager.mark_cancelled(
                "Agent execution was cancelled."
            )

            self.error_occurred.emit(
                "Agent execution was cancelled."
            )

            raise

        except Exception as e:

            err_msg = (
                f"Agent execution failure: "
                f"{type(e).__name__}: {e}"
            )

            self.state_manager.mark_failed(
                err_msg
            )

            self.error_occurred.emit(
                err_msg
            )

        finally:

            # ---------------------------------------------------------
            # 11. Browser cleanup
            # ---------------------------------------------------------

            if browser is not None:

                try:
                    await browser.stop()
                except Exception as cleanup_error:
                    self.step_updated.emit(
                        "⚠️ Browser cleanup warning: "
                        f"{cleanup_error}"
                    )