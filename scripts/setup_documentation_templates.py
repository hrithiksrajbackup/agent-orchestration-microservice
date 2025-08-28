#!/usr/bin/env python3
"""
Setup ABAP Documentation Agent Templates and Registry - Alternative Version
Run this from the project root directory
"""
import asyncio
import sys
import os

# Ensure we can import from the project
if not any('app' in path for path in sys.path):
    current_path = os.getcwd()
    sys.path.insert(0, current_path)

# Alternative import method
try:
    import app.models.agent as agent_models
    import app.models.execution as execution_models
    import app.models.schemas as schemas
    import app.config as config
    
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from datetime import datetime
    
    # Access the classes
    AgentTemplate = agent_models.AgentTemplate
    SystemPromptTemplate = agent_models.SystemPromptTemplate
    MCPServerRegistry = agent_models.MCPServerRegistry
    ToolRegistry = agent_models.ToolRegistry
    AgentConfiguration = agent_models.AgentConfiguration
    
    AgentExecution = execution_models.AgentExecution
    ExecutionResult = execution_models.ExecutionResult
    
    ModelConfig = schemas.ModelConfig
    MCPServerConfig = schemas.MCPServerConfig
    ToolConfig = schemas.ToolConfig
    
    settings = config.settings
    
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    print("Make sure you're running this script from the project root directory")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path[:3])
    sys.exit(1)

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

async def create_documentation_system_prompt_template():
    """Create ABAP Documentation system prompt template"""
    
    template = SystemPromptTemplate(
        template_id="abap-documentation-prompt",
        name="ABAP Documentation Generation System Prompt",
        description="Comprehensive ABAP object documentation prompt with configurable variables",
        template_content="""You are a senior SAP Consultant, ABAP Developer, and Documentation Expert.

Your responsibility is to analyze SAP ABAP development objects and generate enterprise-grade functional and technical documentation in HTML format with professional styling.

OBJECT NAME: {{object_name}}
OBJECT TYPE: {{object_type|default('Unknown')}}

You have access to:
- ABAP source code and SAP metadata via standard ABAP tools.
- All development artifacts including Programs, Includes, Function Modules, Classes, Interfaces, SmartForms, Adobe Forms, Enhancements, Workflow templates, etc.

Your objective is to:
- Produce structured documentation that explains both **functional usage** and **technical implementation** of the SAP development object {{object_name}}.
- The documentation must be **understandable by both technical and non-technical audiences**.
- It must adhere to **enterprise documentation standards** with semantic HTML tags and clean layout.

IMPORTANT TRANSACTION HANDLING:
If the user inputs a TRANSACTION (e.g., object type TRAN/T), you MUST:
1. First identify that it's a transaction using the searchObject tool
2. Query the TSTC table using tableContents tool with SQL: "SELECT * FROM TSTC WHERE TCODE = '<transaction_name>'"
3. Extract the program name from the PGMNA field in the TSTC table results
4. Use getObjectSource tool with the program URL (e.g., /sap/bc/adt/programs/programs/<program_name>/source/main)
5. Analyze the actual program source code for WRICEF categorization
6. In your HTML response, clearly indicate:
   - The transaction name and its description
   - The underlying program it calls
   - The WRICEF category based on the program's functionality

**Dynamic Documentation Structure**:

You must dynamically determine the document structure based on the WRICEF category of the object (`Workflow`, `Report`, `Interface`, `Conversion`, `Enhancement`, or `Form`).  
Each type has its own relevant sections and terminology. Automatically adjust:

- Section names
- Diagrams (e.g., flowchart for reports, architecture for interfaces)
- Tables and sample fields
- Explanation levels

Examples:
- A **Report** should contain details like selection screen, ALV output, and Open SQL logic.
- A **Workflow** should include triggering events, tasks, agents, and flow diagrams.
- An **Interface** should detail IDoc structure, middleware flow, and recovery process.

This adaptability is mandatory.

**Documentation Format and Style**:

- Return well-structured **HTML** using semantic tags (`<h1>`, `<p>`, `<table>`, etc.).
- Apply **inline CSS** with a **{{color_scheme|default('black-and-white')}} color scheme**: {{background_color|default('white background')}}, {{text_color|default('black text')}}.
- All diagrams (flowcharts, class diagrams, sequence diagrams) must use **{{diagram_format|default('Mermaid')}}** syntax.
- The entire document must be a **single scrollable HTML page**—no JavaScript, tabs, or interactivity.
- Ensure it is **responsive** and suitable for modal views or embedded previews.

**HTML Output Rules**:

- Organize documentation into logical sections: {{documentation_sections|default('Overview, Functional, Technical, Appendix')}}.
- Write the output incrementally section-by-section.
- At the end, write the full HTML to: `documentation/{{object_name}}_documentation.html`

**Documentation Structure**: 
Organize the documentation into the following sections:

{{section_1|default('1. Overview
   1.1 Purpose and Functionality  
   1.2 Business Context
   1.3 Benefits
   1.4 Key Features')}}

{{section_2|default('2. Functional Documentation
   2.1 User Guide
   2.1.1 Accessing the Functionality
   2.1.2 Input Parameters
   2.1.3 Main Screen(s)
   2.1.4 Output
   2.1.5 Customizing Options
   2.1.6 Troubleshooting
   2.2 Example Scenarios')}}

{{section_3|default('3. Technical Documentation
   3.1 Technical Architecture
   3.1.1 Summary
   3.1.2 Key Objects (with diagram)
   3.1.3 Data Flow (with diagram)
   3.2 Object Details (for each significant object)
   3.2.1 Details
   3.2.2 Data Flow (with diagram)
   3.3 Data Structures
   3.4 Error Handling
   3.5 Enhancements/Custom Exits')}}

{{section_4|default('4. Appendix
   4.1 List of all objects in the development
   4.2 Glossary of Terms')}}

**Audience**:  
{{target_audience|default('SAP developers, functional consultants, solution architects, business analysts, and auditors')}}.

**Tone**:  
{{documentation_tone|default('Professional, concise, instructional')}}.

You are a documentation automation expert—produce clean, complete, and business-ready HTML documentation, dynamically structured based on the object's WRICEF category.

**Quality Standards**:
{{quality_standards|default('- Enterprise documentation standards
- Semantic HTML tags and clean layout  
- Professional styling with inline CSS
- Comprehensive coverage of functional and technical aspects
- Clear explanations suitable for both technical and non-technical audiences')}}""",
        variables={
            "object_name": {"type": "string", "default": "", "description": "Name of the ABAP object being documented"},
            "object_type": {"type": "string", "default": "Unknown", "description": "Type of ABAP object (PROG, CLAS, FUGR, TRAN, etc.)"},
            "color_scheme": {"type": "string", "default": "black-and-white", "description": "Color scheme for documentation"},
            "background_color": {"type": "string", "default": "white background", "description": "Background color"},
            "text_color": {"type": "string", "default": "black text", "description": "Text color"},
            "diagram_format": {"type": "string", "default": "Mermaid", "description": "Format for diagrams"},
            "documentation_sections": {"type": "string", "default": "Overview, Functional, Technical, Appendix", "description": "Main documentation sections"},
            "target_audience": {"type": "string", "default": "SAP developers, functional consultants, solution architects, business analysts, and auditors", "description": "Target audience"},
            "documentation_tone": {"type": "string", "default": "Professional, concise, instructional", "description": "Documentation tone"}
        },
        category="ABAP",
        is_active=True
    )
    
    await template.save()
    print(f"✅ Created system prompt template: {template.template_id}")

