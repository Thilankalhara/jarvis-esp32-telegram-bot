import json
from openai import OpenAI
from pc_agent.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL
import pc_agent.config as _pcc
from pc_agent.tools import system_tools, file_tools, web_tools, dev_tools, doc_tools

class JarvisAgent:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        
        # Initialize OpenAI client targeting OpenRouter endpoint
        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=self.api_key if self.api_key else "dummy_key_until_set"
        )
        
        self.tools_schema = self._build_tools_schema()

    def _build_tools_schema(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Open or launch any desktop application by name (e.g. VS Code, Chrome, Word, Excel, Notepad, Calculator, Spotify, Command Prompt, PowerShell, Task Manager).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "Application name or command to launch"}
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Capture a live screenshot of the PC desktop and save it.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_info",
                    "description": "Get current PC system health metrics (CPU usage %, RAM used/total, Disk space, Battery status).",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "power_control",
                    "description": "Perform power actions on the PC: lock, sleep, shutdown, or restart.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["lock", "sleep", "shutdown", "restart"], "description": "Power action to execute"}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List files and subdirectories in a directory path.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string", "description": "Optional folder path, defaults to Desktop"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_content",
                    "description": "Read the text contents of a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "File path to read"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file_content",
                    "description": "Create or write content to a text file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Target file path"},
                            "content": {"type": "string", "description": "Text content to write"},
                            "append": {"type": "boolean", "description": "Append to file if true"}
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for files by name/keyword on the PC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query or file extension"},
                            "search_dir": {"type": "string", "description": "Directory to search within"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_terminal_command",
                    "description": "Run a terminal / PowerShell / CMD command on the PC and return standard output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command string to run"},
                            "working_dir": {"type": "string", "description": "Optional directory path"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_operation",
                    "description": "Execute Git repository operations (status, pull, clone, commit_push).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["status", "pull", "clone", "commit_push"]},
                            "repo_path": {"type": "string", "description": "Local repository directory"},
                            "repo_url": {"type": "string", "description": "Repository URL for clone"},
                            "message": {"type": "string", "description": "Commit message"}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for real-time information or answers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Web search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "download_file",
                    "description": "Download a file from a URL to the PC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Source URL"},
                            "filename": {"type": "string", "description": "Save filename"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_word_document",
                    "description": "Generate a formatted Microsoft Word (.docx) document assignment or report on the PC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Document title"},
                            "content_sections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "heading": {"type": "string"},
                                        "body": {"type": "string"}
                                    }
                                },
                                "description": "List of sections with headings and body text"
                            },
                            "output_filename": {"type": "string", "description": "Filename ending with .docx"}
                        },
                        "required": ["title", "content_sections"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_browser_url",
                    "description": "Open a website URL directly in the web browser on the PC screen.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Web URL to open"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_args: dict):
        """Map LLM tool call to actual Python implementation."""
        try:
            if tool_name == "open_application":
                return system_tools.open_application(tool_args.get("app_name"))
            elif tool_name == "take_screenshot":
                return system_tools.take_screenshot()
            elif tool_name == "get_system_info":
                return system_tools.get_system_info()
            elif tool_name == "power_control":
                return system_tools.power_control(tool_args.get("action"))
            elif tool_name == "list_directory":
                return file_tools.list_directory(tool_args.get("directory_path"))
            elif tool_name == "read_file_content":
                return file_tools.read_file_content(tool_args.get("file_path"))
            elif tool_name == "write_file_content":
                return file_tools.write_file_content(tool_args.get("file_path"), tool_args.get("content"), tool_args.get("append", False))
            elif tool_name == "search_files":
                return file_tools.search_files(tool_args.get("query"), tool_args.get("search_dir"))
            elif tool_name == "execute_terminal_command":
                return dev_tools.execute_terminal_command(tool_args.get("command"), tool_args.get("working_dir"))
            elif tool_name == "git_operation":
                return dev_tools.git_operation(tool_args.get("action"), tool_args.get("repo_path"), tool_args.get("repo_url"), tool_args.get("message", "JARVIS Update"))
            elif tool_name == "search_web":
                return web_tools.search_web(tool_args.get("query"))
            elif tool_name == "download_file":
                return web_tools.download_file(tool_args.get("url"), tool_args.get("filename"))
            elif tool_name == "create_word_document":
                return doc_tools.create_word_document(tool_args.get("title"), tool_args.get("content_sections"), tool_args.get("output_filename"))
            elif tool_name == "open_browser_url":
                return web_tools.open_browser_url(tool_args.get("url"))
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def process_command(self, user_prompt: str, allow_open: bool = True) -> dict:
        """Process user command via OpenRouter LLM and execute tools if requested."""
        # Always reload config dynamically to pick up any updated .env settings
        _pcc.reload_config()
        self.api_key = _pcc.OPENROUTER_API_KEY
        self.model = _pcc.OPENROUTER_MODEL
        if self.api_key:
            self.client.api_key = self.api_key
        try:
            self.client.base_url = _pcc.OPENROUTER_BASE_URL
        except Exception:
            pass

        if not self.api_key or self.api_key == "dummy_key_until_set":
            return {
                "text": "⚠️ OpenRouter API Key is not configured! Please click Settings and set your `OpenRouter API Key`."
            }

        user_name = _pcc.get_user_name()
        system_instruction = (
            f"You are J.A.R.V.I.S., a Tony Stark inspired personal AI assistant running on the user's home PC. "
            f"The user's name is '{user_name}' — ALWAYS address them as '{user_name}' in your replies. Never call them 'Sir' or 'User'. "
            "You have direct access to system control tools (open apps, power control, take screenshot, file management, "
            "git operations, web search, creating Word documents). "
            "Execute requested actions efficiently and reply concisely with a confident, helpful tone."
        )

        # If the caller explicitly disables opening applications, instruct the model not to claim
        # it opened or launched applications and to ask the user to use `/open <app> confirm` instead.
        if not allow_open:
            system_instruction += (
                " IMPORTANT: The ability to open or launch applications is currently disabled for this request. "
                "Do NOT claim you opened, launched, or started any application. If the user requested an app to be opened, "
                "respond by saying opening applications is disabled and instruct them to use `/open <app> confirm` to confirm."
            )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        candidate_models = [self.model, "google/gemini-2.0-flash-001", "openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct"]
        # Remove duplicates while preserving order
        models_to_try = []
        for m in candidate_models:
            if m and m not in models_to_try:
                models_to_try.append(m)

        last_exception = None
        for current_model in models_to_try:
            try:
                # Optionally disable the open_application tool to prevent accidental app launches
                tools_to_use = self.tools_schema
                if not allow_open:
                    try:
                        tools_to_use = [t for t in self.tools_schema if t.get('function', {}).get('name') != 'open_application']
                    except Exception:
                        tools_to_use = self.tools_schema

                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    tools=tools_to_use,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                media_attachment = None

                if tool_calls:
                    messages.append(response_message)

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Execute tool
                        tool_result = self.execute_tool(function_name, function_args)

                        # Announce completion via voice
                        from pc_agent.tools.system_tools import announce_tool_completion
                        announce_tool_completion(function_name, **function_args)

                        # If tool returned a screenshot file or doc path
                        if function_name == "take_screenshot" and isinstance(tool_result, str) and tool_result.endswith(".png"):
                            media_attachment = {"type": "photo", "path": tool_result}
                        elif function_name == "create_word_document" and isinstance(tool_result, str) and tool_result.endswith(".docx"):
                            media_attachment = {"type": "document", "path": tool_result}

                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
                        })

                    # Follow-up completion with tool results
                    second_response = self.client.chat.completions.create(
                        model=current_model,
                        messages=messages,
                    )
                    final_text = second_response.choices[0].message.content
                else:
                    final_text = response_message.content

                return {
                    "text": final_text or "Task executed successfully, sir.",
                    "media": media_attachment
                }

            except Exception as e:
                last_exception = e
                print(f"[JARVIS Agent] Model '{current_model}' failed: {e}. Trying fallback model...")
                continue

        return {
            "text": f"An error occurred while contacting J.A.R.V.I.S brain (OpenRouter): {str(last_exception)}"
        }
