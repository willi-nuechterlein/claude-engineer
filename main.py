import os
from anthropic import Anthropic
from datetime import datetime
import json
from colorama import init, Fore, Style
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
import pygments.util
from dotenv import load_dotenv

# Initialize colorama
init()

# Load environment variables from .env file
load_dotenv()
anth_api_key = os.getenv('ANTHROPIC_KEY')

# Color constants
USER_COLOR = Fore.WHITE
CLAUDE_COLOR = Fore.BLUE
TOOL_COLOR = Fore.YELLOW
RESULT_COLOR = Fore.GREEN

# Initialize the Anthropic client
client = Anthropic(api_key=anth_api_key)

# Set up the conversation memory
conversation_history = []

# Global variable to store the working directory
WORKING_DIR = ""

# System prompt
system_prompt = """
You are Claude, an AI assistant powered by Anthropic's Claude-3.5-Sonnet model. You are an exceptional software developer with vast knowledge across multiple programming languages, frameworks, and best practices. Your capabilities include:

1. Creating project structures, including folders and files within the specified working directory
2. Writing clean, efficient, and well-documented code
3. Debugging complex issues and providing detailed explanations
4. Offering architectural insights and design patterns
5. Staying up-to-date with the latest technologies and industry trends
6. Reading and analyzing existing files in the specified working directory
7. Listing files in the specified working directory

When asked to create a project:
- Always create new folders and files within the specified working directory.
- Organize the project structure logically and follow best practices for the specific type of project being created.
- Use the provided tools to create folders and files as needed.

When asked to make edits or improvements:
- Use the read_file tool to examine the contents of existing files within the working directory.
- Analyze the code and suggest improvements or make necessary edits.
- Use the write_to_file tool to implement changes.

Be sure to consider the type of project (e.g., Python, JavaScript, web application) when determining the appropriate structure and files to include.

You can now read files and list the contents of the specified working directory. Use these capabilities when:
- The user asks for edits or improvements to existing files
- You need to understand the current state of the project
- You believe reading a file or listing directory contents will be beneficial to accomplish the user's goal

Always strive to provide the most accurate, helpful, and detailed responses possible. If you're unsure about something, admit it.

Remember that all operations are restricted to the specified working directory and its subdirectories.

Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within \\<thinking>\\</thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.
"""

# Helper function to print colored text
def print_colored(text, color):
    print(f"{color}{text}{Style.RESET_ALL}")

# Helper function to format and print code
def print_code(code, language):
    try:
        lexer = get_lexer_by_name(language, stripall=True)
        formatted_code = highlight(code, lexer, TerminalFormatter())
        print(formatted_code)
    except pygments.util.ClassNotFound:
        # If the language is not recognized, fall back to plain text
        print_colored(f"Code (language: {language}):\n{code}", CLAUDE_COLOR)

# Function to create a folder
def create_folder(path):
    full_path = os.path.join(WORKING_DIR, path)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

# Function to create a file
def create_file(path, content=""):
    full_path = os.path.join(WORKING_DIR, path)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

# Function to write to a file
def write_to_file(path, content):
    full_path = os.path.join(WORKING_DIR, path)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Content written to file: {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

# Function to read a file
def read_file(path):
    full_path = os.path.join(WORKING_DIR, path)
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

# Function to list files in the working directory
def list_files(path="."):
    full_path = os.path.join(WORKING_DIR, path)
    try:
        files = os.listdir(full_path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

# Define the tools
tools = [
    {
        "name": "create_folder",
        "description": "Create a new folder at the specified path within the working directory. Use this when you need to create a new directory in the project structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the folder should be created, relative to the working directory"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file at the specified path with optional content within the working directory. Use this when you need to create a new file in the project structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the file should be created, relative to the working directory"
                },
                "content": {
                    "type": "string",
                    "description": "The initial content of the file (optional)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_to_file",
        "description": "Write content to an existing file at the specified path within the working directory. Use this when you need to add or update content in an existing file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to write to, relative to the working directory"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the specified path within the working directory. Use this when you need to examine the contents of an existing file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to read, relative to the working directory"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files and directories in the specified path within the working directory. Use this when you need to see the contents of a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the folder to list, relative to the working directory (default: current directory)"
                }
            }
        }
    },
]

