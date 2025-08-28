# # # app/services/agent_builder.py
# # """
# # Dynamic agent builder service
# # """
# # import os
# # import logging
# # from typing import Dict, Any, List, Optional, Callable
# # from strands import Agent, tool, models
# # from strands.models import BedrockModel
# # from strands_tools import current_time
# # from strands.tools.mcp import MCPClient
# # from mcp import stdio_client, StdioServerParameters
# # from app.models.agent import ModelConfig, MCPServerConfig, ToolConfig

# # logger = logging.getLogger(__name__)

# # class DynamicAgentBuilder:
# #     def __init__(self):
# #         self.mcp_connections: Dict[str, Any] = {}
# #         self.custom_tools: Dict[str, Callable] = {}
        
# #     def create_model(self, config: ModelConfig) -> models:
# #         """Create appropriate model based on provider"""
        
# #         if config.provider == "bedrock":
# #             # Ensure AWS credentials are available
# #             aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
# #             aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# #             aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            
# #             if not aws_access_key or not aws_secret_key:
# #                 logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
# #                 raise ValueError("AWS credentials not configured")
            
# #             client_config = config.client_config.copy() if config.client_config else {}
            
# #             # Ensure region is set
# #             if 'region_name' not in client_config:
# #                 client_config['region_name'] = aws_region
                
# #             logger.info(f"Creating Bedrock model in region: {client_config.get('region_name', 'us-east-1')}")
            
# #             return BedrockModel(
# #                 model_id=config.model_id,
# #                 temperature=config.temperature,
# #                 max_tokens=config.max_tokens,
# #                 client_config=client_config
# #             )
            
# #         elif config.provider == "perplexity":
# #             api_key = os.getenv(config.api_key_env or "PERPLEXITY_API_KEY")
# #             return self._create_perplexity_model(config, api_key)
            
# #         else:
# #             raise ValueError(f"Unsupported model provider: {config.provider}")
    
# #     def _create_perplexity_model(self, config: ModelConfig, api_key: str):
# #         """Create Perplexity model (using OpenAI-compatible interface)"""
# #         try:
# #             from openai import OpenAI
# #         except ImportError:
# #             logger.error("OpenAI package not installed for Perplexity model")
# #             raise ImportError("Please install openai package: pip install openai")
        
# #         class PerplexityModel(models):
# #             def __init__(self, model_id, api_key, **kwargs):
# #                 self.client = OpenAI(
# #                     api_key=api_key,
# #                     base_url="https://api.perplexity.ai"
# #                 )
# #                 self.model_id = model_id
# #                 self.kwargs = kwargs
                
# #             def __call__(self, prompt: str) -> str:
# #                 try:
# #                     response = self.client.chat.completions.create(
# #                         model=self.model_id,
# #                         messages=[{"role": "user", "content": prompt}],
# #                         **self.kwargs
# #                     )
# #                     return response.choices[0].message.content
# #                 except Exception as e:
# #                     logger.error(f"Perplexity API call failed: {str(e)}")
# #                     raise
        
# #         return PerplexityModel(
# #             model_id=config.model_id,
# #             api_key=api_key,
# #             temperature=config.temperature,
# #             max_tokens=config.max_tokens
# #         )
    
# #     async def setup_mcp_servers(self, mcp_configs: List[MCPServerConfig]) -> List[Any]:
# #         """Setup MCP servers and return available tools"""
# #         all_tools = []
        
# #         for mcp_config in mcp_configs:
# #             if not mcp_config.enabled:
# #                 logger.info(f"Skipping disabled MCP server: {mcp_config.server_name}")
# #                 continue
                
# #             try:
# #                 print("MCP CONFIGS",mcp_config)
# #                 # Prepare args - start with default args
# #                 args = mcp_config.args.copy() if mcp_config.args else []
                
# #                 # Handle different server types
# #                 if mcp_config.server_name == "sap-abap-adt":
# #                     # For SAP ABAP ADT server, we need to find the Node.js file
# #                     if mcp_config.auto_detect_path and hasattr(mcp_config, 'possible_locations'):
# #                         server_path = self._find_mcp_server(mcp_config)
# #                         if not server_path:
# #                             logger.warning(f"SAP ABAP ADT server not found at any location: {mcp_config.possible_locations}")
# #                             continue
# #                         # For node command, the script path is the first argument
# #                         args = [server_path] + args
# #                         logger.info(f"Found SAP ABAP ADT server at: {server_path}")
# #                     else:
# #                         logger.warning(f"SAP ABAP ADT server: auto_detect_path is disabled or no possible_locations defined")
# #                         continue
                
# #                 elif mcp_config.server_name == "perplexity-research":
# #                     # For Docker-based servers, no file path needed - just use the provided args
# #                     logger.info(f"Setting up Docker-based Perplexity server with args: {args}")
                    
# #                     # Check if Docker is available
# #                     try:
# #                         import subprocess
# #                         result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
# #                         if result.returncode != 0:
# #                             logger.error("Docker is not available or not running")
# #                             continue
# #                     except Exception as docker_check_error:
# #                         logger.error(f"Failed to check Docker availability: {str(docker_check_error)}")
# #                         continue
                
# #                 logger.info(f"Setting up MCP server {mcp_config.server_name} with command: {mcp_config.command}, args: {args}")
                
# #                 # Create MCP connection
# #                 if mcp_config.server_type == "stdio":
# #                     def create_connection():
# #                         env_vars = {}
# #                         if hasattr(mcp_config, 'env_vars') and mcp_config.env_vars:
# #                             env_vars = mcp_config.env_vars
                        
# #                         return stdio_client(
# #                             StdioServerParameters(
# #                                 command=mcp_config.command,
# #                                 args=args,
# #                                 env={**os.environ, **env_vars}
# #                             )
# #                         )
                    
# #                     mcp_client = MCPClient(create_connection)
                    
