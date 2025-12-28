"""HTTP tools for agents."""
import httpx
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Constants
JSON_CONTENT_TYPE = "application/json"


@tool(metadata={"required_permissions": ["http.get"]})
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


@tool(metadata={"required_permissions": ["http.post"]})
async def http_post(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP POST request.
    
    Args:
        url: The URL to request
        data: Optional form data
        json: Optional JSON data
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data=data,
            json=json,
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


@tool(metadata={"required_permissions": ["http.put"]})
async def http_put(
    url: str,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make an HTTP PUT request.
    
    Args:
        url: The URL to request
        data: Optional form data
        json: Optional JSON data
        headers: Optional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary
    """
    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            data=data,
            json=json,
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


@tool(metadata={"required_permissions": ["http.delete"]})
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