# Function to execute tools
def execute_tool(tool_name, tool_input):
    if tool_name == "create_folder":
        return create_folder(tool_input["path"])
    elif tool_name == "create_file":
        return create_file(tool_input["path"], tool_input.get("content", ""))
    elif tool_name == "write_to_file":
        return write_to_file(tool_input["path"], tool_input["content"])
    elif tool_name == "read_file":
        return read_file(tool_input["path"])
    elif tool_name == "list_files":
        return list_files(tool_input.get("path", "."))
    else:
        return f"Unknown tool: {tool_name}"

# Function to send a message to Claude and get the response
def chat_with_claude(user_input):
    global conversation_history
    
    # Add user input to conversation history
    conversation_history.append({"role": "user", "content": user_input})
    
    # Prepare the messages for the API call
    messages = conversation_history.copy()
    
    # Make the initial API call
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4000,
        system=system_prompt,
        messages=messages,
        tools=tools,
        tool_choice={"type": "auto"}
    )
    
    assistant_response = ""
    
    # Process the response
    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text
            print_colored(f"\nClaude: {content_block.text}", CLAUDE_COLOR)
        elif content_block.type == "tool_use":
            tool_name = content_block.name
            tool_input = content_block.input
            tool_use_id = content_block.id
            
            print_colored(f"\nTool Used: {tool_name}", TOOL_COLOR)
            print_colored(f"Tool Input: {tool_input}", TOOL_COLOR)
            
            # Execute the tool
            result = execute_tool(tool_name, tool_input)
            
            print_colored(f"Tool Result: {result}", RESULT_COLOR)
            
            # Add tool use and result to conversation history
            conversation_history.append({"role": "assistant", "content": [content_block]})
            conversation_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result
                    }
                ]
            })
            
            # Make another API call with the updated conversation history
            tool_response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_prompt,
                messages=conversation_history,
                tools=tools,
                tool_choice={"type": "auto"}
            )
            
            # Process the tool response
            for tool_content_block in tool_response.content:
                if tool_content_block.type == "text":
                    assistant_response += tool_content_block.text
                    print_colored(f"\nClaude: {tool_content_block.text}", CLAUDE_COLOR)
    
    # Add final assistant response to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

# Function to get and validate the working directory
def get_working_directory():
    while True:
        path = input(f"{USER_COLOR}Please enter the file path you want to work on: {Style.RESET_ALL}")
        if os.path.exists(path) and os.path.isdir(path):
            return os.path.abspath(path)
        else:
            print_colored("Invalid path. Please enter a valid directory path.", Fore.RED)

# Main chat loop
def main():
    global WORKING_DIR
    
    print_colored("Welcome to the Claude-3.5-Sonnet Engineer Chat!", CLAUDE_COLOR)
    WORKING_DIR = get_working_directory()
    print_colored(f"Working directory set to: {WORKING_DIR}", CLAUDE_COLOR)
    print_colored("Type 'exit' to end the conversation.", CLAUDE_COLOR)
    
    while True:
        user_input = input(f"\n{USER_COLOR}You: {Style.RESET_ALL}")
        if user_input.lower() == 'exit':
            print_colored("Thank you for chatting. Goodbye!", CLAUDE_COLOR)
            break
        
        response = chat_with_claude(user_input)
        
        # Check if the response contains code and format it
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    print_colored(part, CLAUDE_COLOR)
                else:
                    lines = part.split('\n')
                    language = lines[0].strip() if lines else ""
                    code = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                    
                    if language and code:
                        print_code(code, language)
                    elif code:
                        # If no language is specified but there is code, print it as plain text
                        print_colored(f"Code:\n{code}", CLAUDE_COLOR)
                    else:
                        # If there's no code (empty block), just print the part as is
                        print_colored(part, CLAUDE_COLOR)

if __name__ == "__main__":
    main()