# #                     # Try to get available tools
# #                     try:
# #                         with mcp_client as client:
# #                             tools = client.list_tools_sync()
# #                             if tools:
# #                                 all_tools.extend(tools)
# #                                 logger.info(f"Connected to MCP server {mcp_config.server_name}: {len(tools)} tools available")
# #                             else:
# #                                 logger.warning(f"MCP server {mcp_config.server_name} connected but no tools available")
                        
# #                         # Store connection for later use
# #                         self.mcp_connections[mcp_config.server_name] = mcp_client
                        
# #                     except Exception as tool_error:
# #                         logger.error(f"Failed to get tools from MCP server {mcp_config.server_name}: {str(tool_error)}")
# #                         continue
                    
# #             except Exception as e:
# #                 logger.error(f"Failed to setup MCP server {mcp_config.server_name}: {str(e)}")
# #                 logger.debug(f"MCP server config: {mcp_config}")
# #                 continue
                
# #         logger.info(f"Total MCP tools loaded: {len(all_tools)}")
# #         return all_tools
    
# #     def _find_mcp_server(self, config: MCPServerConfig) -> Optional[str]:
# #         """Auto-detect MCP server path"""
# #         if not hasattr(config, 'possible_locations') or not config.possible_locations:
# #             logger.warning(f"No possible locations defined for MCP server {config.server_name}")
# #             return None
            
# #         for location in config.possible_locations:
# #             expanded_path = os.path.expanduser(location)
# #             logger.debug(f"Checking MCP server path: {expanded_path}")
# #             if os.path.exists(expanded_path):
# #                 logger.info(f"Found MCP server at: {expanded_path}")
# #                 return expanded_path
                
# #         return None
    
# #     def create_custom_tool(self, tool_config: ToolConfig) -> Callable:
# #         """Create custom tool from configuration"""
# #         if tool_config.code:
# #             try:
# #                 # Dynamic tool creation from code
# #                 namespace = {'tool': tool}  # Make tool decorator available
# #                 exec(tool_config.code, namespace)
                
# #                 # Find the tool function
# #                 for name, obj in namespace.items():
# #                     if callable(obj) and hasattr(obj, '__tool__'):
# #                         logger.info(f"Created custom tool: {tool_config.tool_name}")
# #                         return obj
# #             except Exception as e:
# #                 logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
                    
# #         # Return a placeholder tool if creation fails
# #         @tool
# #         def custom_tool(**kwargs):
# #             """Custom tool placeholder"""
# #             return f"Executing {tool_config.tool_name} with params: {kwargs}"
        
# #         return custom_tool
    
# #     def get_builtin_tools(self, tool_names: List[str]) -> List[Callable]:
# #         """Get built-in Strands tools"""
# #         builtin_tools = {
# #             "current_time": current_time,
# #             # Add more built-in tools as needed
# #         }
        
# #         tools = []
# #         for name in tool_names:
# #             if name in builtin_tools:
# #                 tools.append(builtin_tools[name])
# #                 logger.info(f"Added built-in tool: {name}")
# #             else:
# #                 logger.warning(f"Built-in tool not found: {name}")
        
# #         return tools
    
# #     async def build_agent(self, config) -> Agent:
# #         """Build a complete Strands agent from configuration"""
        
# #         try:
# #             logger.info("Starting agent build process...")

# #             # Handle both field names: model_config or agent_model_config
# #             model_config = None
# #             if hasattr(config, 'agent_model_config'):
# #                 model_config = config.agent_model_config
# #             elif hasattr(config, 'model_config'):
# #                 model_config = config.model_config
# #             else:
# #                 raise ValueError("No model configuration found in agent config")
            
# #             # Create model
# #             logger.info(f"Creating model with provider: {model_config.provider}")
# #             model = self.create_model(model_config)
            
# #             # Setup MCP servers and get tools
# #             logger.info("Setting up MCP servers...")
# #             mcp_tools = []
# #             if hasattr(config, 'mcp_servers') and config.mcp_servers:
# #                 try:
# #                     mcp_tools = await self.setup_mcp_servers(config.mcp_servers)
# #                 except Exception as e:
# #                     logger.error(f"MCP server setup failed: {str(e)}")
# #                     # Continue without MCP tools
            
# #             # Get custom tools
# #             logger.info("Creating custom tools...")
# #             custom_tools = []
# #             if hasattr(config, 'tools') and config.tools:
# #                 for tool_config in config.tools:
# #                     if tool_config.enabled and tool_config.tool_type == "custom":
# #                         try:
# #                             custom_tool = self.create_custom_tool(tool_config)
# #                             if custom_tool:
# #                                 custom_tools.append(custom_tool)
# #                         except Exception as e:
# #                             logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
            
# #             # Get built-in tools
# #             logger.info("Adding built-in tools...")
# #             builtin_tools = []
# #             if hasattr(config, 'builtin_tools') and config.builtin_tools:
# #                 builtin_tools = self.get_builtin_tools(config.builtin_tools)
            
# #             # Combine all tools
# #             all_tools = builtin_tools + mcp_tools + custom_tools
# #             logger.info(f"Total tools available: {len(all_tools)}")
            
# #             # Create agent
# #             logger.info("Creating agent...")
# #             agent = Agent(
# #                 model=model,
# #                 tools=all_tools if all_tools else [],
# #                 system_prompt=config.system_prompt if hasattr(config, 'system_prompt') else "You are a helpful assistant"
# #             )
            
# #             logger.info("Agent successfully built")
# #             return agent
            
# #         except Exception as e:
# #             logger.error(f"Failed to build agent: {str(e)}", exc_info=True)
# #             raise