async def create_documentation_mcp_server_registry():
    """Create MCP server registry entries for documentation"""
    
    server = MCPServerRegistry(
        server_id="abap-adt-api",
        name="ABAP ADT API MCP Server",
        description="MCP server for ABAP ADT API access - documentation generation",
        server_type="stdio",
        command="node",
        default_args=[],
        possible_locations=[
            r"C:\abap-adt-mcp\mcp-abap-abap-adt-api\dist\index.js",
            r"C:\Development Space\GenAI\New folder\mcp-abap-abap-adt-api\dist\index.js",
            "~/mcp-abap-abap-adt-api/dist/index.js",
            "./mcp-abap-abap-adt-api/dist/index.js"
        ],
        env_vars_required=["SAP_HOST", "SAP_USER", "SAP_PASSWORD"],
        auto_detect_enabled=True,
        health_check_command="node --version",
        category="SAP",
        is_active=True
    )
    
    existing = await MCPServerRegistry.find_one(
        MCPServerRegistry.server_id == server.server_id
    )
    if not existing:
        await server.save()
        print(f"✅ Created MCP server registry: {server.server_id}")
    else:
        print(f"⚠️  MCP server registry already exists: {server.server_id}")

async def create_documentation_tool_registry():
    """Create tool registry entries for documentation"""
    
    tools = [
        ToolRegistry(
            tool_id="file_write",
            name="File Write",
            description="Write content to file - builtin tool",
            tool_type="builtin",
            category="File",
            is_active=True
        )
    ]
    
    for tool in tools:
        existing = await ToolRegistry.find_one(
            ToolRegistry.tool_id == tool.tool_id
        )
        if not existing:
            await tool.save()
            print(f"✅ Created tool registry: {tool.tool_id}")
        else:
            print(f"⚠️  Tool registry already exists: {tool.tool_id}")

