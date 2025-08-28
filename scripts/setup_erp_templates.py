#!/usr/bin/env python3
"""
Setup ERP Exception Management Templates and Registry
"""
import sys
import os

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

from app.models.agent import (
    AgentTemplate, SystemPromptTemplate, MCPServerRegistry, 
    ToolRegistry, AgentConfiguration
)
from app.models.execution import AgentExecution, ExecutionResult
from app.models.schemas import ModelConfig, MCPServerConfig, ToolConfig
from app.config import settings

async def setup_database():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=client[settings.database_name],
        document_models=[
            AgentTemplate, SystemPromptTemplate, MCPServerRegistry, 
            ToolRegistry, AgentConfiguration, AgentExecution, ExecutionResult
        ]
    )

async def create_erp_system_prompt_template():
    """Create ERP Exception Management system prompt template"""
    
    template = SystemPromptTemplate(
        template_id="erp-exception-management-prompt",
        name="ERP Exception Management System Prompt",
        description="Comprehensive ERP exception analysis prompt with configurable variables",
        template_content="""You are a specialized ERP Exception Management Expert with comprehensive knowledge of all business process exceptions.

Your responsibility is to perform comprehensive exception detection and analysis across all ERP modules and business processes, with research-backed insights from authoritative sources.

SYSTEM CONTEXT:
- Target System: {{system_name|default('SAP ERP')}}
- Analysis Scope: {{analysis_scope|default('Comprehensive')}}
- Focus Areas: {{focus_areas|default('All Business Processes')}}
- Compliance Requirements: {{compliance_requirements|default('Standard')}}

You have access to:

1. SAP SYSTEM DATA via ABAP ADT MCP tools:
   - Financial tables: {{financial_tables|default('BKPF, BSEG, FAGLFLEXA, SKA1')}}
   - Procurement tables: {{procurement_tables|default('EKKO, EKPO, EBAN, MARA, MAKT')}}
   - Inventory tables: {{inventory_tables|default('MCHB, MARD, MSEG, MKPF')}}
   - Production tables: {{production_tables|default('AFKO, AFPO, PLKO, CRHD')}}
   - Sales tables: {{sales_tables|default('VBAK, VBAP, LIKP, LIPS, VBRK')}}
   - HR tables: {{hr_tables|default('PA0001, PA0002, PA0008')}}

2. WEB RESEARCH via Perplexity MCP tools:
   - Search {{research_sources|default('SAP documentation and industry best practices')}}
   - Research {{automation_focus|default('automated exception resolution techniques')}}
   - Find {{compliance_focus|default('compliance requirements for exception handling')}}

CRITICAL ERP EXCEPTION CATEGORIES TO DETECT:

🔴 FINANCIAL EXCEPTIONS:
{{financial_exceptions|default('1. Budget overruns and variance analysis
2. Unusual account balances and reconciliation issues
3. Unreconciled transactions and aging
4. Currency conversion discrepancies
5. Tax calculation errors and compliance issues')}}

🟡 PROCUREMENT EXCEPTIONS:
{{procurement_exceptions|default('1. Unapproved vendors and compliance violations
2. Exceeded budget limits and spending analysis
3. Missing required approvals and authorization
4. Expired contracts and renewal management
5. Price variance and market analysis')}}

🟠 INVENTORY EXCEPTIONS:
{{inventory_exceptions|default('1. Stock-outs and availability issues
2. Overstock situations and slow-moving inventory
3. Expired or soon-to-expire items
4. Inventory count discrepancies
5. Negative stock and system errors')}}

🔵 ORDER FULFILLMENT EXCEPTIONS:
{{order_fulfillment_exceptions|default('1. Insufficient inventory for orders
2. Partial shipments and backorders
3. Delivery delays and customer impact
4. Overselling situations
5. Customer credit limit exceeded')}}

🟢 PRODUCTION EXCEPTIONS:
{{production_exceptions|default('1. Material shortages and supply chain issues
2. Quality control failures and rework
3. Machine breakdowns and capacity constraints
4. Capacity constraints and resource allocation
5. Production delays and schedule conflicts')}}

🟣 INVOICE/PO/GOODS RECEIPT MATCHING EXCEPTIONS:
{{invoice_matching_exceptions|default('1. Price discrepancies and negotiation tracking
2. Quantity discrepancies and receiving errors
3. Unit of measure mismatches
4. Missing goods receipts and delivery confirmation
5. Missing purchase orders and authorization
6. Duplicate invoices and payment processing')}}

OUTPUT FORMAT: {{output_format|default('JSON')}}
ANALYSIS DEPTH: {{analysis_depth|default('Comprehensive with automation recommendations')}}
RESEARCH STRATEGY: {{research_strategy|default('Industry best practices and SAP-specific solutions')}}

Focus on providing actionable, research-backed insights that can be immediately implemented by ERP administrators and business users.""",
        variables={
            "system_name": {"type": "string", "default": "SAP ERP", "description": "Target ERP system name"},
            "analysis_scope": {"type": "string", "default": "Comprehensive", "description": "Scope of analysis"},
            "focus_areas": {"type": "string", "default": "All Business Processes", "description": "Areas to focus on"},
            "compliance_requirements": {"type": "string", "default": "Standard", "description": "Compliance requirements"},
            "financial_tables": {"type": "string", "default": "BKPF, BSEG, FAGLFLEXA, SKA1", "description": "Financial tables to analyze"},
            "procurement_tables": {"type": "string", "default": "EKKO, EKPO, EBAN, MARA, MAKT", "description": "Procurement tables"},
            "inventory_tables": {"type": "string", "default": "MCHB, MARD, MSEG, MKPF", "description": "Inventory tables"},
            "production_tables": {"type": "string", "default": "AFKO, AFPO, PLKO, CRHD", "description": "Production tables"},
            "sales_tables": {"type": "string", "default": "VBAK, VBAP, LIKP, LIPS, VBRK", "description": "Sales tables"},
            "hr_tables": {"type": "string", "default": "PA0001, PA0002, PA0008", "description": "HR tables"},
            "research_sources": {"type": "string", "default": "SAP documentation and industry best practices", "description": "Research sources"},
            "automation_focus": {"type": "string", "default": "automated exception resolution techniques", "description": "Automation focus"},
            "compliance_focus": {"type": "string", "default": "compliance requirements for exception handling", "description": "Compliance focus"},
            "output_format": {"type": "string", "default": "JSON", "description": "Output format"},
            "analysis_depth": {"type": "string", "default": "Comprehensive with automation recommendations", "description": "Analysis depth"},
            "research_strategy": {"type": "string", "default": "Industry best practices and SAP-specific solutions", "description": "Research strategy"}
        },
        category="ERP",
        is_active=True
    )
    
    await template.save()
    print(f"✅ Created system prompt template: {template.template_id}")