# # app/services/agent_builder.py
# """
# Dynamic agent builder service - Fixed MCP server handling
# """
# import os
# import logging
# from typing import Dict, Any, List, Optional, Callable
# from strands import Agent, tool, models
# from strands.models import BedrockModel
# from strands_tools import current_time
# from strands.tools.mcp import MCPClient
# from mcp import stdio_client, StdioServerParameters
# from app.models.agent import ModelConfig, MCPServerConfig, ToolConfig

# logger = logging.getLogger(__name__)

# class DynamicAgentBuilder:
#     def __init__(self):
#         self.mcp_connections: Dict[str, Any] = {}
#         self.custom_tools: Dict[str, Callable] = {}
        
#     def create_model(self, config: ModelConfig) -> models:
#         """Create appropriate model based on provider"""
        
#         if config.provider == "bedrock":
#             # Ensure AWS credentials are available
#             aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
#             aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
#             aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            
#             if not aws_access_key or not aws_secret_key:
#                 logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
#                 raise ValueError("AWS credentials not configured")
            
#             client_config = config.client_config.copy() if config.client_config else {}
            
#             # Ensure region is set
#             if 'region_name' not in client_config:
#                 client_config['region_name'] = aws_region
                
#             logger.info(f"Creating Bedrock model in region: {client_config.get('region_name', 'us-east-1')}")
            
#             return BedrockModel(
#                 model_id=config.model_id,
#                 temperature=config.temperature,
#                 max_tokens=config.max_tokens,
#                 client_config=client_config
#             )
            
#         elif config.provider == "perplexity":
#             api_key = os.getenv(config.api_key_env or "PERPLEXITY_API_KEY")
#             return self._create_perplexity_model(config, api_key)
            
#         else:
#             raise ValueError(f"Unsupported model provider: {config.provider}")
    
#     def _create_perplexity_model(self, config: ModelConfig, api_key: str):
#         """Create Perplexity model (using OpenAI-compatible interface)"""
#         try:
#             from openai import OpenAI
#         except ImportError:
#             logger.error("OpenAI package not installed for Perplexity model")
#             raise ImportError("Please install openai package: pip install openai")
        
#         class PerplexityModel(models):
#             def __init__(self, model_id, api_key, **kwargs):
#                 self.client = OpenAI(
#                     api_key=api_key,
#                     base_url="https://api.perplexity.ai"
#                 )
#                 self.model_id = model_id
#                 self.kwargs = kwargs
                
#             def __call__(self, prompt: str) -> str:
#                 try:
#                     response = self.client.chat.completions.create(
#                         model=self.model_id,
#                         messages=[{"role": "user", "content": prompt}],
#                         **self.kwargs
#                     )
#                     return response.choices[0].message.content
#                 except Exception as e:
#                     logger.error(f"Perplexity API call failed: {str(e)}")
#                     raise
        
#         return PerplexityModel(
#             model_id=config.model_id,
#             api_key=api_key,
#             temperature=config.temperature,
#             max_tokens=config.max_tokens
#         )
    
#     async def setup_mcp_servers(self, mcp_configs: List[MCPServerConfig]) -> List[Any]:
#         """Setup MCP servers and return available tools"""
#         all_tools = []
        
#         for mcp_config in mcp_configs:
#             if not mcp_config.enabled:
#                 logger.info(f"Skipping disabled MCP server: {mcp_config.server_name}")
#                 continue
                
#             try:
#                 logger.info(f"Setting up MCP server: {mcp_config.server_name}")
                
#                 # Initialize args with default args from config
#                 args = mcp_config.args.copy() if mcp_config.args else []
                
#                 # Handle specific server types
#                 if mcp_config.server_name in ["sap-abap-adt", "abap-adt-api"]:
#                     # For SAP ABAP ADT server, we need to find the Node.js file
#                     if mcp_config.auto_detect_path and hasattr(mcp_config, 'possible_locations'):
#                         server_path = self._find_mcp_server(mcp_config)
#                         if not server_path:
#                             logger.warning(f"SAP ABAP ADT server not found at any location")
#                             for location in mcp_config.possible_locations:
#                                 logger.warning(f"  Checked: {location}")
#                             continue
                        
#                         # For node command, the script path should be the first argument
#                         args = [server_path] + args
#                         logger.info(f"Found SAP ABAP ADT server at: {server_path}")
#                         logger.info(f"Command will be: {mcp_config.command} {' '.join(args)}")
#                     else:
#                         logger.warning(f"SAP ABAP ADT server: auto_detect_path is disabled or no possible_locations defined")
#                         continue
                
#                 elif mcp_config.server_name == "perplexity-research":
#                     # For Docker-based servers, args are already set correctly
#                     logger.info(f"Setting up Docker-based Perplexity server")
                    
#                     # Verify Docker is available
#                     try:
#                         import subprocess
#                         result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
#                         if result.returncode != 0:
#                             logger.error("Docker is not available or not running")
#                             continue
#                     except Exception as docker_check_error:
#                         logger.error(f"Failed to check Docker availability: {str(docker_check_error)}")
#                         continue
                
#                 else:
#                     # For other server types, use the provided args as-is
#                     logger.info(f"Setting up generic MCP server: {mcp_config.server_name}")
                
#                 logger.info(f"Final MCP server command: {mcp_config.command} {' '.join(args)}")
                
#                 # Create MCP connection
#                 if mcp_config.server_type == "stdio":
#                     def create_connection():
#                         # Prepare environment variables
#                         env_vars = {**os.environ}
#                         if hasattr(mcp_config, 'env_vars') and mcp_config.env_vars:
#                             env_vars.update(mcp_config.env_vars)
                        
#                         return stdio_client(
#                             StdioServerParameters(
#                                 command=mcp_config.command,
#                                 args=args,
#                                 env=env_vars
#                             )
#                         )
                    
#                     mcp_client = MCPClient(create_connection)
                    
#                     # Test the connection and get tools
#                     try:
#                         with mcp_client as client:
#                             tools = client.list_tools_sync()
#                             if tools:
#                                 all_tools.extend(tools)
#                                 logger.info(f"Successfully connected to {mcp_config.server_name}: {len(tools)} tools available")
                                