async def create_documentation_agent_template():
    """Create ABAP Documentation agent template"""
    
    template = AgentTemplate(
        template_id="abap-documentation-agent",
        name="ABAP Documentation Generator",
        description="Enterprise-grade functional and technical documentation generator for ABAP objects",
        category="ABAP",
        system_prompt_template="abap-documentation-prompt",
        default_model_config=ModelConfig(
            provider="bedrock",
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            temperature=0.3,
            max_tokens=64000,
            client_config={
                "read_timeout": 900,
                "connect_timeout": 50,
                "retries": {
                    "max_attempts": 3,
                    "mode": "standard"
                }
            }
        ),
        default_mcp_servers=[
            MCPServerConfig(
                server_type="stdio",
                server_name="abap-adt-api",
                command="node",
                args=[],
                auto_detect_path=True,
                possible_locations=[
                    r"C:\abap-adt-mcp\mcp-abap-abap-adt-api\dist\index.js",
                    r"C:\Development Space\GenAI\New folder\mcp-abap-abap-adt-api\dist\index.js",
                    "~/mcp-abap-abap-adt-api/dist/index.js"
                ],
                enabled=True,
                timeout=30
            )
        ],
        default_tools=[],
        default_builtin_tools=["file_write"],
        template_variables={
            "object_name": "",
            "object_type": "Unknown",
            "color_scheme": "black-and-white",
            "diagram_format": "Mermaid",
            "documentation_tone": "Professional, concise, instructional"
        },
        capabilities=[
            "ABAP Object Analysis",
            "Functional Documentation Generation", 
            "Technical Documentation Creation",
            "HTML Report Generation",
            "WRICEF Categorization",
            "Transaction Code Analysis",
            "Program Structure Analysis",
            "Data Flow Diagrams",
            "Mermaid Diagram Generation",
            "Enterprise Documentation Standards"
        ],
        tags=[
            "abap", "documentation", "sap", "html", "technical", "functional", 
            "enterprise", "wricef", "reports", "programs", "classes"
        ],
        is_active=True
    )
    
    existing = await AgentTemplate.find_one(
        AgentTemplate.template_id == template.template_id
    )
    if not existing:
        await template.save()
        print(f"✅ Created agent template: {template.template_id}")
    else:
        print(f"⚠️  Agent template already exists: {template.template_id}")

async def create_documentation_agent_instances():
    """Create ABAP Documentation agent instances from template"""
    
    agents = [
        {
            "agent_id": "abap-documentation-001",
            "name": "ABAP Documentation Generator - Standard",
            "description": "Standard ABAP documentation generator for all object types",
            "variables": {
                "object_name": "",
                "object_type": "Unknown",
                "color_scheme": "black-and-white",
                "documentation_tone": "Professional, concise, instructional",
                "target_audience": "SAP developers, functional consultants, solution architects, business analysts, and auditors"
            }
        }
    ]
    
    for agent_data in agents:
        existing = await AgentConfiguration.find_one(
            AgentConfiguration.agent_id == agent_data["agent_id"]
        )
        
        if not existing:
            agent_config = AgentConfiguration(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                description=agent_data["description"],
                system_prompt_template_id="abap-documentation-prompt",
                system_prompt_variables=agent_data["variables"],
                agent_model_config=ModelConfig(
                    provider="bedrock",
                    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
                    temperature=0.3,
                    max_tokens=64000,
                    client_config={
                        "read_timeout": 900,
                        "connect_timeout": 50,
                        "retries": {
                            "max_attempts": 3,
                            "mode": "standard"
                        }
                    }
                ),
                mcp_servers=[
                    MCPServerConfig(
                        server_type="stdio",
                        server_name="abap-adt-api",
                        command="node",
                        args=[],
                        auto_detect_path=True,
                        possible_locations=[
                            r"C:\abap-adt-mcp\mcp-abap-abap-adt-api\dist\index.js",
                            r"C:\Development Space\GenAI\New folder\mcp-abap-abap-adt-api\dist\index.js",
                            "~/mcp-abap-abap-adt-api/dist/index.js"
                        ],
                        enabled=True,
                        timeout=30
                    )
                ],
                tools=[],
                builtin_tools=["file_write"],
                timeout=900,
                capabilities=[
                    "ABAP Object Analysis",
                    "Functional Documentation Generation", 
                    "Technical Documentation Creation",
                    "HTML Report Generation",
                    "WRICEF Categorization"
                ],
                tags=[
                    "abap", "documentation", "sap", "html", "technical", "functional"
                ],
                template_id="abap-documentation-agent",
                is_active=True
            )
            
            await agent_config.save()
            print(f"✅ Created agent instance: {agent_config.agent_id}")
        else:
            print(f"⚠️  Agent instance already exists: {agent_data['agent_id']}")

async def main():
    """Setup all ABAP Documentation templates and registry"""
    print("🚀 Setting up ABAP Documentation Agent Templates and Registry...")
    
    await setup_database()
    
    # Create templates and registry
    await create_documentation_system_prompt_template()
    await create_documentation_mcp_server_registry()
    await create_documentation_tool_registry()
    await create_documentation_agent_template()
    await create_documentation_agent_instances()
    
    print("\n✅ ABAP Documentation Agent setup completed!")
    print("\n📋 What was created:")
    print("   • System prompt template with configurable variables for ABAP documentation")
    print("   • MCP server registry (ABAP ADT API)")
    print("   • Tool registry (file_write)")
    print("   • Agent template for ABAP documentation generation")
    print("   • Agent instance: abap-documentation-001")
    print("\n🚀 You can now use the REST API to execute the documentation agent:")
    print("   POST /api/v1/dynamic/execute/abap-documentation-001")

if __name__ == "__main__":
    asyncio.run(main())