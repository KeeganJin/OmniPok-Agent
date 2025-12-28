"""HTTP tools for agents."""
import httpx
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Constants
JSON_CONTENT_TYPE = "application/json"


@tool
async def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP GET request.
    
    Args:
        url: The URL to request
        headers: Optional headers
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers or {},
            params=params or {},
            timeout=timeout
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith(JSON_CONTENT_TYPE) else None,
        }

# Set metadata after tool creation
http_get.metadata = {"required_permissions": ["http.get"]}


@tool
async def http_post(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP POST request.
    
    Args:
        url: The URL to request
        data: Optional form data
        json_data: Optional JSON data
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data=data,
            json=json_data,
            headers=headers or {},
            timeout=timeout
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith(JSON_CONTENT_TYPE) else None,
        }

# Set metadata after tool creation
http_post.metadata = {"required_permissions": ["http.post"]}


@tool
async def http_put(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP PUT request.
    
    Args:
        url: The URL to request
        data: Optional form data
        json_data: Optional JSON data
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            data=data,
            json=json_data,
            headers=headers or {},
            timeout=timeout
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get("content-type", "").startswith(JSON_CONTENT_TYPE) else None,
        }

# Set metadata after tool creation
http_put.metadata = {"required_permissions": ["http.put"]}


@tool
async def http_delete(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP DELETE request.
    
    Args:
        url: The URL to request
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url,
            headers=headers or {},
            timeout=timeout
        )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
        }

# Set metadata after tool creation
http_delete.metadata = {"required_permissions": ["http.delete"]}