#                                 # Log tool names for debugging
#                                 tool_names = [getattr(tool, 'name', str(tool)) for tool in tools[:5]]  # First 5 tools
#                                 logger.info(f"Sample tools from {mcp_config.server_name}: {tool_names}")
#                             else:
#                                 logger.warning(f"MCP server {mcp_config.server_name} connected but no tools available")
                        
#                         # Store connection for later use
#                         self.mcp_connections[mcp_config.server_name] = mcp_client
                        
#                     except Exception as tool_error:
#                         logger.error(f"Failed to get tools from MCP server {mcp_config.server_name}: {str(tool_error)}")
#                         # Log more details for debugging
#                         logger.debug(f"Command attempted: {mcp_config.command} {' '.join(args)}")
#                         continue
                    
#             except Exception as e:
#                 logger.error(f"Failed to setup MCP server {mcp_config.server_name}: {str(e)}")
#                 logger.debug(f"MCP server config details: command={mcp_config.command}, args={args}")
#                 continue
                
#         logger.info(f"Total MCP tools loaded from all servers: {len(all_tools)}")
#         return all_tools
    
#     def _find_mcp_server(self, config: MCPServerConfig) -> Optional[str]:
#         """Auto-detect MCP server path"""
#         if not hasattr(config, 'possible_locations') or not config.possible_locations:
#             logger.warning(f"No possible locations defined for MCP server {config.server_name}")
#             return None
            
#         for location in config.possible_locations:
#             expanded_path = os.path.expanduser(location)
#             logger.debug(f"Checking MCP server path: {expanded_path}")
#             if os.path.exists(expanded_path):
#                 logger.info(f"Found MCP server at: {expanded_path}")
#                 return expanded_path
        
#         logger.error(f"MCP server not found at any of the possible locations for {config.server_name}")
#         return None
    
#     def create_custom_tool(self, tool_config: ToolConfig) -> Callable:
#         """Create custom tool from configuration"""
#         if tool_config.code:
#             try:
#                 # Dynamic tool creation from code
#                 namespace = {'tool': tool}  # Make tool decorator available
#                 exec(tool_config.code, namespace)
                
#                 # Find the tool function
#                 for name, obj in namespace.items():
#                     if callable(obj) and hasattr(obj, '__tool__'):
#                         logger.info(f"Created custom tool: {tool_config.tool_name}")
#                         return obj
#             except Exception as e:
#                 logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
                    
#         # Return a placeholder tool if creation fails
#         @tool
#         def custom_tool(**kwargs):
#             """Custom tool placeholder"""
#             return f"Executing {tool_config.tool_name} with params: {kwargs}"
        
#         return custom_tool
    
#     def get_builtin_tools(self, tool_names: List[str]) -> List[Callable]:
#         """Get built-in Strands tools"""
#         builtin_tools = {
#             "current_time": current_time,
#             # Add more built-in tools as needed
#         }
        
#         tools = []
#         for name in tool_names:
#             if name in builtin_tools:
#                 tools.append(builtin_tools[name])
#                 logger.info(f"Added built-in tool: {name}")
#             else:
#                 logger.warning(f"Built-in tool not found: {name}")
        
#         return tools
    
#     async def build_agent(self, config) -> Agent:
#         """Build a complete Strands agent from configuration"""
        
#         try:
#             logger.info("Starting agent build process...")

#             # Handle both field names: model_config or agent_model_config
#             model_config = None
#             if hasattr(config, 'agent_model_config'):
#                 model_config = config.agent_model_config
#             elif hasattr(config, 'model_config'):
#                 model_config = config.model_config
#             else:
#                 raise ValueError("No model configuration found in agent config")
            
#             # Create model
#             logger.info(f"Creating model with provider: {model_config.provider}")
#             model = self.create_model(model_config)
            
#             # Setup MCP servers and get tools
#             logger.info("Setting up MCP servers...")
#             mcp_tools = []
#             if hasattr(config, 'mcp_servers') and config.mcp_servers:
#                 try:
#                     mcp_tools = await self.setup_mcp_servers(config.mcp_servers)
#                 except Exception as e:
#                     logger.error(f"MCP server setup failed: {str(e)}")
#                     # Continue without MCP tools
            
#             # Get custom tools
#             logger.info("Creating custom tools...")
#             custom_tools = []
#             if hasattr(config, 'tools') and config.tools:
#                 for tool_config in config.tools:
#                     if tool_config.enabled and tool_config.tool_type == "custom":
#                         try:
#                             custom_tool = self.create_custom_tool(tool_config)
#                             if custom_tool:
#                                 custom_tools.append(custom_tool)
#                         except Exception as e:
#                             logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
            
#             # Get built-in tools
#             logger.info("Adding built-in tools...")
#             builtin_tools = []
#             if hasattr(config, 'builtin_tools') and config.builtin_tools:
#                 builtin_tools = self.get_builtin_tools(config.builtin_tools)
            
#             # Combine all tools
#             all_tools = builtin_tools + mcp_tools + custom_tools
#             logger.info(f"Total tools available: {len(all_tools)}")
#             logger.info(f"  - Built-in tools: {len(builtin_tools)}")
#             logger.info(f"  - MCP tools: {len(mcp_tools)}")
#             logger.info(f"  - Custom tools: {len(custom_tools)}")
            
#             # Create agent
#             logger.info("Creating agent...")
#             agent = Agent(
#                 model=model,
#                 tools=all_tools if all_tools else [],
#                 system_prompt=config.system_prompt if hasattr(config, 'system_prompt') else "You are a helpful assistant"
#             )
            
#             logger.info("Agent successfully built")
#             return agent
            
#         except Exception as e:
#             logger.error(f"Failed to build agent: {str(e)}", exc_info=True)
#             raise

