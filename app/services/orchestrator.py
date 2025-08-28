# # # app/services/orchestrator.py
# # """
# # Main orchestrator service for agent execution
# # """
# # import asyncio
# # import json
# # import logging
# # from datetime import datetime
# # from typing import Dict, Any
# # from app.models.agent import AgentConfiguration
# # from app.models.execution import AgentExecution
# # from app.models.schemas import ExecuteAgentRequest
# # from app.services.agent_builder import DynamicAgentBuilder
# # from app.config import settings
# # from langfuse import observe
# # from langfuse import get_client
# # from bson import ObjectId
# # from fastapi import HTTPException
# # from beanie.odm.fields import PydanticObjectId

# # langfuse = get_client()

# # def normalize_mongo_ids(data: dict) -> dict:
# #     """Recursively convert ObjectId/PydanticObjectId to str."""
# #     for key, value in data.items():
# #         if isinstance(value, (ObjectId, PydanticObjectId)):
# #             data[key] = str(value)
# #         elif isinstance(value, list):
# #             data[key] = [str(v) if isinstance(v, (ObjectId, PydanticObjectId)) else v for v in value]
# #         elif isinstance(value, dict):
# #             data[key] = normalize_mongo_ids(value)
# #     return data


# # # Obtain the current trace ID
# # trace_id = langfuse.get_current_trace_id()



# # logger = logging.getLogger(__name__)

# # class Orchestrator:
# #     def __init__(self):
# #         self.agent_builder = DynamicAgentBuilder()
# #         self.active_executions: Dict[str, asyncio.Task] = {}
    
# #     @observe(name="execute_agent")
# #     async def execute_agent(self, request: any) -> AgentExecution:
# #         """Execute agent with full dynamic configuration"""
        
# #         # Create execution record
# #         execution = AgentExecution(
# #             execution_id=f"exec_{datetime.utcnow().timestamp()}",
# #             agent_id=request.agent_id,
# #             input_data=request.input_data,
# #             agent_version="1",
# #             status="initializing",
# #             started_at=datetime.utcnow(),
# #             metadata=request.metadata or {}
# #         )
# #         await execution.save()
        
# #         try:
# #             # Load agent configuration
# #             agent_config = await AgentConfiguration.find_one(
# #                 AgentConfiguration.agent_id == request.agent_id
# #             )

# #             agent_config = normalize_mongo_ids(agent_config.dict())
# #             print("BOOOOOOOOOOOOM HERE",agent_config)
# #             if not agent_config:
# #                 raise Exception(f"Agent {request.agent_id} not found")
            
# #             execution.agent_version = "1"
            
# #             # Apply overrides if provided
# #             if request.system_prompt_override:
# #                 logger.info(f"Overriding system prompt for agent {request.agent_id}")
# #                 agent_config.system_prompt = request.system_prompt_override
# #             if request.model_override:
# #                 logger.info(f"Overriding model config for agent {request.agent_id}")
# #                 agent_config.agent_model_config = request.model_override
# #             if request.mcp_servers_override:
# #                 logger.info(f"Overriding MCP servers for agent {request.agent_id}")
# #                 agent_config.mcp_servers = request.mcp_servers_override
# #             if request.tools_override:
# #                 logger.info(f"Overriding tools for agent {request.agent_id}")
# #                 agent_config.tools = request.tools_override
            
# #             # Build agent
# #             agent = await self.agent_builder.build_agent(agent_config)
            
# #             # Track MCP servers
# #             execution.mcp_servers_used = [
# #                 server.server_name for server in agent_config.mcp_servers if server.enabled
# #             ]
            
# #             # Update status
# #             execution.status = "running"
# #             await execution.save()
            
# #             # Execute with timeout
# #             timeout = request.timeout_override or agent_config.timeout
            
# #             if agent_config.chunking_enabled:
# #                 result = await self._execute_chunked(
# #                     agent, 
# #                     request.input_data,
# #                     agent_config.chunk_size,
# #                     timeout
# #                 )
# #             else:
# #                 async with asyncio.timeout(timeout):
# #                     prompt = request.input_data.get("prompt", json.dumps(request.input_data))
# #                     result = await asyncio.to_thread(agent, prompt)
            
# #             # Process result
# #             if isinstance(result, str):
# #                 output_data = {"response": result}
# #             else:
# #                 output_data = {"response": str(result)}
            
# #             # Update execution
# #             execution.status = "completed"
# #             execution.output_data = output_data
# #             execution.completed_at = datetime.utcnow()
# #             execution.duration_ms = int(
# #                 (execution.completed_at - execution.started_at).total_seconds() * 1000
# #             )
            
