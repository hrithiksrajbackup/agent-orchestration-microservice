# """
# Dynamic Agent Service - Database-driven agent execution
# """
# import os
# import json
# import logging
# import asyncio
# import uuid
# from datetime import datetime
# from typing import Dict, Any, List, Optional
# from contextlib import asynccontextmanager

# from strands import Agent
# from strands.models import BedrockModel
# from strands_tools import current_time

# from app.models.agent import AgentConfiguration
# from app.models.execution import AgentExecution, ExecutionResult
# from app.services.template_service import TemplateService
# from app.services.agent_builder import DynamicAgentBuilder
# from app.config import settings

# logger = logging.getLogger(__name__)

# class DynamicAgentService:
#     """Service for executing agents with database-driven configuration"""
    
#     def __init__(self):
#         self.template_service = TemplateService()
#         self.agent_builder = DynamicAgentBuilder()
#         self.active_executions: Dict[str, asyncio.Task] = {}
    
#     async def execute_agent_by_id(
#         self,
#         agent_id: str,
#         input_data: Dict[str, Any],
#         execution_id: Optional[str] = None,
#         variables: Dict[str, Any] = None,
#         async_execution: bool = False
#     ) -> AgentExecution:
#         """Execute agent by ID with database configuration"""
        
#         # Generate execution ID if not provided
#         if not execution_id:
#             execution_id = str(uuid.uuid4())
        
#         # Load agent configuration from database
#         agent_config = await AgentConfiguration.find_one(
#             AgentConfiguration.agent_id == agent_id,
#             AgentConfiguration.is_active == True
#         )
        
#         if not agent_config:
#             raise ValueError(f"Agent {agent_id} not found or inactive")
        
#         # Create execution record
#         execution = AgentExecution(
#             execution_id=execution_id,
#             agent_id=agent_id,
#             agent_version=agent_config.version,
#             input_data=input_data,
#             status="initializing",
#             started_at=datetime.utcnow(),
#             configuration_snapshot=agent_config.dict(),
#             metadata={
#                 "variables": variables or {},
#                 "async_execution": async_execution
#             }
#         )
#         await execution.save()
        
#         if async_execution:
#             # Execute in background
#             task = asyncio.create_task(
#                 self._execute_agent_background(execution_id, agent_config, input_data, variables)
#             )
#             self.active_executions[execution_id] = task
#             return execution
#         else:
#             # Execute synchronously
#             return await self._execute_agent_sync(execution, agent_config, input_data, variables)
    
#     async def _execute_agent_sync(
#         self,
#         execution: AgentExecution,
#         agent_config: AgentConfiguration,
#         input_data: Dict[str, Any],
#         variables: Dict[str, Any] = None
#     ) -> AgentExecution:
#         """Execute agent synchronously"""
        
#         try:
#             execution.status = "running"
#             await execution.save()
            
#             # Build and execute agent
#             result = await self._build_and_execute_agent(
#                 agent_config, input_data, variables, execution.execution_id
#             )
            
#             # Save result
#             result_id = await self._save_execution_result(
#                 execution.execution_id, agent_config.agent_id, result
#             )
            
#             # Update execution
#             execution.status = "completed"
#             execution.completed_at = datetime.utcnow()
#             execution.duration_ms = int(
#                 (execution.completed_at - execution.started_at).total_seconds() * 1000
#             )
#             execution.output_data = {"result_summary": "Execution completed successfully"}
#             execution.result_id = result_id
#             await execution.save()
            
#             return execution
            
#         except Exception as e:
#             logger.error(f"Agent execution failed: {e}")
#             execution.status = "failed"
#             execution.error_message = str(e)
#             execution.completed_at = datetime.utcnow()
#             if execution.started_at:
#                 execution.duration_ms = int(
#                     (execution.completed_at - execution.started_at).total_seconds() * 1000
#                 )
#             await execution.save()
#             raise
    
#     async def _execute_agent_background(
#         self,
#         execution_id: str,
#         agent_config: AgentConfiguration,
#         input_data: Dict[str, Any],
#         variables: Dict[str, Any] = None
#     ):
#         """Execute agent in background"""
        
#         try:
#             execution = await AgentExecution.find_one(
#                 AgentExecution.execution_id == execution_id
#             )
            
#             if not execution:
#                 logger.error(f"Execution {execution_id} not found")
#                 return
            
#             execution.status = "running"
#             await execution.save()
            
#             # Build and execute agent
#             result = await self._build_and_execute_agent(
#                 agent_config, input_data, variables, execution_id
#             )
            
#             # Save result
#             result_id = await self._save_execution_result(
#                 execution_id, agent_config.agent_id, result
#             )
            