# # app/services/agent_builder.py
# """
# Dynamic agent builder service with proper MCP context management
# """
# import os
# import logging
# from typing import Dict, Any, List, Optional, Callable
# from contextlib import asynccontextmanager
# from strands import Agent, tool, models
# from strands.models import BedrockModel
# from strands_tools import current_time
# from strands.tools.mcp import MCPClient
# from mcp import stdio_client, StdioServerParameters
# from app.models.agent import ModelConfig, MCPServerConfig, ToolConfig

# logger = logging.getLogger(__name__)

# class DynamicAgentBuilder:
#     def __init__(self):
#         self.mcp_connections: Dict[str, Any] = {}
#         self.custom_tools: Dict[str, Callable] = {}
        
#     def create_model(self, config: ModelConfig) -> models:
#         """Create appropriate model based on provider"""
        
#         if config.provider == "bedrock":
#             return BedrockModel(
#                 model_id=config.model_id,
#                 temperature=config.temperature,
#                 max_tokens=config.max_tokens,
#                 client_config=config.client_config if config.client_config else {}
#             )
            
#         elif config.provider == "perplexity":
#             api_key = os.getenv(config.api_key_env or "PERPLEXITY_API_KEY")
#             return self._create_perplexity_model(config, api_key)
            
#         else:
#             raise ValueError(f"Unsupported model provider: {config.provider}")
    
#     def _create_perplexity_model(self, config: ModelConfig, api_key: str):
#         """Create Perplexity model (using OpenAI-compatible interface)"""
#         try:
#             from openai import OpenAI
#         except ImportError:
#             logger.error("OpenAI package not installed for Perplexity model")
#             raise ImportError("Please install openai package: pip install openai")
        
#         class PerplexityModel(models):
#             def __init__(self, model_id, api_key, **kwargs):
#                 self.client = OpenAI(
#                     api_key=api_key,
#                     base_url="https://api.perplexity.ai"
#                 )
#                 self.model_id = model_id
#                 self.kwargs = kwargs
                
#             def __call__(self, prompt: str) -> str:
#                 try:
#                     response = self.client.chat.completions.create(
#                         model=self.model_id,
#                         messages=[{"role": "user", "content": prompt}],
#                         **self.kwargs
#                     )
#                     return response.choices[0].message.content
#                 except Exception as e:
#                     logger.error(f"Perplexity API call failed: {str(e)}")
#                     raise
        
#         return PerplexityModel(
#             model_id=config.model_id,
#             api_key=api_key,
#             temperature=config.temperature,
#             max_tokens=config.max_tokens
#         )
    
#     async def setup_mcp_servers(self, mcp_configs: List[MCPServerConfig]) -> List[Any]:
#         """Setup MCP servers and return available tools"""
#         all_tools = []
        
#         for mcp_config in mcp_configs:
#             if not mcp_config.enabled:
#                 continue
                
#             try:
#                 # Auto-detect server path if needed
#                 if mcp_config.auto_detect_path:
#                     server_path = self._find_mcp_server(mcp_config)
#                     if not server_path:
#                         logger.warning(f"MCP server {mcp_config.server_name} not found at any location")
#                         continue
                    
#                     # Update the command arguments
#                     if mcp_config.server_name == "sap-abap-adt":
#                         mcp_config.command = "node"
#                         mcp_config.args = [server_path]
#                         logger.info(f"Found SAP ABAP ADT server at: {server_path}")
#                         logger.info(f"Command will be: {mcp_config.command} {' '.join(mcp_config.args)}")
#                         logger.info(f"Final MCP server command: {mcp_config.command} {' '.join(mcp_config.args)}")
                
#                 # Create MCP connection function
#                 if mcp_config.server_type == "stdio":
#                     def create_connection():
#                         return stdio_client(
#                             StdioServerParameters(
#                                 command=mcp_config.command,
#                                 args=mcp_config.args,
#                                 env={**os.environ, **mcp_config.env_vars}
#                             )
#                         )
                    
#                     mcp_client = MCPClient(create_connection)
                    
#                     # Test connection and get available tools
#                     with mcp_client as client:
#                         tools = client.list_tools_sync()
#                         if tools:
#                             all_tools.extend(tools)
#                             logger.info(f"Successfully connected to {mcp_config.server_name}: {len(tools)} tools available")
#                             logger.info(f"Sample tools from {mcp_config.server_name}: {[str(tool)[:100] for tool in tools[:5]]}")
#                         else:
#                             logger.warning(f"No tools found for {mcp_config.server_name}")
                    
#                     # Store connection for later use
#                     self.mcp_connections[mcp_config.server_name] = mcp_client
                    
#             except Exception as e:
#                 logger.error(f"Failed to setup MCP server {mcp_config.server_name}: {str(e)}")
#                 continue
        
#         logger.info(f"Total MCP tools loaded from all servers: {len(all_tools)}")
#         return all_tools
    
#     def _find_mcp_server(self, config: MCPServerConfig) -> Optional[str]:
#         """Auto-detect MCP server path"""
#         logger.info(f"Setting up MCP server: {config.server_name}")
        
#         for location in config.possible_locations:
#             expanded_path = os.path.expanduser(location)
#             logger.info(f"Checking location: {expanded_path}")
#             if os.path.exists(expanded_path):
#                 logger.info(f"Found MCP server at: {expanded_path}")
#                 return expanded_path
        
#         logger.warning(f"MCP server {config.server_name} not found at any specified location")
#         return None
    
#     def create_custom_tool(self, tool_config: ToolConfig) -> Callable:
#         """Create custom tool from configuration"""
#         if tool_config.code:
#             try:
#                 # Dynamic tool creation from code
#                 namespace = {'tool': tool}  # Make tool decorator available
#                 exec(tool_config.code, namespace)
                