# #             if request.include_trace:
# #                 execution.langfuse_trace_id =  langfuse.get_current_trace_id()
# #                 execution.trace_url = f"{settings.langfuse_host}/trace/{execution.langfuse_trace_id}"
            
# #             await execution.save()
# #             return execution
            
# #         except asyncio.TimeoutError:
# #             logger.warning(f"Agent execution timeout for {request.agent_id} after {timeout} seconds")
# #             execution.status = "timeout"
# #             execution.error_message = f"Execution timeout after {timeout} seconds"
# #             execution.completed_at = datetime.utcnow()
# #             if execution.started_at:
# #                 execution.duration_ms = int(
# #                     (execution.completed_at - execution.started_at).total_seconds() * 1000
# #                 )
# #             await execution.save()
# #             raise
            
# #         except Exception as e:
# #             logger.error(f"Agent execution failed for {request.agent_id}: {str(e)}", exc_info=True)
# #             execution.status = "failed"
# #             execution.error_message = str(e)
# #             execution.completed_at = datetime.utcnow()
# #             if execution.started_at:
# #                 execution.duration_ms = int(
# #                     (execution.completed_at - execution.started_at).total_seconds() * 1000
# #                 )
# #             await execution.save()
# #             raise
    
# #     async def _execute_chunked(
# #         self,
# #         agent,
# #         input_data: Dict[str, Any],
# #         chunk_size: int,
# #         timeout: int
# #     ) -> Dict[str, Any]:
# #         """Execute agent in chunks"""
# #         results = []
# #         data_str = json.dumps(input_data)
# #         chunks = [data_str[i:i+chunk_size] for i in range(0, len(data_str), chunk_size)]
        
# #         for i, chunk in enumerate(chunks):
# #             logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
# #             try:
# #                 async with asyncio.timeout(timeout):
# #                     chunk_result = await asyncio.to_thread(agent, chunk)
# #                     results.append(chunk_result)
# #             except Exception as e:
# #                 logger.error(f"Failed to process chunk {i+1}: {str(e)}")
# #                 results.append({"error": f"Chunk {i+1} failed: {str(e)}"})

        
# #         return {"chunked_results": results}


# # app/services/orchestrator.py
# """
# Main orchestrator service for agent execution
# """
# import asyncio
# import json
# import logging
# from datetime import datetime
# from typing import Dict, Any
# from app.models.agent import AgentConfiguration
# from app.models.execution import AgentExecution
# from app.models.schemas import ExecuteAgentRequest
# from app.services.agent_builder import DynamicAgentBuilder
# from app.config import settings
# from langfuse import observe
# logger = logging.getLogger(__name__)

# class Orchestrator:
#     def __init__(self):
#         self.agent_builder = DynamicAgentBuilder()
#         self.active_executions: Dict[str, asyncio.Task] = {}
    
#     @observe(name="execute_agent")
#     async def execute_agent(self, request: ExecuteAgentRequest) -> AgentExecution:
#         """Execute agent with full dynamic configuration"""
        
#         # Create execution record
#         execution = AgentExecution(
#             execution_id=f"exec_{datetime.utcnow().timestamp()}",
#             agent_id=request.agent_id,
#             input_data=request.input_data,
#             agent_version=1,
#             status="initializing",
#             started_at=datetime.utcnow(),
#             metadata=request.metadata or {}
#         )
#         await execution.save()
        
#         try:
#             # Load agent configuration
#             agent_config = await AgentConfiguration.find_one(
#                 AgentConfiguration.agent_id == request.agent_id
#             )
            
#             if not agent_config:
#                 raise Exception(f"Agent {request.agent_id} not found")
            
#             execution.agent_version = agent_config.version
            
#             # Apply overrides if provided (work with the object, not dict)
#             if request.system_prompt_override:
#                 logger.info(f"Overriding system prompt for agent {request.agent_id}")
#                 agent_config.system_prompt = request.system_prompt_override
            
#             if request.model_override:
#                 logger.info(f"Overriding model config for agent {request.agent_id}")
#                 # Check if the field is named 'model_config' or 'agent_model_config'
#                 if hasattr(agent_config, 'agent_model_config'):
#                     agent_config.agent_model_config = request.model_override
#                 else:
#                     agent_config.model_config = request.model_override
            
#             if request.mcp_servers_override:
#                 logger.info(f"Overriding MCP servers for agent {request.agent_id}")
#                 agent_config.mcp_servers = request.mcp_servers_override
            
#             if request.tools_override:
#                 logger.info(f"Overriding tools for agent {request.agent_id}")
#                 agent_config.tools = request.tools_override
            
#             # Build agent (pass the actual object, not dict)
#             agent = await self.agent_builder.build_agent(agent_config)

#             print("AGENT BUILD",agent)
            