#             # Update execution
#             execution.status = "completed"
#             execution.completed_at = datetime.utcnow()
#             execution.duration_ms = int(
#                 (execution.completed_at - execution.started_at).total_seconds() * 1000
#             )
#             execution.output_data = {"result_summary": "Execution completed successfully"}
#             execution.result_id = result_id
#             await execution.save()
            
#         except Exception as e:
#             logger.error(f"Background execution failed: {e}")
#             execution = await AgentExecution.find_one(
#                 AgentExecution.execution_id == execution_id
#             )
#             if execution:
#                 execution.status = "failed"
#                 execution.error_message = str(e)
#                 execution.completed_at = datetime.utcnow()
#                 if execution.started_at:
#                     execution.duration_ms = int(
#                         (execution.completed_at - execution.started_at).total_seconds() * 1000
#                     )
#                 await execution.save()
#         finally:
#             # Clean up
#             self.active_executions.pop(execution_id, None)
    
#     async def _build_and_execute_agent(
#         self,
#         agent_config: AgentConfiguration,
#         input_data: Dict[str, Any],
#         variables: Dict[str, Any] = None,
#         execution_id: str = None
#     ) -> Dict[str, Any]:
#         """Build and execute agent with dynamic configuration"""
        
#         # Resolve system prompt
#         system_prompt = await self._resolve_system_prompt(agent_config, variables)
        
#         # Update config with resolved prompt
#         agent_config.system_prompt = system_prompt
        
#         # Build agent using existing builder
#         agent = await self.agent_builder.build_agent(agent_config)
        
#         # Execute agent
#         prompt = input_data.get("prompt", json.dumps(input_data))
        
#         # Execute with timeout
#         timeout = agent_config.timeout
#         async with asyncio.timeout(timeout):
#             result = await asyncio.to_thread(agent, prompt)
        
#         # Process result
#         if isinstance(result, str):
#             return {"response": result, "execution_id": execution_id}
#         else:
#             return {"response": str(result), "execution_id": execution_id}
    
#     async def _resolve_system_prompt(
#         self,
#         agent_config: AgentConfiguration,
#         variables: Dict[str, Any] = None
#     ) -> str:
#         """Resolve system prompt from template or direct value"""
        
#         if agent_config.system_prompt_template_id:
#             # Use template service to render prompt
#             merged_variables = {**agent_config.system_prompt_variables}
#             if variables:
#                 merged_variables.update(variables)
            
#             return await self.template_service.render_system_prompt(
#                 agent_config.system_prompt_template_id,
#                 merged_variables
#             )
#         elif agent_config.system_prompt:
#             # Use direct prompt
#             return agent_config.system_prompt
#         else:
#             # Fallback
#             return "You are a helpful AI assistant."
    
#     async def _save_execution_result(
#         self,
#         execution_id: str,
#         agent_id: str,
#         result_data: Dict[str, Any]
#     ) -> str:
#         """Save execution result to database"""
        
#         result_id = str(uuid.uuid4())
        
#         # Determine result type based on content
#         result_type = "general"
#         if "exception_analysis" in str(result_data):
#             result_type = "erp_exception_analysis"
#         elif "report" in str(result_data):
#             result_type = "report"
        
#         # Create summary
#         summary = self._create_result_summary(result_data)
        
#         # Save result
#         execution_result = ExecutionResult(
#             result_id=result_id,
#             execution_id=execution_id,
#             agent_id=agent_id,
#             result_type=result_type,
#             result_data=result_data,
#             summary=summary,
#             metrics=self._extract_metrics(result_data)
#         )
#         await execution_result.save()
        
#         return result_id
    
#     def _create_result_summary(self, result_data: Dict[str, Any]) -> str:
#         """Create a summary of the result"""
#         response = result_data.get("response", "")
#         if len(response) > 500:
#             return response[:500] + "..."
#         return response
    
#     def _extract_metrics(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
#         """Extract metrics from result data"""
#         metrics = {}
        
#         response = result_data.get("response", "")
#         metrics["response_length"] = len(response)
        
#         # Try to parse JSON for more metrics
#         try:
#             if isinstance(response, str) and response.strip().startswith("{"):
#                 parsed = json.loads(response)
#                 if "exception_summary" in parsed:
#                     summary = parsed["exception_summary"]
#                     metrics.update({
#                         "total_exceptions": summary.get("total_exceptions", 0),
#                         "high_severity_count": summary.get("high_severity_count", 0),
#                         "automation_opportunities": summary.get("automation_opportunities", 0)
#                     })
#         except:
#             pass
        
#         return metrics
    
#     async def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
#         """Get execution result by execution ID"""
#         execution = await AgentExecution.find_one(
#             AgentExecution.execution_id == execution_id
#         )
        