#                 # Find the tool function
#                 for name, obj in namespace.items():
#                     if callable(obj) and hasattr(obj, '__tool__'):
#                         logger.info(f"Created custom tool: {tool_config.tool_name}")
#                         return obj
#             except Exception as e:
#                 logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
                    
#         # Return a placeholder tool if creation fails
#         @tool
#         def custom_tool(**kwargs):
#             """Custom tool placeholder"""
#             return f"Executing {tool_config.tool_name} with params: {kwargs}"
        
#         return custom_tool
    
#     def get_builtin_tools(self, tool_names: List[str]) -> List[Callable]:
#         """Get built-in Strands tools"""
#         builtin_tools = {
#             "current_time": current_time,
#             # Add more built-in tools as needed
#         }
        
#         tools = []
#         for name in tool_names:
#             if name in builtin_tools:
#                 tools.append(builtin_tools[name])
#                 logger.info(f"Added built-in tool: {name}")
#             else:
#                 logger.warning(f"Built-in tool not found: {name}")
        
#         return tools
    
#     async def build_agent(self, config) -> Agent:
#         """Build a complete Strands agent from configuration"""
        
#         try:
#             logger.info("Starting agent build process...")
            
#             # Handle both field names: model_config or agent_model_config
#             model_config = None
#             if hasattr(config, 'agent_model_config'):
#                 model_config = config.agent_model_config
#             elif hasattr(config, 'model_config'):
#                 model_config = config.model_config
#             else:
#                 raise ValueError("No model configuration found in agent config")
            
#             # Create model
#             logger.info(f"Creating model with provider: {model_config.provider}")
#             if model_config.provider == "bedrock":
#                 logger.info(f"Creating Bedrock model in region: {os.getenv('AWS_REGION', 'us-east-1')}")
#             model = self.create_model(model_config)
            
#             # Setup MCP servers and get tools
#             logger.info("Setting up MCP servers...")
#             mcp_tools = []
#             if hasattr(config, 'mcp_servers') and config.mcp_servers:
#                 mcp_tools = await self.setup_mcp_servers(config.mcp_servers)
            
#             # Get custom tools
#             logger.info("Creating custom tools...")
#             custom_tools = []
#             if hasattr(config, 'tools') and config.tools:
#                 for tool_config in config.tools:
#                     if tool_config.enabled and tool_config.tool_type == "custom":
#                         custom_tool = self.create_custom_tool(tool_config)
#                         if custom_tool:
#                             custom_tools.append(custom_tool)
            
#             # Get built-in tools
#             logger.info("Adding built-in tools...")
#             builtin_tools = []
#             if hasattr(config, 'builtin_tools') and config.builtin_tools:
#                 builtin_tools = self.get_builtin_tools(config.builtin_tools)
#                 for tool_name in config.builtin_tools:
#                     if tool_name == "file_write":
#                         logger.warning(f"Built-in tool not found: {tool_name}")
            
#             # Combine all tools
#             all_tools = builtin_tools + mcp_tools + custom_tools
#             logger.info(f"Total tools available: {len(all_tools)}")
#             logger.info(f"  - Built-in tools: {len(builtin_tools)}")
#             logger.info(f"  - MCP tools: {len(mcp_tools)}")
#             logger.info(f"  - Custom tools: {len(custom_tools)}")
            
#             # Create agent
#             logger.info("Creating agent...")
#             agent = Agent(
#                 model=model,
#                 tools=all_tools if all_tools else [],
#                 system_prompt=config.system_prompt if hasattr(config, 'system_prompt') else "You are a helpful assistant"
#             )
            
#             logger.info("Agent successfully built")
#             return agent
            
#         except Exception as e:
#             logger.error(f"Failed to build agent: {str(e)}", exc_info=True)
#             raise
    
#     @asynccontextmanager
#     async def get_mcp_context(self):
#         """Context manager for MCP connections"""
#         active_clients = []
#         try:
#             # Start all MCP clients
#             for server_name, mcp_client in self.mcp_connections.items():
#                 if mcp_client:
#                     client = mcp_client.__enter__()
#                     active_clients.append((server_name, mcp_client, client))
#                     logger.info(f"Started MCP client: {server_name}")
            
#             yield active_clients
            
#         finally:
#             # Clean up all MCP clients
#             for server_name, mcp_client, client in active_clients:
#                 try:
#                     mcp_client.__exit__(None, None, None)
#                     logger.info(f"Closed MCP client: {server_name}")
#                 except Exception as e:
#                     logger.error(f"Error closing MCP client {server_name}: {e}")


# app/services/agent_builder.py
"""
Dynamic agent builder service with improved MCP context management and error handling
"""
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from contextlib import asynccontextmanager
from strands import Agent, tool, models
from strands.models import BedrockModel
from strands_tools import current_time
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from app.models.agent import ModelConfig, MCPServerConfig, ToolConfig

logger = logging.getLogger(__name__)

