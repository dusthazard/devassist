# DevAssist

An autonomous development assistant for software development tasks

![version](https://img.shields.io/badge/version-0.1.0-blue)
![python](https://img.shields.io/badge/python-3.11+-green)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

## Overview

DevAssist is an intelligent assistant framework designed to help developers with various software development tasks. It combines the power of language models with specialized tools to provide actionable assistance for coding, database design, API development, and more. DevAssist acts as your AI pair programmer, reducing cognitive load and automating repetitive development tasks.

## Features

- **Intelligent Task Planning**: Breaks down complex development tasks into manageable steps
- **Tool-Augmented Assistance**: Specialized tools for code generation, API design, database management and more
- **Multi-Agent Architecture**: Collaborative problem-solving with specialized agent roles
- **Memory Systems**: Both short-term and long-term memory to maintain context
- **Adaptive Response Generation**: Tailors responses based on task complexity and developer needs

## Installation

```bash
# Install from PyPI
pip install devassist

# Or install from source
git clone https://github.com/username/devassist.git
cd devassist
pip install -e .
```

### Requirements

- Python 3.11+
- OpenAI API key or other supported LLM provider

## Quick Start

### Command Line Interface

DevAssist includes a command-line interface for direct interaction:

```bash
# Set up your API key
export OPENAI_API_KEY=your_api_key

# Start DevAssist in interactive mode
devassist

# Or execute a specific task
devassist --task "Create a FastAPI endpoint for user authentication"
```

### Python API

```python
from devassist.core.orchestrator import AgentOrchestrator

# Initialize the orchestrator
orchestrator = AgentOrchestrator()

# Execute a development task
result = orchestrator.execute_task(
    "Generate a React component for displaying user profiles with Tailwind CSS styling"
)

# Access the result
print(result["answer"])
```

## Core Components

### Agents

DevAssist uses a hybrid agent architecture that can dynamically switch between single and multi-agent modes based on task complexity:

- **Single Agent Mode**: Handles simple, straightforward tasks efficiently
- **Multi-Agent Mode**: Orchestrates multiple specialized agents for complex tasks:
  - Researcher: Gathers information and analyzes requirements
  - Planner: Develops strategy and approach
  - Executor: Implements the solution
  - Critic: Evaluates and refines the output

### Tools

DevAssist comes with specialized development tools:

#### Backend Tools
- **API Endpoint Generator**: Creates API endpoints for various frameworks (Express, FastAPI, Flask, Django, Spring)
- **Database Model Generator**: Generates ORM models for different database frameworks

#### Frontend Tools
- **React Component Generator**: Creates functional, class, or hook-based React components
- **CSS Generator**: Generates CSS, SCSS, styled-components, or Tailwind classes

#### Database Tools
- **SQL Generator**: Creates SQL queries and schemas for different database systems
- **NoSQL Generator**: Generates NoSQL database operations (MongoDB, DynamoDB, Firebase, etc.)

#### Utility Tools
- **Calculator**: Performs mathematical calculations and conversions
- **Text Tool**: Handles text processing and formatting
- **Search Tool**: Finds documentation, examples, and resources
- **Code Tool**: Executes Python code in a secure sandbox

## Configuration

DevAssist can be configured using a YAML file:

```yaml
# config.yaml
agent:
  name: devassist
  mode: auto
  max_iterations: 10
  complexity_threshold: 7

memory:
  short_term:
    capacity: 1000
    ttl: 3600
  long_term:
    enabled: true
    storage_path: null
    index_in_memory: true

models:
  default:
    provider: openai
    model: gpt-4
    temperature: 0.0

tools:
  enabled:
    - api_endpoint
    - database_model
    - react_component
    - calculator
    - search
    - text
```

## Example Use Cases

### 1. API Endpoint Development

```python
# Generate a FastAPI endpoint for user authentication
result = orchestrator.execute_task(
    "Create a FastAPI endpoint for user authentication with JSON Web Token"
)
```

This will produce a complete FastAPI endpoint with:
- Request/response models with validation
- JWT token generation and verification
- Password hashing and security measures
- Error handling and documentation

### 2. Frontend Component Creation

```python
# Generate a React data visualization component
result = orchestrator.execute_task(
    "Create a React component for displaying sales data in a line chart using recharts"
)
```

The output includes:
- A functional React component with TypeScript typing
- Data processing functions
- Responsive chart configuration
- Props documentation

### 3. Database Schema Design

```python
# Generate a database schema for a blog application
result = orchestrator.execute_task(
    "Design a PostgreSQL database schema for a blog with users, posts, comments, and tags"
)
```

DevAssist will create:
- Complete SQL schema with proper relationships
- Indexes for performance optimization
- Constraints for data integrity
- Explanations of design decisions

### 4. Full-Stack Feature Implementation

For more complex tasks, DevAssist can orchestrate the development of full features:

```python
# Implement a complete feature
result = orchestrator.execute_task(
    """
    Implement a user profile management feature for a web application with:
    - React frontend with form validation
    - Express API endpoints for CRUD operations
    - MongoDB schema design
    - JWT authentication integration
    """
)
```

## Advanced Usage

### Task Planning

DevAssist includes a planning system that breaks down complex tasks:

```python
from devassist.core.planning.task_planner import TaskPlanner
from devassist.models.openai_model import OpenAIModel

# Create a model and planner
model = OpenAIModel(model_name="gpt-4")
planner = TaskPlanner(model)

# Create a development plan
plan = planner.create_plan(
    "Build a user authentication system with React and Express",
    context={
        "project": "web-app",
        "technology": {
            "stack": "mern",
            "frontend": "react",
            "backend": "express",
            "database": "mongodb"
        }
    }
)

# View the plan
print(planner.format_plan(plan))
```

### Tool Collections

You can directly use DevAssist's tools:

```python
from devassist.tools.base.tool_collection import ToolCollection

# Create a tool collection
tools = ToolCollection()

# Discover available tools
tools.discover_tools()

# Execute specific tools
result = tools.execute_tool(
    "api_endpoint",
    endpoint_name="UserAuthentication",
    http_method="POST",
    framework="fastapi",
    parameters=[
        {"name": "username", "type": "string", "location": "body", "required": True},
        {"name": "password", "type": "string", "location": "body", "required": True}
    ]
)

print(result["code"])
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [OpenAI API](https://openai.com/blog/openai-api)
- Uses various open-source libraries for development tools
