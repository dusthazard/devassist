"""
Tool Collection module for managing collections of development tools.

This module provides a centralized system for:
- Registering and discovering development tools
- Loading tools dynamically
- Tool execution and error handling
- Tool management and organization
"""

from typing import Dict, List, Any, Optional, Type, Union
import importlib
import inspect
import logging
import os
import pkgutil

from devassist.tools.base.tool import BaseTool

class ToolCollection:
    """
    A collection of development tools with registration and discovery capabilities.
    
    Provides functionality for:
    - Registering tools
    - Loading tools dynamically
    - Tool discovery
    - Tool execution with error handling
    - Listing available tools
    """
    
    def __init__(self):
        """
        Initialize a ToolCollection instance.
        """
        self.tools: Dict[str, BaseTool] = {}
        self.tool_classes: Dict[str, Type[BaseTool]] = {}
        self.logger = logging.getLogger("devassist.tools")
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: The tool instance to register.
        """
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def register_tool_class(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class for later instantiation.
        
        Args:
            tool_class: The tool class to register.
        """
        name = getattr(tool_class, "name", tool_class.__name__.lower())
        self.tool_classes[name] = tool_class
        self.logger.info(f"Registered tool class: {name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool.
            
        Returns:
            The tool instance, or None if not found.
        """
        # Check if the tool is already instantiated
        if name in self.tools:
            return self.tools[name]
        
        # Check if we have the tool class and can instantiate it
        if name in self.tool_classes:
            try:
                tool = self.tool_classes[name]()
                self.register_tool(tool)
                return tool
            except Exception as e:
                self.logger.error(f"Error instantiating tool {name}: {e}")
                return None
        
        # Tool not found, try to load it dynamically
        try:
            # Try to find the tool in different subdirectories
            directories = ["dev", "utility"]
            for directory in directories:
                try:
                    module_path = f"devassist.tools.{directory}.{name}_tools"
                    module = importlib.import_module(module_path)
                    
                    # Look for a class that ends with 'Tool'
                    for attr_name in dir(module):
                        if attr_name.endswith('Tool'):
                            attr = getattr(module, attr_name)
                            if (inspect.isclass(attr) and 
                                issubclass(attr, BaseTool) and 
                                attr != BaseTool):
                                tool = attr()
                                self.register_tool(tool)
                                return tool
                except ImportError:
                    # Try next directory
                    continue
            
            # Try direct import as a top-level tool
            module_path = f"devassist.tools.{name}"
            module = importlib.import_module(module_path)
            
            # Look for a class that ends with 'Tool'
            for attr_name in dir(module):
                if attr_name.endswith('Tool'):
                    attr = getattr(module, attr_name)
                    if (inspect.isclass(attr) and 
                        issubclass(attr, BaseTool) and 
                        attr != BaseTool):
                        tool = attr()
                        self.register_tool(tool)
                        return tool
                    
        except Exception as e:
            self.logger.error(f"Error loading tool {name}: {e}")
        
        # Tool not found
        return None
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: The name of the tool to execute.
            **kwargs: Input parameters for the tool.
            
        Returns:
            The result of the tool execution, or an error message.
        """
        tool = self.get_tool(name)
        
        if tool is None:
            error_msg = f"Tool not found: {name}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        
        try:
            # Validate input if the tool provides validation
            if hasattr(tool, "validate_input") and not tool.validate_input(**kwargs):
                error_msg = f"Invalid input for tool {name}"
                self.logger.error(error_msg)
                return {"status": "error", "error": error_msg}
            
            # Execute the tool
            self.logger.debug(f"Executing tool: {name}")
            result = tool.execute(**kwargs)
            
            # If the result is already a dictionary with status info, return it directly
            if isinstance(result, dict) and "status" in result:
                return result
            
            # Otherwise, wrap it in a success response
            return {"status": "success", "result": result}
            
        except Exception as e:
            error_msg = f"Error executing tool {name}: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.
        
        Returns:
            A list of tool information dictionaries.
        """
        tool_info = []
        
        # Add instantiated tools
        for name, tool in self.tools.items():
            info = {
                "name": name,
                "description": getattr(tool, "description", "No description available"),
                "category": self._get_tool_category(tool),
                "parameters": getattr(tool, "parameters", {})
            }
            tool_info.append(info)
        
        # Add non-instantiated tool classes
        for name, tool_class in self.tool_classes.items():
            if name not in self.tools:
                info = {
                    "name": name,
                    "description": getattr(tool_class, "description", "No description available"),
                    "category": self._get_tool_class_category(tool_class),
                    "parameters": getattr(tool_class, "parameters", {})
                }
                tool_info.append(info)
        
        # Sort by category and name
        tool_info.sort(key=lambda x: (x.get("category", ""), x.get("name", "")))
        
        return tool_info
    
    def list_tools_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all available tools organized by category.
        
        Returns:
            A dictionary mapping categories to lists of tools.
        """
        tools = self.list_tools()
        categories: Dict[str, List[Dict[str, Any]]] = {}
        
        for tool in tools:
            category = tool.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        return categories
    
    def discover_tools(self, package_name: str = "devassist.tools") -> int:
        """
        Discover tools in the specified package.
        
        Args:
            package_name: The package to search for tools.
            
        Returns:
            The number of tools discovered.
        """
        count = 0
        
        try:
            package = importlib.import_module(package_name)
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                if is_pkg:
                    # Recursively discover tools in subpackages
                    count += self.discover_tools(name)
                else:
                    # Import the module
                    try:
                        module = importlib.import_module(name)
                        
                        # Find tool classes in the module
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            
                            # Check if it's a tool class
                            if (
                                inspect.isclass(attr) and 
                                issubclass(attr, BaseTool) and 
                                attr != BaseTool
                            ):
                                self.register_tool_class(attr)
                                count += 1
                    except Exception as e:
                        self.logger.error(f"Error discovering tools in module {name}: {e}")
        except Exception as e:
            self.logger.error(f"Error discovering tools in package {package_name}: {e}")
        
        self.logger.info(f"Discovered {count} tools in {package_name}")
        return count
    
    def _get_tool_category(self, tool: BaseTool) -> str:
        """
        Get the category of a tool.
        
        Args:
            tool: The tool instance.
            
        Returns:
            The category as a string.
        """
        # If the tool has a category attribute, use it
        if hasattr(tool, "category"):
            return getattr(tool, "category")
        
        # Otherwise, infer from the module path
        module = tool.__class__.__module__
        
        # Handle special paths
        if ".dev." in module:
            return "Development"
        elif ".utility." in module:
            return "Utility"
        elif ".search" in module:
            return "Search"
        elif ".code" in module:
            return "Code"
        elif ".text" in module:
            return "Text"
        
        # Default to "Other"
        return "Other"
    
    def _get_tool_class_category(self, tool_class: Type[BaseTool]) -> str:
        """
        Get the category of a tool class.
        
        Args:
            tool_class: The tool class.
            
        Returns:
            The category as a string.
        """
        # If the class has a category attribute, use it
        if hasattr(tool_class, "category"):
            return getattr(tool_class, "category")
        
        # Otherwise, infer from the module path
        module = tool_class.__module__
        
        # Handle special paths
        if ".dev." in module:
            return "Development"
        elif ".utility." in module:
            return "Utility"
        elif ".search" in module:
            return "Search"
        elif ".code" in module:
            return "Code"
        elif ".text" in module:
            return "Text"
        
        # Default to "Other"
        return "Other"