class DynamicAgentBuilder:
    def __init__(self):
        self.mcp_connections: Dict[str, Any] = {}
        self.custom_tools: Dict[str, Callable] = {}
        
    def create_model(self, config: ModelConfig) -> models:
        """Create appropriate model based on provider"""
        
        if config.provider == "bedrock":
            return BedrockModel(
                model_id=config.model_id,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                client_config=config.client_config if config.client_config else {}
            )
            
        elif config.provider == "perplexity":
            api_key = os.getenv(config.api_key_env or "PERPLEXITY_API_KEY")
            return self._create_perplexity_model(config, api_key)
            
        else:
            raise ValueError(f"Unsupported model provider: {config.provider}")
    
    def _create_perplexity_model(self, config: ModelConfig, api_key: str):
        """Create Perplexity model (using OpenAI-compatible interface)"""
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("OpenAI package not installed for Perplexity model")
            raise ImportError("Please install openai package: pip install openai")
        
        class PerplexityModel(models):
            def __init__(self, model_id, api_key, **kwargs):
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.perplexity.ai"
                )
                self.model_id = model_id
                self.kwargs = kwargs
                
            def __call__(self, prompt: str) -> str:
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_id,
                        messages=[{"role": "user", "content": prompt}],
                        **self.kwargs
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Perplexity API call failed: {str(e)}")
                    raise
        
        return PerplexityModel(
            model_id=config.model_id,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    
    def _validate_mcp_server_requirements(self, mcp_config: MCPServerConfig) -> bool:
        """Validate MCP server requirements before attempting connection"""
        try:
            # Check if Node.js is available for Node.js-based servers
            if mcp_config.command == "node":
                import subprocess
                result = subprocess.run(['node', '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode != 0:
                    logger.error(f"Node.js not available for {mcp_config.server_name}")
                    return False
                logger.info(f"Node.js version: {result.stdout.strip()}")
            
            # Check if server file exists and is readable
            if mcp_config.args:
                server_file = mcp_config.args[0]
                if not os.path.exists(server_file):
                    logger.error(f"Server file not found: {server_file}")
                    return False
                if not os.access(server_file, os.R_OK):
                    logger.error(f"Server file not readable: {server_file}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating MCP server requirements: {e}")
            return False
    
    async def _test_mcp_connection_with_timeout(self, mcp_client, server_name: str, timeout: int = 60) -> List[Any]:
        """Test MCP connection with configurable timeout"""
        try:
            logger.info(f"Testing MCP connection for {server_name} with {timeout}s timeout...")
            
            # Use asyncio timeout for better control
            async def test_connection():
                with mcp_client as client:
                    return client.list_tools_sync()
            
            # Run with timeout
            tools = await asyncio.wait_for(test_connection(), timeout=timeout)
            return tools or []
            
        except asyncio.TimeoutError:
            logger.error(f"MCP server {server_name} connection timeout after {timeout} seconds")
            return []
        except Exception as e:
            logger.error(f"MCP server {server_name} connection failed: {str(e)}")
            return []
    
    async def setup_mcp_servers(self, mcp_configs: List[MCPServerConfig]) -> List[Any]:
        """Setup MCP servers with improved error handling and timeout management"""
        all_tools = []
        
        for mcp_config in mcp_configs:
            if not mcp_config.enabled:
                logger.info(f"Skipping disabled MCP server: {mcp_config.server_name}")
                continue
                
            try:
                logger.info(f"Setting up MCP server: {mcp_config.server_name}")
                
                # Auto-detect server path if needed
                if mcp_config.auto_detect_path:
                    server_path = self._find_mcp_server(mcp_config)
                    if not server_path:
                        logger.warning(f"MCP server {mcp_config.server_name} not found at any location")
                        continue
                    
                    # Update the command arguments
                    if mcp_config.server_name == "sap-abap-adt" or "abap" in mcp_config.server_name.lower():
                        mcp_config.command = "node"
                        mcp_config.args = [server_path]
                        logger.info(f"Found SAP ABAP ADT server at: {server_path}")
                
                # Validate requirements before attempting connection
                if not self._validate_mcp_server_requirements(mcp_config):
                    logger.warning(f"MCP server {mcp_config.server_name} requirements not met, skipping")
                    continue
                
                logger.info(f"Command: {mcp_config.command} {' '.join(mcp_config.args if mcp_config.args else [])}")
                logger.info(f"Environment variables: {mcp_config.env_vars}")
                
                # Create MCP connection function with enhanced configuration
                if mcp_config.server_type == "stdio":
                    def create_connection():
                        env_vars = {**os.environ, **mcp_config.env_vars}
                        
                        # Add debugging environment variables
                        if logger.isEnabledFor(logging.DEBUG):
                            env_vars['DEBUG'] = '1'
                            env_vars['NODE_DEBUG'] = 'mcp'
                        
                        return stdio_client(
                            StdioServerParameters(
                                command=mcp_config.command,
                                args=mcp_config.args or [],
                                env=env_vars
                            )
                        )
                    
                    mcp_client = MCPClient(create_connection)
                    
                    # Test connection with extended timeout for slow servers
                    timeout = getattr(mcp_config, 'connection_timeout', 60)  # Default 60 seconds
                    tools = await self._test_mcp_connection_with_timeout(mcp_client, mcp_config.server_name, timeout)
                    
                    if tools:
                        all_tools.extend(tools)
                        self.mcp_connections[mcp_config.server_name] = mcp_client
                        logger.info(f"Successfully connected to {mcp_config.server_name}: {len(tools)} tools available")
                        
                        # Log sample tools for debugging
                        if logger.isEnabledFor(logging.DEBUG):
                            sample_tools = [str(tool)[:100] for tool in tools[:3]]
                            logger.debug(f"Sample tools from {mcp_config.server_name}: {sample_tools}")
                    else:
                        logger.warning(f"No tools found or connection failed for {mcp_config.server_name}")
                        
            except Exception as e:
                logger.error(f"Failed to setup MCP server {mcp_config.server_name}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Total MCP tools loaded from all servers: {len(all_tools)}")
        return all_tools
    
    def _find_mcp_server(self, config: MCPServerConfig) -> Optional[str]:
        """Auto-detect MCP server path with enhanced logging"""
        logger.info(f"Auto-detecting MCP server: {config.server_name}")
        
        for location in config.possible_locations:
            expanded_path = os.path.expanduser(location)
            logger.debug(f"Checking location: {expanded_path}")
            
            if os.path.exists(expanded_path):
                # Additional validation for Node.js files
                if expanded_path.endswith('.js'):
                    try:
                        # Check if it's a valid JavaScript file
                        with open(expanded_path, 'r', encoding='utf-8') as f:
                            content = f.read(1000)  # Read first 1000 chars
                            if 'mcp' in content.lower() or 'server' in content.lower():
                                logger.info(f"Found valid MCP server at: {expanded_path}")
                                return expanded_path
                            else:
                                logger.warning(f"File exists but may not be an MCP server: {expanded_path}")
                    except Exception as e:
                        logger.warning(f"Could not validate server file {expanded_path}: {e}")
                else:
                    logger.info(f"Found MCP server at: {expanded_path}")
                    return expanded_path
        
        logger.error(f"MCP server {config.server_name} not found at any specified location")
        return None
    
    def create_custom_tool(self, tool_config: ToolConfig) -> Callable:
        """Create custom tool from configuration"""
        if tool_config.code:
            try:
                # Dynamic tool creation from code
                namespace = {'tool': tool}  # Make tool decorator available
                exec(tool_config.code, namespace)
                
                # Find the tool function
                for name, obj in namespace.items():
                    if callable(obj) and hasattr(obj, '__tool__'):
                        logger.info(f"Created custom tool: {tool_config.tool_name}")
                        return obj
            except Exception as e:
                logger.error(f"Failed to create custom tool {tool_config.tool_name}: {str(e)}")
                    
        # Return a placeholder tool if creation fails
        @tool
        def custom_tool(**kwargs):
            """Custom tool placeholder"""
            return f"Executing {tool_config.tool_name} with params: {kwargs}"
        
        return custom_tool
    
    def get_builtin_tools(self, tool_names: List[str]) -> List[Callable]:
        """Get built-in Strands tools"""
        builtin_tools = {
            "current_time": current_time,
            # Add more built-in tools as needed
        }
        
        tools = []
        for name in tool_names:
            if name in builtin_tools:
                tools.append(builtin_tools[name])
                logger.info(f"Added built-in tool: {name}")
            else:
                logger.warning(f"Built-in tool not found: {name}")
        
        return tools
    
    async def build_agent(self, config) -> Agent:
        """Build a complete Strands agent from configuration with resilient error handling"""
        
        try:
            logger.info("Starting agent build process...")
            
            # Handle both field names: model_config or agent_model_config
            model_config = None
            if hasattr(config, 'agent_model_config'):
                model_config = config.agent_model_config
            elif hasattr(config, 'model_config'):
                model_config = config.model_config
            else:
                raise ValueError("No model configuration found in agent config")
            
            # Create model
            logger.info(f"Creating model with provider: {model_config.provider}")
            if model_config.provider == "bedrock":
                logger.info(f"Creating Bedrock model in region: {os.getenv('AWS_REGION', 'us-east-1')}")
            model = self.create_model(model_config)
            
            # Setup MCP servers and get tools (with improved error handling)
            logger.info("Setting up MCP servers...")
            mcp_tools = []
            if hasattr(config, 'mcp_servers') and config.mcp_servers:
                try:
                    mcp_tools = await self.setup_mcp_servers(config.mcp_servers)
                except Exception as e:
                    logger.error(f"Failed to setup some MCP servers: {e}")
                    # Continue with agent creation even if some MCP servers fail
            
            # Get custom tools
            logger.info("Creating custom tools...")
            custom_tools = []
            if hasattr(config, 'tools') and config.tools:
                for tool_config in config.tools:
                    if tool_config.enabled and tool_config.tool_type == "custom":
                        try:
                            custom_tool = self.create_custom_tool(tool_config)
                            if custom_tool:
                                custom_tools.append(custom_tool)
                        except Exception as e:
                            logger.error(f"Failed to create custom tool {tool_config.tool_name}: {e}")
            
            # Get built-in tools
            logger.info("Adding built-in tools...")
            builtin_tools = []
            if hasattr(config, 'builtin_tools') and config.builtin_tools:
                try:
                    builtin_tools = self.get_builtin_tools(config.builtin_tools)
                except Exception as e:
                    logger.error(f"Failed to load some built-in tools: {e}")
            
            # Combine all tools
            all_tools = builtin_tools + mcp_tools + custom_tools
            logger.info(f"Total tools available: {len(all_tools)}")
            logger.info(f"  - Built-in tools: {len(builtin_tools)}")
            logger.info(f"  - MCP tools: {len(mcp_tools)}")
            logger.info(f"  - Custom tools: {len(custom_tools)}")
            
            # Create agent
            logger.info("Creating agent...")
            agent = Agent(
                model=model,
                tools=all_tools if all_tools else [],
                system_prompt=config.system_prompt if hasattr(config, 'system_prompt') else "You are a helpful assistant"
            )
            
            logger.info("Agent successfully built")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to build agent: {str(e)}", exc_info=True)
            raise
    
    @asynccontextmanager
    async def get_mcp_context(self):
        """Context manager for MCP connections with proper cleanup"""
        active_clients = []
        try:
            # Start all MCP clients
            for server_name, mcp_client in self.mcp_connections.items():
                if mcp_client:
                    try:
                        client = mcp_client.__enter__()
                        active_clients.append((server_name, mcp_client, client))
                        logger.info(f"Started MCP client: {server_name}")
                    except Exception as e:
                        logger.error(f"Failed to start MCP client {server_name}: {e}")
            
            yield active_clients
            
        finally:
            # Clean up all MCP clients
            for server_name, mcp_client, client in active_clients:
                try:
                    mcp_client.__exit__(None, None, None)
                    logger.info(f"Closed MCP client: {server_name}")
                except Exception as e:
                    logger.error(f"Error closing MCP client {server_name}: {e}")
    
    def cleanup(self):
        """Clean up all connections and resources"""
        for server_name, mcp_client in self.mcp_connections.items():
            try:
                if hasattr(mcp_client, '__exit__'):
                    mcp_client.__exit__(None, None, None)
                logger.info(f"Cleaned up MCP client: {server_name}")
            except Exception as e:
                logger.error(f"Error during cleanup of {server_name}: {e}")
        
        self.mcp_connections.clear()
        self.custom_tools.clear()