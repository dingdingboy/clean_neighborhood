"""
Llama-server process manager for starting/stopping the model service.

This module manages the lifecycle of the llama.cpp server process,
ensuring it's started when the backend starts and properly terminated on shutdown.
"""

import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LlamaServerManager:
    """
    Manager for llama-server subprocess.

    Handles starting the server, waiting for it to be ready,
    and graceful shutdown.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        mmproj_path: Optional[str] = None,
        cli_path: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        context_size: int = 8192,
        threads: int = -1,
        gpu_layers: int = 0,
        parallel_slots: int = 4,
    ):
        """
        Initialize the server manager.

        Args:
            model_path: Path to the GGUF model file
            mmproj_path: Path to the multimodal projector file
            cli_path: Path to llama.cpp binaries
            host: Host to bind the server to
            port: Port to listen on
            context_size: Context window size
            threads: Number of CPU threads (-1 = auto)
            gpu_layers: Number of layers to offload to GPU (0 = CPU only)
            parallel_slots: Number of parallel processing slots
        """
        self.model_path = Path(model_path or settings.LLAMA_MODEL_PATH)
        self.mmproj_path = Path(mmproj_path or settings.LLAMA_MMPROJ_PATH)
        self.cli_path = Path(cli_path or settings.LLAMA_CLI_PATH).expanduser()
        self.host = host
        self.port = port
        self.context_size = context_size
        self.threads = threads
        self.gpu_layers = gpu_layers
        self.parallel_slots = parallel_slots

        self._process: Optional[asyncio.subprocess.Process] = None
        self._server_url = f"http://{host}:{port}"

    def _build_command(self) -> List[str]:
        """Build the llama-server command with arguments."""
        server_bin = self.cli_path / "llama-server"

        cmd = [
            str(server_bin),
            "--model", str(self.model_path),
            "--mmproj", str(self.mmproj_path),
            "--port", str(self.port),
            "--host", self.host,
            "-ngl", str(self.gpu_layers),
            "--ctx-size", str(self.context_size),
            "--threads", str(self.threads),
            "--batch-size", "2048",
            "--ubatch-size", "512",
            "--timeout", "300",
            "-np", str(self.parallel_slots),
            "--metrics",
        ]

        return cmd

    async def start(self, ready_timeout: float = 300.0) -> None:
        """
        Start the llama-server process and wait for it to be ready.

        Args:
            ready_timeout: Maximum time to wait for server to be ready (seconds)

        Raises:
            RuntimeError: If server fails to start or becomes ready in time
        """
        if self._process is not None:
            logger.info("llama-server is already running")
            return

        # Validate files exist
        if not self.model_path.exists():
            raise RuntimeError(f"Model file not found: {self.model_path}")
        if not self.mmproj_path.exists():
            raise RuntimeError(f"MMProj file not found: {self.mmproj_path}")

        server_bin = self.cli_path / "llama-server"
        if not server_bin.exists():
            raise RuntimeError(f"llama-server binary not found: {server_bin}")

        cmd = self._build_command()
        logger.info(f"Starting llama-server on {self.host}:{self.port} with ctx-size={self.context_size}")
        logger.debug(f"Command: {' '.join(cmd)}")

        # Start the process
        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start llama-server: {e}") from e

        # Wait for server to be ready
        logger.info(f"Waiting for llama-server to be ready (timeout: {ready_timeout}s)...")
        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > ready_timeout:
                    await self.stop()
                    raise RuntimeError(
                        f"llama-server failed to become ready within {ready_timeout}s"
                    )

                try:
                    response = await client.get(
                        f"{self._server_url}/health",
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        logger.info("llama-server is ready and healthy")
                        return
                except httpx.ConnectError:
                    # Server not yet accepting connections
                    pass
                except Exception as e:
                    logger.debug(f"Health check error: {e}")

                # Check if process died
                if self._process.returncode is not None:
                    stdout, _ = await self._process.communicate()
                    raise RuntimeError(
                        f"llama-server process exited with code {self._process.returncode}. "
                        f"Output: {stdout.decode()[-2000:] if stdout else 'No output'}"
                    )

                await asyncio.sleep(0.5)

    async def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the llama-server process gracefully.

        Args:
            timeout: Time to wait for graceful shutdown before force kill
        """
        if self._process is None:
            return

        logger.info("Stopping llama-server...")

        try:
            # Try graceful termination
            self._process.terminate()

            try:
                await asyncio.wait_for(
                    self._process.wait(),
                    timeout=timeout
                )
                logger.info("llama-server stopped gracefully")
            except asyncio.TimeoutError:
                logger.warning("llama-server did not stop gracefully, forcing kill...")
                self._process.kill()
                await self._process.wait()
                logger.info("llama-server killed")

        except Exception as e:
            logger.error(f"Error stopping llama-server: {e}")
        finally:
            self._process = None

    async def health_check(self) -> bool:
        """Check if llama-server is healthy."""
        if self._process is None or self._process.returncode is not None:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._server_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False

    @property
    def is_running(self) -> bool:
        """Check if the server process is running."""
        return self._process is not None and self._process.returncode is None


# Global singleton instance
_server_manager: Optional[LlamaServerManager] = None


def get_server_manager() -> LlamaServerManager:
    """Get or create the global server manager instance."""
    global _server_manager
    if _server_manager is None:
        _server_manager = LlamaServerManager(
            context_size=settings.LLAMA_CONTEXT_SIZE,
        )
    return _server_manager


async def start_model_server() -> None:
    """Start the model server (convenience function)."""
    manager = get_server_manager()
    await manager.start()


async def stop_model_server() -> None:
    """Stop the model server (convenience function)."""
    global _server_manager
    if _server_manager is not None:
        await _server_manager.stop()
        _server_manager = None