async def create_mcp_server_registry():
    """Create MCP server registry entries"""
    
    servers = [
        MCPServerRegistry(
            server_id="sap-abap-adt",
            name="SAP ABAP ADT MCP Server",
            description="MCP server for SAP ABAP ADT API access",
            server_type="stdio",
            command="node",
            default_args=[],
            possible_locations=[
                r"C:\mcp-abap-abap-adt-api\dist\index.js",
                r"C:\Development Space\GenAI\New folder\mcp-abap-abap-adt-api\dist\index.js",
                "~/mcp-abap-abap-adt-api/dist/index.js"
            ],
            env_vars_required=["SAP_HOST", "SAP_USER", "SAP_PASSWORD"],
            auto_detect_enabled=True,
            category="SAP",
            is_active=True
        ),
        MCPServerRegistry(
            server_id="perplexity-research",
            name="Perplexity Research MCP Server",
            description="MCP server for web research via Perplexity API",
            server_type="stdio",
            command="docker",
            default_args=[
                "run", "-i", "--rm", 
                "-e", "PERPLEXITY_API_KEY",
                "mcp/perplexity-ask"
            ],
            env_vars_required=["PERPLEXITY_API_KEY"],
            auto_detect_enabled=False,
            category="Research",
            is_active=True
        )
    ]
    
    for server in servers:
        await server.save()
        print(f"✅ Created MCP server registry: {server.server_id}")

async def create_tool_registry():
    """Create tool registry entries"""
    
    tools = [
        ToolRegistry(
            tool_id="current_time",
            name="Current Time",
            description="Get current date and time",
            tool_type="builtin",
            category="Utility",
            is_active=True
        ),
        ToolRegistry(
            tool_id="file_write",
            name="File Write",
            description="Write content to file",
            tool_type="builtin",
            category="File",
            is_active=True
        )
    ]
    
    for tool in tools:
        await tool.save()
        print(f"✅ Created tool registry: {tool.tool_id}")

