from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp = FastMCP("HelloWorld Server")

# Define a resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name} from MCP!"

# Define a tool
@mcp.tool()
def reverse_text(text: str) -> str:
    return text[::-1]

if __name__ == "__main__":
    mcp.run()
