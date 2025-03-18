"""
Tool Agent module that extends the react agent with tool execution capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
import importlib
import logging
import re

from devassist.core.agent.react_agent import ReactAgent

class ToolAgent(ReactAgent):
    """
    An agent that can use tools to interact with its environment.
    
    Extends the ReactAgent with the ability to discover, load, and execute tools.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None, 
        max_iterations: int = 10, 
        tools: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a ToolAgent instance.
        
        Args:
            name: Optional name for the agent.
            max_iterations: Maximum number of thought-action cycles to perform.
            tools: Optional list of tool names to load.
            **kwargs: Additional configuration options for the agent.
        """
        super().__init__(name=name, max_iterations=max_iterations, **kwargs)
        self.tools: Dict[str, Any] = {}
        
        # Load specified tools or default tools
        if tools:
            for tool_name in tools:
                self.load_tool(tool_name)
    
    def load_tool(self, tool_name: str) -> bool:
        """
        Load a tool by name.
        
        Args:
            tool_name: The name of the tool to load.
            
        Returns:
            True if the tool was successfully loaded, False otherwise.
        """
        try:
            # Dynamically import the tool module
            module_path = f"devassist.tools.{tool_name}"
            module = importlib.import_module(module_path)
            
            # Get the tool class (assumed to be the same name as the module but capitalized)
            class_name = "".join(word.capitalize() for word in tool_name.split("_")) + "Tool"
            tool_class = getattr(module, class_name)
            
            # Instantiate the tool
            tool_instance = tool_class()
            
            # Register the tool
            self.tools[tool_name] = tool_instance
            
            self.log_action("load_tool", {"tool_name": tool_name, "status": "success"})
            logging.info(f"Agent '{self.name}' loaded tool: {tool_name}")
            return True
            
        except (ImportError, AttributeError, Exception) as e:
            self.log_action("load_tool", {"tool_name": tool_name, "status": "error", "error": str(e)})
            logging.error(f"Failed to load tool {tool_name}: {e}")
            return False
    
    def _decide_action(self, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Decide on the next action to take based on the task.
        
        Args:
            context: The current execution context.
            
        Returns:
            A tuple of (action_name, action_input).
        """
        task = context['task'].lower()
        
        # Check for calculator tasks
        calc_pattern = r'calculate\s+(.+)$'
        calc_match = re.search(calc_pattern, task, re.IGNORECASE)
        
        if calc_match and 'calculator' in self.tools:
            expression = calc_match.group(1).strip()
            logging.info(f"Agent '{self.name}' identified calculator task: '{expression}'")
            return "calculator", {"expression": expression}
            
        # Check for search tasks
        search_patterns = [
            r'search(?:\s+for)?\s+(.+)',
            r'find(?:\s+information(?:\s+about)?)?\s+(.+)',
            r'look\s+up\s+(.+)'
        ]
        
        for pattern in search_patterns:
            search_match = re.search(pattern, task, re.IGNORECASE)
            if search_match and 'search' in self.tools:
                query = search_match.group(1)
                logging.info(f"Agent '{self.name}' identified search task: '{query}'")
                return "search", {"query": query}
                
        # Check for text processing tasks
        text_patterns = {
            r'count\s+characters\s+in\s+[\'"](.+)[\'"]': ("count", lambda m: m.group(1)),
            r'count\s+words\s+in\s+[\'"](.+)[\'"]': ("wordcount", lambda m: m.group(1)),
            r'reverse\s+[\'"](.+)[\'"]': ("reverse", lambda m: m.group(1)),
            r'uppercase\s+[\'"](.+)[\'"]': ("uppercase", lambda m: m.group(1)),
            r'lowercase\s+[\'"](.+)[\'"]': ("lowercase", lambda m: m.group(1)),
            r'capitalize\s+[\'"](.+)[\'"]': ("capitalize", lambda m: m.group(1))
        }
        
        for pattern, (operation, extractor) in text_patterns.items():
            text_match = re.search(pattern, task, re.IGNORECASE)
            if text_match and 'text' in self.tools:
                text = extractor(text_match)
                logging.info(f"Agent '{self.name}' identified text task: '{operation}' on '{text}'")
                return "text", {"text": text, "operation": operation}
                
        # Check for code execution tasks
        code_patterns = [
            r'run\s+code\s+```(?:python)?\s*(.+?)```',
            r'execute\s+```(?:python)?\s*(.+?)```',
            r'evaluate\s+```(?:python)?\s*(.+?)```'
        ]
        
        for pattern in code_patterns:
            code_match = re.search(pattern, task, re.IGNORECASE | re.DOTALL)
            if code_match and 'code' in self.tools:
                code = code_match.group(1).strip()
                logging.info(f"Agent '{self.name}' identified code execution task")
                return "code", {"code": code}
        
        # Check for API endpoint generation tasks
        api_patterns = [
            r'create\s+(?:an?\s+)?api\s+endpoint\s+(?:for\s+)?(.+)',
            r'generate\s+(?:an?\s+)?api\s+(?:for\s+)?(.+)',
            r'implement\s+(?:an?\s+)?api\s+(?:for\s+)?(.+)'
        ]
        
        for pattern in api_patterns:
            api_match = re.search(pattern, task, re.IGNORECASE)
            if api_match and 'api_endpoint' in self.tools:
                endpoint_name = api_match.group(1).strip()
                logging.info(f"Agent '{self.name}' identified API endpoint task: '{endpoint_name}'")
                
                # Default to REST API with Express.js
                return "api_endpoint", {
                    "endpoint_name": endpoint_name,
                    "http_method": "GET",
                    "framework": "express"
                }
        
        # Check for React component generation tasks
        react_patterns = [
            r'create\s+(?:a\s+)?react\s+component\s+(?:for\s+)?(.+)',
            r'generate\s+(?:a\s+)?react\s+(?:component\s+)?(?:for\s+)?(.+)',
            r'implement\s+(?:a\s+)?react\s+(?:component\s+)?(?:for\s+)?(.+)'
        ]
        
        for pattern in react_patterns:
            react_match = re.search(pattern, task, re.IGNORECASE)
            if react_match and 'react_component' in self.tools:
                component_name = react_match.group(1).strip()
                # Convert to PascalCase for component name
                component_name = "".join(word.capitalize() for word in component_name.split())
                logging.info(f"Agent '{self.name}' identified React component task: '{component_name}'")
                
                return "react_component", {
                    "component_name": component_name,
                    "component_type": "functional",
                    "use_typescript": True
                }
                
        # If no specific task pattern matched, use a dummy action
        logging.info(f"Agent '{self.name}' could not identify specific task, using default action")
        return "dummy_action", {"query": f"Placeholder action for {task}"}
    
    def _execute_action(self, action_name: str, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action using the appropriate tool.
        
        Args:
            action_name: The name of the action/tool to execute.
            action_input: The input parameters for the action.
            
        Returns:
            The observation from executing the action.
        """
        # Check if the action corresponds to a loaded tool
        if action_name in self.tools:
            try:
                tool = self.tools[action_name]
                logging.info(f"Agent '{self.name}' executing tool: {action_name}")
                result = tool.execute(**action_input)
                
                # If result is already a dict with status, return it directly
                if isinstance(result, dict) and "status" in result:
                    return result
                    
                # Otherwise, wrap it in a success response
                return {"status": "success", "result": result}
                
            except Exception as e:
                error_message = f"Error executing tool {action_name}: {str(e)}"
                logging.error(error_message)
                return {"status": "error", "error": error_message}
        else:
            # Try to load the tool if it's not already loaded
            if self.load_tool(action_name):
                # Retry execution with the newly loaded tool
                return self._execute_action(action_name, action_input)
            
            error_message = f"Unknown action or tool: {action_name}"
            logging.error(error_message)
            return {"status": "error", "error": error_message}
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.
        
        Returns:
            A list of tool information dictionaries.
        """
        tool_info = []
        for name, tool in self.tools.items():
            info = {
                "name": name,
                "description": getattr(tool, "description", "No description available"),
                "parameters": getattr(tool, "parameters", {})
            }
            tool_info.append(info)
        return tool_info