import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from medrix_flow.config.extensions_config import ExtensionsConfig, get_extensions_config, reload_extensions_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["mcp"])


class McpOAuthConfigResponse(BaseModel):
    """OAuth configuration for an MCP server."""

    enabled: bool = Field(default=True, description="Whether OAuth token injection is enabled")
    token_url: str = Field(default="", description="OAuth token endpoint URL")
    grant_type: Literal["client_credentials", "refresh_token"] = Field(default="client_credentials", description="OAuth grant type")
    client_id: str | None = Field(default=None, description="OAuth client ID")
    client_secret: str | None = Field(default=None, description="OAuth client secret")
    refresh_token: str | None = Field(default=None, description="OAuth refresh token")
    scope: str | None = Field(default=None, description="OAuth scope")
    audience: str | None = Field(default=None, description="OAuth audience")
    token_field: str = Field(default="access_token", description="Token response field containing access token")
    token_type_field: str = Field(default="token_type", description="Token response field containing token type")
    expires_in_field: str = Field(default="expires_in", description="Token response field containing expires-in seconds")
    default_token_type: str = Field(default="Bearer", description="Default token type when response omits token_type")
    refresh_skew_seconds: int = Field(default=60, description="Refresh this many seconds before expiry")
    extra_token_params: dict[str, str] = Field(default_factory=dict, description="Additional form params sent to token endpoint")


class McpServerConfigResponse(BaseModel):
    """Response model for MCP server configuration."""

    enabled: bool = Field(default=True, description="Whether this MCP server is enabled")
    type: str = Field(default="stdio", description="Transport type: 'stdio', 'sse', or 'http'")
    command: str | None = Field(default=None, description="Command to execute to start the MCP server (for stdio type)")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the command (for stdio type)")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables for the MCP server")
    url: str | None = Field(default=None, description="URL of the MCP server (for sse or http type)")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers to send (for sse or http type)")
    oauth: McpOAuthConfigResponse | None = Field(default=None, description="OAuth configuration for MCP HTTP/SSE servers")
    description: str = Field(default="", description="Human-readable description of what this MCP server provides")


class McpConfigResponse(BaseModel):
    """Response model for MCP configuration."""

    mcp_servers: dict[str, McpServerConfigResponse] = Field(
        default_factory=dict,
        description="Map of MCP server name to configuration",
    )


class McpConfigUpdateRequest(BaseModel):
    """Request model for updating MCP configuration."""

    mcp_servers: dict[str, McpServerConfigResponse] = Field(
        ...,
        description="Map of MCP server name to configuration",
    )


@router.get(
    "/mcp/config",
    response_model=McpConfigResponse,
    summary="Get MCP Configuration",
    description="Retrieve the current Model Context Protocol (MCP) server configurations.",
)
async def get_mcp_configuration() -> McpConfigResponse:
    """Get the current MCP configuration.

    Returns:
        The current MCP configuration with all servers.

    Example:
        ```json
        {
            "mcp_servers": {
                "github": {
                    "enabled": true,
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "ghp_xxx"},
                    "description": "GitHub MCP server for repository operations"
                }
            }
        }
        ```
    """
    config = get_extensions_config()

    return McpConfigResponse(mcp_servers={name: McpServerConfigResponse(**server.model_dump()) for name, server in config.mcp_servers.items()})