#             # Track MCP servers
#             execution.mcp_servers_used = [
#                 server.server_name for server in agent_config.mcp_servers if server.enabled
#             ]
            
#             # Update status
#             execution.status = "running"
#             await execution.save()
            
#             # Execute with timeout
#             timeout = request.timeout_override or agent_config.timeout
            
#             if agent_config.chunking_enabled:
#                 result = await self._execute_chunked(
#                     agent, 
#                     request.input_data,
#                     agent_config.chunk_size,
#                     timeout
#                 )
#             else:
#                 async with asyncio.timeout(timeout):
#                     prompt = request.input_data.get("prompt", json.dumps(request.input_data))
#                     result = await asyncio.to_thread(agent, prompt)
            
#             # Process result
#             if isinstance(result, str):
#                 output_data = {"response": result}
#             else:
#                 output_data = {"response": str(result)}
            
#             # Update execution
#             execution.status = "completed"
#             execution.output_data = output_data
#             execution.completed_at = datetime.utcnow()
#             execution.duration_ms = int(
#                 (execution.completed_at - execution.started_at).total_seconds() * 1000
#             )
            
#             if request.include_trace:
#                 try:
#                     execution.langfuse_trace_id = "1"
#                     execution.trace_url = f"{settings.langfuse_host}/trace/{execution.langfuse_trace_id}"
#                 except:
#                     # Handle case when Langfuse is not configured
#                     logger.warning("Langfuse not configured, skipping trace")
            
#             await execution.save()
#             return execution
            
#         except asyncio.TimeoutError:
#             logger.warning(f"Agent execution timeout for {request.agent_id} after {timeout} seconds")
#             execution.status = "timeout"
#             execution.error_message = f"Execution timeout after {timeout} seconds"
#             execution.completed_at = datetime.utcnow()
#             if execution.started_at:
#                 execution.duration_ms = int(
#                     (execution.completed_at - execution.started_at).total_seconds() * 1000
#                 )
#             await execution.save()
#             raise
            
#         except Exception as e:
#             logger.error(f"Agent execution failed for {request.agent_id}: {str(e)}", exc_info=True)
#             execution.status = "failed"
#             execution.error_message = str(e)
#             execution.completed_at = datetime.utcnow()
#             if execution.started_at:
#                 execution.duration_ms = int(
#                     (execution.completed_at - execution.started_at).total_seconds() * 1000
#                 )
#             await execution.save()
#             raise
    
#     async def _execute_chunked(
#         self,
#         agent,
#         input_data: Dict[str, Any],
#         chunk_size: int,
#         timeout: int
#     ) -> Dict[str, Any]:
#         """Execute agent in chunks"""
#         results = []
#         data_str = json.dumps(input_data)
#         chunks = [data_str[i:i+chunk_size] for i in range(0, len(data_str), chunk_size)]
        
#         for i, chunk in enumerate(chunks):
#             logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
#             try:
#                 async with asyncio.timeout(timeout):
#                     chunk_result = await asyncio.to_thread(agent, chunk)
#                     results.append(chunk_result)
#             except Exception as e:
#                 logger.error(f"Failed to process chunk {i+1}: {str(e)}")
#                 results.append({"error": f"Chunk {i+1} failed: {str(e)}"})
        
#         return {"chunked_results": results}