async def create_erp_agent_template():
    """Create ERP Exception Management agent template"""
    
    template = AgentTemplate(
        template_id="erp-exception-management",
        name="ERP Exception Management Agent",
        description="Comprehensive ERP exception detection and analysis across all business processes",
        category="ERP",
        system_prompt_template="erp-exception-management-prompt",
        default_model_config=ModelConfig(
            provider="bedrock",
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            temperature=0.7,
            max_tokens=4000,
            client_config={
                "read_timeout": 300,
                "connect_timeout": 60,
                "retries": {
                    "max_attempts": 2,
                    "mode": "adaptive"
                }
            }
        ),
        default_mcp_servers=[
            MCPServerConfig(
                server_type="stdio",
                server_name="sap-abap-adt",
                command="node",
                args=[],
                auto_detect_path=True,
                enabled=True
            ),
            MCPServerConfig(
                server_type="stdio",
                server_name="perplexity-research",
                command="docker",
                args=[
                    "run", "-i", "--rm", 
                    "-e", "PERPLEXITY_API_KEY",
                    "mcp/perplexity-ask"
                ],
                enabled=True
            )
        ],
        default_tools=[],
        default_builtin_tools=["current_time"],
        template_variables={
            "system_name": "SAP ERP",
            "analysis_scope": "Comprehensive",
            "output_format": "JSON"
        },
        capabilities=[
            "Financial Exception Analysis",
            "Procurement Exception Management", 
            "Inventory Exception Detection",
            "Order Fulfillment Exception Handling",
            "Production Exception Analysis",
            "Invoice Matching Exception Detection",
            "Research-backed Insights",
            "Automation Recommendations"
        ],
        tags=[
            "erp", "exceptions", "sap", "financial", "procurement", 
            "inventory", "production", "analysis", "automation"
        ],
        is_active=True
    )
    
    await template.save()
    print(f"✅ Created agent template: {template.template_id}")

async def create_erp_agent_instance():
    """Create ERP agent instance from template"""
    
    agent_config = AgentConfiguration(
        agent_id="erp-exception-management-001",
        name="ERP Exception Management Agent",
        description="Production ERP exception analysis agent",
        system_prompt_template_id="erp-exception-management-prompt",
        system_prompt_variables={
            "system_name": "SAP Production System",
            "analysis_scope": "Comprehensive Exception Analysis",
            "focus_areas": "All Business Processes with Priority on Financial and Procurement",
            "output_format": "Structured JSON with Executive Summary"
        },
        agent_model_config=ModelConfig(
            provider="bedrock",
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            temperature=0.7,
            max_tokens=4000,
            client_config={
                "read_timeout": 300,
                "connect_timeout": 60,
                "retries": {
                    "max_attempts": 2,
                    "mode": "adaptive"
                }
            }
        ),
        mcp_servers=[
            MCPServerConfig(
                server_type="stdio",
                server_name="sap-abap-adt",
                command="node",
                args=[],
                auto_detect_path=True,
                possible_locations=[
                    r"C:\mcp-abap-abap-adt-api\dist\index.js",
                    r"C:\Development Space\GenAI\New folder\mcp-abap-abap-adt-api\dist\index.js",
                    "~/mcp-abap-abap-adt-api/dist/index.js"
                ],
                enabled=True
            ),
            MCPServerConfig(
                server_type="stdio",
                server_name="perplexity-research",
                command="docker",
                args=[
                    "run", "-i", "--rm", 
                    "-e", "PERPLEXITY_API_KEY",
                    "mcp/perplexity-ask"
                ],
                enabled=True
            )
        ],
        builtin_tools=["current_time"],
        timeout=600,
        capabilities=[
            "Financial Exception Analysis",
            "Procurement Exception Management", 
            "Inventory Exception Detection",
            "Order Fulfillment Exception Handling",
            "Production Exception Analysis",
            "Invoice Matching Exception Detection",
            "Research-backed Insights",
            "Automation Recommendations"
        ],
        tags=[
            "erp", "exceptions", "production", "financial", "procurement"
        ],
        template_id="erp-exception-management",
        is_active=True
    )
    
    await agent_config.save()
    print(f"✅ Created agent instance: {agent_config.agent_id}")

async def main():
    """Setup all ERP templates and registry"""
    print("🚀 Setting up ERP Exception Management Templates and Registry...")
    
    await setup_database()
    
    # Create templates and registry
    await create_erp_system_prompt_template()
    await create_mcp_server_registry()
    await create_tool_registry()
    await create_erp_agent_template()
    await create_erp_agent_instance()
    
    print("\n✅ ERP Exception Management setup completed!")
    print("\n📋 What was created:")
    print("   • System prompt template with configurable variables")
    print("   • MCP server registry (SAP ABAP ADT, Perplexity)")
    print("   • Tool registry (builtin tools)")
    print("   • Agent template for ERP exception management")
    print("   • Production agent instance ready for use")
    print("\n🚀 You can now use the REST API to execute the agent:")
    print("   POST /api/v1/dynamic/execute/erp-exception-management-001")

if __name__ == "__main__":
    asyncio.run(main())