@router.put(
    "/mcp/config",
    response_model=McpConfigResponse,
    summary="Update MCP Configuration",
    description="Update Model Context Protocol (MCP) server configurations and save to file.",
)
async def update_mcp_configuration(request: McpConfigUpdateRequest) -> McpConfigResponse:
    """Update the MCP configuration.

    This will:
    1. Save the new configuration to the mcp_config.json file
    2. Reload the configuration cache
    3. Reset MCP tools cache to trigger reinitialization

    Args:
        request: The new MCP configuration to save.

    Returns:
        The updated MCP configuration.

    Raises:
        HTTPException: 500 if the configuration file cannot be written.

    Example Request:
        ```json
        {
            "mcp_servers": {
                "github": {
                    "enabled": true,
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_TOKEN": "$GITHUB_TOKEN"},
                    "description": "GitHub MCP server for repository operations"
                }
            }
        }
        ```
    """
    try:
        # Get the current config path (or determine where to save it)
        config_path = ExtensionsConfig.resolve_config_path()

        # If no config file exists, create one in the parent directory (project root)
        if config_path is None:
            config_path = Path.cwd().parent / "extensions_config.json"
            logger.info(f"No existing extensions config found. Creating new config at: {config_path}")

        # Load current config to preserve skills configuration
        current_config = get_extensions_config()

        # Convert request to dict format for JSON serialization
        config_data = {
            "mcpServers": {name: server.model_dump() for name, server in request.mcp_servers.items()},
            "skills": {name: {"enabled": skill.enabled} for name, skill in current_config.skills.items()},
        }

        # Write the configuration to file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"MCP configuration updated and saved to: {config_path}")

        # NOTE: No need to reload/reset cache here - LangGraph Server (separate process)
        # will detect config file changes via mtime and reinitialize MCP tools automatically

        # Reload the configuration and update the global cache
        reloaded_config = reload_extensions_config()
        return McpConfigResponse(mcp_servers={name: McpServerConfigResponse(**server.model_dump()) for name, server in reloaded_config.mcp_servers.items()})

    except Exception as e:
        logger.error(f"Failed to update MCP configuration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update MCP configuration: {str(e)}")


class McpTestRequest(BaseModel):
    """Request model for testing an MCP server connection."""

    type: str = Field(default="stdio", description="Transport type: 'stdio', 'sse', or 'http'")
    command: str | None = Field(default=None, description="Command (for stdio type)")
    args: list[str] = Field(default_factory=list, description="Arguments (for stdio type)")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables (for stdio type)")
    url: str | None = Field(default=None, description="URL (for sse or http type)")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers (for sse or http type)")


class McpTestResponse(BaseModel):
    """Response model for MCP server connection test."""

    success: bool
    message: str


@router.post(
    "/mcp/test",
    response_model=McpTestResponse,
    summary="Test MCP Server Connection",
    description="Test whether an MCP server is reachable and can be started.",
)
async def test_mcp_server(request: McpTestRequest) -> McpTestResponse:
    """Test an MCP server connection.

    For stdio servers: checks if the command exists and can be launched.
    For sse/http servers: sends a HEAD/GET request to the URL.

    Returns:
        Test result with success status and message.
    """
    transport_type = request.type or "stdio"

    try:
        if transport_type == "stdio":
            if not request.command:
                return McpTestResponse(success=False, message="Command is required for stdio transport.")

            command = request.command
            if not shutil.which(command):
                return McpTestResponse(success=False, message=f"Command '{command}' not found in PATH.")

            try:
                env = {**os.environ, **request.env} if request.env else None
                proc = await asyncio.create_subprocess_exec(
                    command,
                    *request.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                try:
                    await asyncio.wait_for(proc.communicate(input=b""), timeout=5.0)
                except TimeoutError:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=3.0)
                    except TimeoutError:
                        proc.kill()

                return McpTestResponse(success=True, message=f"Command '{command}' launched successfully.")
            except FileNotFoundError:
                return McpTestResponse(success=False, message=f"Command '{command}' not found.")
            except PermissionError:
                return McpTestResponse(success=False, message=f"Permission denied when running '{command}'.")
            except Exception as e:
                return McpTestResponse(success=False, message=f"Failed to launch command: {str(e)}")

        elif transport_type in ("sse", "http"):
            if not request.url:
                return McpTestResponse(success=False, message="URL is required for sse/http transport.")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        request.url,
                        headers=request.headers or {},
                    )
                    return McpTestResponse(
                        success=True,
                        message=f"Server responded with status {response.status_code}.",
                    )
            except httpx.ConnectError:
                return McpTestResponse(success=False, message=f"Cannot connect to {request.url}.")
            except httpx.TimeoutException:
                return McpTestResponse(success=False, message=f"Connection to {request.url} timed out.")
            except Exception as e:
                return McpTestResponse(success=False, message=f"Connection failed: {str(e)}")

        else:
            return McpTestResponse(success=False, message=f"Unsupported transport type: {transport_type}")

    except Exception as e:
        logger.error(f"MCP test failed: {e}", exc_info=True)
        return McpTestResponse(success=False, message=f"Test failed: {str(e)}")