# app/services/orchestrator.py
"""
Main orchestrator service for agent execution with proper MCP context management
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from app.models.agent import AgentConfiguration
from app.models.execution import AgentExecution
from app.models.schemas import ExecuteAgentRequest
from app.services.agent_builder import DynamicAgentBuilder
from app.config import settings
from langfuse import observe

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.agent_builder = DynamicAgentBuilder()
        self.active_executions: Dict[str, asyncio.Task] = {}
    
    @observe(name="execute_agent")
    async def execute_agent(self, request: ExecuteAgentRequest) -> AgentExecution:
        """Execute agent with full dynamic configuration and proper MCP context"""
        
        # Create execution record
        execution = AgentExecution(
            execution_id=f"exec_{datetime.utcnow().timestamp()}",
            agent_id=request.agent_id,
            input_data=request.input_data,
            agent_version=1,
            status="initializing",
            started_at=datetime.utcnow(),
            metadata=request.metadata or {}
        )
        await execution.save()
        
        try:
            # Load agent configuration
            agent_config = await AgentConfiguration.find_one(
                AgentConfiguration.agent_id == request.agent_id
            )
            
            if not agent_config:
                raise Exception(f"Agent {request.agent_id} not found")
            
            execution.agent_version = agent_config.version
            
            # Apply overrides if provided
            if request.system_prompt_override:
                logger.info(f"Overriding system prompt for agent {request.agent_id}")
                agent_config.system_prompt = request.system_prompt_override
            
            if request.model_override:
                logger.info(f"Overriding model config for agent {request.agent_id}")
                if hasattr(agent_config, 'agent_model_config'):
                    agent_config.agent_model_config = request.model_override
                else:
                    agent_config.model_config = request.model_override
            
            if request.mcp_servers_override:
                logger.info(f"Overriding MCP servers for agent {request.agent_id}")
                agent_config.mcp_servers = request.mcp_servers_override
            
            if request.tools_override:
                logger.info(f"Overriding tools for agent {request.agent_id}")
                agent_config.tools = request.tools_override
            
            # Build agent
            agent = await self.agent_builder.build_agent(agent_config)
            
            # Track MCP servers
            execution.mcp_servers_used = [
                server.server_name for server in agent_config.mcp_servers if server.enabled
            ]
            
            # Update status
            execution.status = "running"
            await execution.save()
            
            # Execute with timeout and proper MCP context
            timeout = request.timeout_override or agent_config.timeout
            
            if agent_config.chunking_enabled:
                result = await self._execute_chunked_with_context(
                    agent, 
                    request.input_data,
                    agent_config.chunk_size,
                    timeout
                )
            else:
                result = await self._execute_with_mcp_context(
                    agent,
                    request.input_data,
                    timeout
                )
            
            # Process result
            if isinstance(result, str):
                output_data = {"response": result}
            else:
                output_data = {"response": str(result)}
            
            # Update execution
            execution.status = "completed"
            execution.output_data = output_data
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
            
            if request.include_trace:
                try:
                    execution.langfuse_trace_id = "1"
                    execution.trace_url = f"{settings.langfuse_host}/trace/{execution.langfuse_trace_id}"
                except:
                    logger.warning("Langfuse not configured, skipping trace")
            
            await execution.save()
            return execution
            
        except asyncio.TimeoutError:
            logger.warning(f"Agent execution timeout for {request.agent_id} after {timeout} seconds")
            execution.status = "timeout"
            execution.error_message = f"Execution timeout after {timeout} seconds"
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
            await execution.save()
            raise
            
        except Exception as e:
            logger.error(f"Agent execution failed for {request.agent_id}: {str(e)}", exc_info=True)
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
            await execution.save()
            raise
    
    async def _execute_with_mcp_context(
        self,
        agent,
        input_data: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute agent with proper MCP context management"""
        
        prompt = input_data.get("prompt", json.dumps(input_data))
        
        # Check if agent has MCP connections that need context
        if hasattr(self.agent_builder, 'mcp_connections') and self.agent_builder.mcp_connections:
            # Execute within MCP context
            async with self.agent_builder.get_mcp_context() as mcp_clients:
                logger.info(f"Executing agent with {len(mcp_clients)} active MCP connections")
                async with asyncio.timeout(timeout):
                    result = await asyncio.to_thread(agent, prompt)
                return result
        else:
            # Execute without MCP context
            logger.info("Executing agent without MCP connections")
            async with asyncio.timeout(timeout):
                result = await asyncio.to_thread(agent, prompt)
            return result
    
    async def _execute_chunked_with_context(
        self,
        agent,
        input_data: Dict[str, Any],
        chunk_size: int,
        timeout: int
    ) -> Dict[str, Any]:
        """Execute agent in chunks with proper MCP context"""
        results = []
        data_str = json.dumps(input_data)
        chunks = [data_str[i:i+chunk_size] for i in range(0, len(data_str), chunk_size)]
        
        # Check if agent has MCP connections
        if hasattr(self.agent_builder, 'mcp_connections') and self.agent_builder.mcp_connections:
            # Execute within MCP context
            async with self.agent_builder.get_mcp_context() as mcp_clients:
                logger.info(f"Executing chunked agent with {len(mcp_clients)} active MCP connections")
                
                for i, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                    
                    try:
                        async with asyncio.timeout(timeout):
                            chunk_result = await asyncio.to_thread(agent, chunk)
                            results.append(chunk_result)
                    except Exception as e:
                        logger.error(f"Failed to process chunk {i+1}: {str(e)}")
                        results.append({"error": f"Chunk {i+1} failed: {str(e)}"})
        else:
            # Execute without MCP context
            logger.info("Executing chunked agent without MCP connections")
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                try:
                    async with asyncio.timeout(timeout):
                        chunk_result = await asyncio.to_thread(agent, chunk)
                        results.append(chunk_result)
                except Exception as e:
                    logger.error(f"Failed to process chunk {i+1}: {str(e)}")
                    results.append({"error": f"Chunk {i+1} failed: {str(e)}"})
        
        return {"chunked_results": results}