#         if not execution or not execution.result_id:
#             return None
        
#         return await ExecutionResult.find_one(
#             ExecutionResult.result_id == execution.result_id
#         )
    
#     async def list_executions(
#         self,
#         agent_id: Optional[str] = None,
#         status: Optional[str] = None,
#         limit: int = 100
#     ) -> List[AgentExecution]:
#         """List executions with filters"""
#         query = {}
#         if agent_id:
#             query["agent_id"] = agent_id
#         if status:
#             query["status"] = status
        
#         return await AgentExecution.find(query).limit(limit).sort("-started_at").to_list()


"""
Dynamic Agent Service - Database-driven agent execution with proper MCP context management
"""
import os
import json
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from strands import Agent
from strands.models import BedrockModel
from strands_tools import current_time

from app.models.agent import AgentConfiguration
from app.models.execution import AgentExecution, ExecutionResult
from app.services.template_service import TemplateService
from app.services.agent_builder import DynamicAgentBuilder
from app.config import settings

logger = logging.getLogger(__name__)

class DynamicAgentService:
    """Service for executing agents with database-driven configuration"""
    
    def __init__(self):
        self.template_service = TemplateService()
        self.agent_builder = DynamicAgentBuilder()
        self.active_executions: Dict[str, asyncio.Task] = {}
    
    async def execute_agent_by_id(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None,
        variables: Dict[str, Any] = None,
        async_execution: bool = False
    ) -> AgentExecution:
        """Execute agent by ID with database configuration"""
        
        # Generate execution ID if not provided
        if not execution_id:
            execution_id = str(uuid.uuid4())
        
        # Load agent configuration from database
        agent_config = await AgentConfiguration.find_one(
            AgentConfiguration.agent_id == agent_id,
            AgentConfiguration.is_active == True
        )
        
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found or inactive")
        
        # Create execution record
        execution = AgentExecution(
            execution_id=execution_id,
            agent_id=agent_id,
            agent_version=agent_config.version,
            input_data=input_data,
            status="initializing",
            started_at=datetime.utcnow(),
            configuration_snapshot=agent_config.dict(),
            metadata={
                "variables": variables or {},
                "async_execution": async_execution
            }
        )
        await execution.save()
        
        if async_execution:
            # Execute in background
            task = asyncio.create_task(
                self._execute_agent_background(execution_id, agent_config, input_data, variables)
            )
            self.active_executions[execution_id] = task
            return execution
        else:
            # Execute synchronously
            return await self._execute_agent_sync(execution, agent_config, input_data, variables)
    
    async def _execute_agent_sync(
        self,
        execution: AgentExecution,
        agent_config: AgentConfiguration,
        input_data: Dict[str, Any],
        variables: Dict[str, Any] = None
    ) -> AgentExecution:
        """Execute agent synchronously with proper MCP context"""
        
        try:
            execution.status = "running"
            await execution.save()
            
            # Build and execute agent with MCP context
            result = await self._build_and_execute_agent_with_context(
                agent_config, input_data, variables, execution.execution_id
            )
            
            # Save result
            result_id = await self._save_execution_result(
                execution.execution_id, agent_config.agent_id, result
            )
            
            # Update execution
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
            execution.output_data = {"result_summary": "Execution completed successfully"}
            execution.result_id = result_id
            await execution.save()
            
            return execution
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.duration_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
            await execution.save()
            raise
    
    async def _execute_agent_background(
        self,
        execution_id: str,
        agent_config: AgentConfiguration,
        input_data: Dict[str, Any],
        variables: Dict[str, Any] = None
    ):
        """Execute agent in background with proper MCP context"""
        
        try:
            execution = await AgentExecution.find_one(
                AgentExecution.execution_id == execution_id
            )
            
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return
            
            execution.status = "running"
            await execution.save()
            
            # Build and execute agent with MCP context
            result = await self._build_and_execute_agent_with_context(
                agent_config, input_data, variables, execution_id
            )
            
            # Save result
            result_id = await self._save_execution_result(
                execution_id, agent_config.agent_id, result
            )
            
            # Update execution
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
            execution.output_data = {"result_summary": "Execution completed successfully"}
            execution.result_id = result_id
            await execution.save()
            
        except Exception as e:
            logger.error(f"Background execution failed: {e}")
            execution = await AgentExecution.find_one(
                AgentExecution.execution_id == execution_id
            )
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration_ms = int(
                        (execution.completed_at - execution.started_at).total_seconds() * 1000
                    )
                await execution.save()
        finally:
            # Clean up
            self.active_executions.pop(execution_id, None)
    
    async def _build_and_execute_agent_with_context(
        self,
        agent_config: AgentConfiguration,
        input_data: Dict[str, Any],
        variables: Dict[str, Any] = None,
        execution_id: str = None
    ) -> Dict[str, Any]:
        """Build and execute agent with proper MCP context management"""
        
        # Resolve system prompt
        system_prompt = await self._resolve_system_prompt(agent_config, variables)
        
        # Update config with resolved prompt
        agent_config.system_prompt = system_prompt
        
        # Build agent using existing builder
        agent = await self.agent_builder.build_agent(agent_config)
        
        # Execute agent within MCP context
        try:
            # Check if agent has MCP connections
            if hasattr(self.agent_builder, 'mcp_connections') and self.agent_builder.mcp_connections:
                # Execute within MCP context
                async with self.agent_builder.get_mcp_context() as mcp_clients:
                    logger.info(f"Executing agent with {len(mcp_clients)} active MCP connections")
                    result = await self._execute_agent_with_timeout(agent, input_data, agent_config.timeout)
            else:
                # Execute without MCP context
                logger.info("Executing agent without MCP connections")
                # result = await self._execute_agent_with_timeout(agent, input_data, agent_config.timeout)
            
            # Process result
            if isinstance(result, str):
                return {"response": result, "execution_id": execution_id}
            else:
                return {"response": str(result), "execution_id": execution_id}
                
        except Exception as e:
            logger.error(f"Agent execution with context failed: {e}")
            raise
    
    async def _execute_agent_with_timeout(self, agent, input_data: Dict[str, Any], timeout: int) -> Any:
        """Execute agent with timeout"""
        prompt = input_data.get("prompt", json.dumps(input_data))
        
        # Execute with timeout
        async with asyncio.timeout(timeout):
            result = await asyncio.to_thread(agent, prompt)
        
        return result
    
    async def _resolve_system_prompt(
        self,
        agent_config: AgentConfiguration,
        variables: Dict[str, Any] = None
    ) -> str:
        """Resolve system prompt from template or direct value"""
        
        if agent_config.system_prompt_template_id:
            # Use template service to render prompt
            merged_variables = {**agent_config.system_prompt_variables}
            if variables:
                merged_variables.update(variables)
            
            return await self.template_service.render_system_prompt(
                agent_config.system_prompt_template_id,
                merged_variables
            )
        elif agent_config.system_prompt:
            # Use direct prompt
            return agent_config.system_prompt
        else:
            # Fallback
            return "You are a helpful AI assistant."
    
    async def _save_execution_result(
        self,
        execution_id: str,
        agent_id: str,
        result_data: Dict[str, Any]
    ) -> str:
        """Save execution result to database"""
        
        result_id = str(uuid.uuid4())
        
        # Determine result type based on content
        result_type = "general"
        if "exception_analysis" in str(result_data):
            result_type = "erp_exception_analysis"
        elif "report" in str(result_data):
            result_type = "report"
        
        # Create summary
        summary = self._create_result_summary(result_data)
        
        # Save result
        execution_result = ExecutionResult(
            result_id=result_id,
            execution_id=execution_id,
            agent_id=agent_id,
            result_type=result_type,
            result_data=result_data,
            summary=summary,
            metrics=self._extract_metrics(result_data)
        )
        await execution_result.save()
        
        return result_id
    
    def _create_result_summary(self, result_data: Dict[str, Any]) -> str:
        """Create a summary of the result"""
        response = result_data.get("response", "")
        if len(response) > 500:
            return response[:500] + "..."
        return response
    
    def _extract_metrics(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from result data"""
        metrics = {}
        
        response = result_data.get("response", "")
        metrics["response_length"] = len(response)
        
        # Try to parse JSON for more metrics
        try:
            if isinstance(response, str) and response.strip().startswith("{"):
                parsed = json.loads(response)
                if "exception_summary" in parsed:
                    summary = parsed["exception_summary"]
                    metrics.update({
                        "total_exceptions": summary.get("total_exceptions", 0),
                        "high_severity_count": summary.get("high_severity_count", 0),
                        "automation_opportunities": summary.get("automation_opportunities", 0)
                    })
        except:
            pass
        
        return metrics
    
    async def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result by execution ID"""
        execution = await AgentExecution.find_one(
            AgentExecution.execution_id == execution_id
        )
        
        if not execution or not execution.result_id:
            return None
        
        return await ExecutionResult.find_one(
            ExecutionResult.result_id == execution.result_id
        )
    
    async def list_executions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentExecution]:
        """List executions with filters"""
        query = {}
        if agent_id:
            query["agent_id"] = agent_id
        if status:
            query["status"] = status
        
        return await AgentExecution.find(query).limit(limit).sort("-started_at").to_list()