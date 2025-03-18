"""
Frontend development tools for generating and manipulating frontend code.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Union

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class ReactComponentTool(BaseTool):
    """
    Tool for generating React components and related code.
    """
    
    name = "react_component"
    description = "Generate React component code"
    parameters = {
        "type": "object",
        "properties": {
            "component_name": {
                "type": "string",
                "description": "Name of the React component to generate"
            },
            "component_type": {
                "type": "string",
                "description": "Type of component to generate (functional, class, hook)",
                "enum": ["functional", "class", "hook"]
            },
            "props": {
                "type": "array",
                "description": "List of props for the component",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the prop"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of the prop (string, number, boolean, etc.)"
                        },
                        "default": {
                            "type": "string",
                            "description": "Default value for the prop (as a string)"
                        },
                        "required": {
                            "type": "boolean",
                            "description": "Whether the prop is required"
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "description": {
                "type": "string",
                "description": "Description of the component"
            },
            "use_typescript": {
                "type": "boolean",
                "description": "Whether to generate TypeScript code",
                "default": False
            }
        },
        "required": ["component_name", "component_type"]
    }
    
    def execute(self, 
                component_name: str,
                component_type: str = "functional",
                props: Optional[List[Dict[str, Any]]] = None,
                description: Optional[str] = None,
                use_typescript: bool = False,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate a React component based on the given specifications.
        
        Args:
            component_name: Name of the React component to generate.
            component_type: Type of component to generate (functional, class, hook).
            props: List of props for the component.
            description: Description of the component.
            use_typescript: Whether to generate TypeScript code.
            **kwargs: Additional parameters.
            
        Returns:
            The generated component code.
        """
        try:
            # Validate inputs
            if not self._is_valid_component_name(component_name):
                return ToolResult.error(
                    self.name,
                    f"Invalid component name: {component_name}. Component names should be in PascalCase."
                )
            
            if component_type not in ["functional", "class", "hook"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid component type: {component_type}. Valid types are: functional, class, hook."
                )
            
            # Normalize props
            props = props or []
            
            # Generate appropriate component code
            file_extension = "tsx" if use_typescript else "jsx"
            
            if component_type == "functional":
                code = self._generate_functional_component(component_name, props, description, use_typescript)
            elif component_type == "class":
                code = self._generate_class_component(component_name, props, description, use_typescript)
            else:  # hook
                code = self._generate_hook(component_name, description, use_typescript)
            
            return ToolResult.success(
                self.name,
                {
                    "code": code,
                    "component_name": component_name,
                    "file_name": f"{component_name}.{file_extension}",
                    "component_type": component_type,
                    "language": "typescript" if use_typescript else "javascript"
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating React component: {e}")
            return ToolResult.error(self.name, f"Failed to generate component: {str(e)}")
    
    def _is_valid_component_name(self, name: str) -> bool:
        """
        Check if the component name is valid (PascalCase).
        
        Args:
            name: Component name to validate.
            
        Returns:
            True if the name is valid, False otherwise.
        """
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
    
    def _generate_functional_component(self,
                                      name: str,
                                      props: List[Dict[str, Any]],
                                      description: Optional[str] = None,
                                      use_typescript: bool = False) -> str:
        """
        Generate a functional React component.
        
        Args:
            name: Component name.
            props: List of props.
            description: Component description.
            use_typescript: Whether to use TypeScript.
            
        Returns:
            The generated component code.
        """
        # Generate props interface/type for TypeScript
        props_type = ""
        if use_typescript:
            props_type = f"interface {name}Props {{\n"
            for prop in props:
                prop_name = prop["name"]
                prop_type = prop["type"]
                required = prop.get("required", False)
                
                # Add optional marker (?) if not required
                optional_marker = "" if required else "?"
                props_type += f"  {prop_name}{optional_marker}: {prop_type};\n"
            
            props_type += "}\n\n"
        
        # Generate JSDoc comment
        jsdoc = ""
        if description:
            jsdoc = "/**\n"
            jsdoc += f" * {description}\n"
            jsdoc += " *\n"
            
            # Add prop documentation
            for prop in props:
                prop_name = prop["name"]
                prop_desc = prop.get("description", f"The {prop_name} prop")
                jsdoc += f" * @param {{{prop['type']}}} {prop_name} - {prop_desc}\n"
            
            jsdoc += " */\n"
        
        # Generate imports
        imports = "import React from 'react';\n\n"
        
        # Generate component
        component = ""
        if use_typescript:
            component += props_type
            component += jsdoc
            component += f"const {name}: React.FC<{name}Props> = ({{"
        else:
            component += jsdoc
            component += f"const {name} = ({{"
        
        # Add props
        if props:
            component += " " + ", ".join([prop["name"] for prop in props]) + " "
        
        component += "}) => {\n"
        component += "  return (\n"
        component += "    <div>\n"
        component += f"      <h2>{name}</h2>\n"
        component += "      {/* Add your component content here */}\n"
        component += "    </div>\n"
        component += "  );\n"
        component += "};\n\n"
        
        # Generate prop default values for non-TypeScript
        if not use_typescript and props:
            component += f"{name}.defaultProps = {{\n"
            for prop in props:
                if "default" in prop:
                    component += f"  {prop['name']}: {prop['default']},\n"
            component += "};\n\n"
        
        # Add export
        component += f"export default {name};\n"
        
        return imports + component

    def _generate_class_component(self,
                                 name: str,
                                 props: List[Dict[str, Any]],
                                 description: Optional[str] = None,
                                 use_typescript: bool = False) -> str:
        """
        Generate a class-based React component.
        
        Args:
            name: Component name.
            props: List of props.
            description: Component description.
            use_typescript: Whether to use TypeScript.
            
        Returns:
            The generated component code.
        """
        # Generate props/state interfaces for TypeScript
        types = ""
        if use_typescript:
            # Props interface
            types += f"interface {name}Props {{\n"
            for prop in props:
                prop_name = prop["name"]
                prop_type = prop["type"]
                required = prop.get("required", False)
                
                # Add optional marker (?) if not required
                optional_marker = "" if required else "?"
                types += f"  {prop_name}{optional_marker}: {prop_type};\n"
            types += "}\n\n"
            
            # State interface
            types += f"interface {name}State {{\n"
            types += "  loading: boolean;\n"
            types += "}\n\n"
        
        # Generate JSDoc comment
        jsdoc = ""
        if description:
            jsdoc = "/**\n"
            jsdoc += f" * {description}\n"
            jsdoc += " */\n"
        
        # Generate imports
        imports = "import React, { Component } from 'react';\n\n"
        
        # Generate component
        component = ""
        if use_typescript:
            component += types
            component += jsdoc
            component += f"class {name} extends Component<{name}Props, {name}State> {{\n"
        else:
            component += jsdoc
            component += f"class {name} extends Component {{\n"
        
        # Add constructor
        component += "  constructor(props) {\n"
        component += "    super(props);\n"
        component += "    this.state = {\n"
        component += "      loading: false,\n"
        component += "    };\n"
        component += "  }\n\n"
        
        # Add componentDidMount
        component += "  componentDidMount() {\n"
        component += "    // Initialization logic\n"
        component += "  }\n\n"
        
        # Add render method
        component += "  render() {\n"
        component += "    return (\n"
        component += "      <div>\n"
        component += f"        <h2>{name}</h2>\n"
        component += "        {/* Add your component content here */}\n"
        component += "      </div>\n"
        component += "    );\n"
        component += "  }\n"
        component += "}\n\n"
        
        # Generate prop default values
        if props:
            component += f"{name}.defaultProps = {{\n"
            for prop in props:
                if "default" in prop:
                    component += f"  {prop['name']}: {prop['default']},\n"
            component += "};\n\n"
        
        # Add export
        component += f"export default {name};\n"
        
        return imports + component

    def _generate_hook(self,
                      name: str,
                      description: Optional[str] = None,
                      use_typescript: bool = False) -> str:
        """
        Generate a React hook.
        
        Args:
            name: Hook name (should start with 'use').
            description: Hook description.
            use_typescript: Whether to use TypeScript.
            
        Returns:
            The generated hook code.
        """
        # Ensure hook name starts with 'use'
        if not name.startswith("use"):
            name = "use" + name
        
        # Generate JSDoc comment
        jsdoc = ""
        if description:
            jsdoc = "/**\n"
            jsdoc += f" * {description}\n"
            jsdoc += " *\n"
            jsdoc += f" * @returns {{object}} Hook state and functions\n"
            jsdoc += " */\n"
        
        # Generate imports
        imports = "import { useState, useEffect } from 'react';\n\n"
        
        # Generate hook
        hook = ""
        hook += jsdoc
        if use_typescript:
            hook += f"function {name}() {{\n"
        else:
            hook += f"function {name}() {{\n"
        
        # Add state
        hook += "  const [loading, setLoading] = useState(false);\n"
        hook += "  const [data, setData] = useState(null);\n"
        hook += "  const [error, setError] = useState(null);\n\n"
        
        # Add useEffect
        hook += "  useEffect(() => {\n"
        hook += "    // Effect logic here\n"
        hook += "    return () => {\n"
        hook += "      // Cleanup logic here\n"
        hook += "    };\n"
        hook += "  }, []);\n\n"
        
        # Add example function
        hook += "  const fetchData = async () => {\n"
        hook += "    try {\n"
        hook += "      setLoading(true);\n"
        hook += "      // Fetch data logic\n"
        hook += "      setLoading(false);\n"
        hook += "    } catch (err) {\n"
        hook += "      setError(err);\n"
        hook += "      setLoading(false);\n"
        hook += "    }\n"
        hook += "  };\n\n"
        
        # Return hook values
        hook += "  return {\n"
        hook += "    loading,\n"
        hook += "    data,\n"
        hook += "    error,\n"
        hook += "    fetchData,\n"
        hook += "  };\n"
        hook += "}\n\n"
        
        # Add export
        hook += f"export default {name};\n"
        
        return imports + hook


class CssGeneratorTool(BaseTool):
    """
    Tool for generating CSS/SCSS code.
    """
    
    name = "css_generator"
    description = "Generate CSS, SCSS, or styled-components code"
    parameters = {
        "type": "object",
        "properties": {
            "component_name": {
                "type": "string",
                "description": "Name of the component to style"
            },
            "style_type": {
                "type": "string",
                "description": "Type of styling code to generate",
                "enum": ["css", "scss", "styled-components", "css-modules", "tailwind"]
            },
            "elements": {
                "type": "array",
                "description": "List of elements to style",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the element (e.g., 'container', 'button')"
                        },
                        "styles": {
                            "type": "object",
                            "description": "CSS styles for the element"
                        }
                    },
                    "required": ["name", "styles"]
                }
            },
            "description": {
                "type": "string",
                "description": "Description of the styling"
            }
        },
        "required": ["component_name", "style_type"]
    }
    
    def execute(self,
                component_name: str,
                style_type: str = "css",
                elements: Optional[List[Dict[str, Any]]] = None,
                description: Optional[str] = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate CSS/SCSS/styled-components code based on specifications.
        
        Args:
            component_name: Name of the component to style.
            style_type: Type of styling code to generate.
            elements: List of elements to style.
            description: Description of the styling.
            **kwargs: Additional parameters.
            
        Returns:
            The generated styling code.
        """
        try:
            # Validate inputs
            if style_type not in ["css", "scss", "styled-components", "css-modules", "tailwind"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid style type: {style_type}. Valid types are: css, scss, styled-components, css-modules, tailwind."
                )
            
            # Normalize elements
            elements = elements or [
                {
                    "name": "container",
                    "styles": {
                        "display": "flex",
                        "flex-direction": "column",
                        "padding": "1rem"
                    }
                },
                {
                    "name": "title",
                    "styles": {
                        "font-size": "1.5rem",
                        "font-weight": "bold",
                        "margin-bottom": "1rem"
                    }
                }
            ]
            
            # Generate code based on style type
            if style_type == "css":
                code = self._generate_css(component_name, elements, description)
                file_extension = "css"
            elif style_type == "scss":
                code = self._generate_scss(component_name, elements, description)
                file_extension = "scss"
            elif style_type == "styled-components":
                code = self._generate_styled_components(component_name, elements, description)
                file_extension = "js"
            elif style_type == "css-modules":
                code = self._generate_css_modules(component_name, elements, description)
                file_extension = "module.css"
            else:  # tailwind
                code = self._generate_tailwind_classes(component_name, elements, description)
                file_extension = "tailwind.txt"
            
            return ToolResult.success(
                self.name,
                {
                    "code": code,
                    "component_name": component_name,
                    "file_name": f"{self._format_file_name(component_name)}.{file_extension}",
                    "style_type": style_type
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating CSS/SCSS code: {e}")
            return ToolResult.error(self.name, f"Failed to generate styling code: {str(e)}")
    
    def _format_file_name(self, name: str) -> str:
        """
        Format a component name for a file name (camelCase or PascalCase to kebab-case).
        
        Args:
            name: The component name.
            
        Returns:
            The formatted file name.
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    
    def _generate_css(self,
                     component_name: str,
                     elements: List[Dict[str, Any]],
                     description: Optional[str] = None) -> str:
        """
        Generate CSS code.
        
        Args:
            component_name: Component name.
            elements: Elements to style.
            description: Style description.
            
        Returns:
            The generated CSS code.
        """
        css = ""
        
        # Add description as comment
        if description:
            css += f"/* {description} */\n\n"
        
        # Format component name for CSS class (PascalCase to kebab-case)
        base_class = self._format_file_name(component_name)
        
        # Generate CSS for each element
        for element in elements:
            element_name = element["name"]
            styles = element["styles"]
            
            # Create class name
            class_name = f".{base_class}" if element_name == "container" else f".{base_class}__{element_name}"
            
            css += f"{class_name} {{\n"
            
            # Add styles
            for property_name, value in styles.items():
                css += f"  {property_name}: {value};\n"
            
            css += "}\n\n"
        
        return css.strip()
    
    def _generate_scss(self,
                      component_name: str,
                      elements: List[Dict[str, Any]],
                      description: Optional[str] = None) -> str:
        """
        Generate SCSS code.
        
        Args:
            component_name: Component name.
            elements: Elements to style.
            description: Style description.
            
        Returns:
            The generated SCSS code.
        """
        scss = ""
        
        # Add description as comment
        if description:
            scss += f"/* {description} */\n\n"
        
        # Format component name for SCSS class (PascalCase to kebab-case)
        base_class = self._format_file_name(component_name)
        
        # Generate SCSS with nesting
        scss += f".{base_class} {{\n"
        
        # Add container styles
        container = next((e for e in elements if e["name"] == "container"), None)
        if container:
            for property_name, value in container["styles"].items():
                scss += f"  {property_name}: {value};\n"
            
            # Add nested elements
            for element in elements:
                if element["name"] != "container":
                    element_name = element["name"]
                    styles = element["styles"]
                    
                    scss += f"\n  &__{element_name} {{\n"
                    
                    # Add styles
                    for property_name, value in styles.items():
                        scss += f"    {property_name}: {value};\n"
                    
                    scss += "  }\n"
        else:
            # No container element, just add all elements at top level
            for element in elements:
                element_name = element["name"]
                styles = element["styles"]
                
                if element_name == "container":
                    # Add container styles directly
                    for property_name, value in styles.items():
                        scss += f"  {property_name}: {value};\n"
                else:
                    # Nest other elements
                    scss += f"\n  &__{element_name} {{\n"
                    
                    # Add styles
                    for property_name, value in styles.items():
                        scss += f"    {property_name}: {value};\n"
                    
                    scss += "  }\n"
        
        scss += "}\n"
        
        return scss.strip()
    
    def _generate_styled_components(self,
                                   component_name: str,
                                   elements: List[Dict[str, Any]],
                                   description: Optional[str] = None) -> str:
        """
        Generate styled-components code.
        
        Args:
            component_name: Component name.
            elements: Elements to style.
            description: Style description.
            
        Returns:
            The generated styled-components code.
        """
        styled = "import styled from 'styled-components';\n\n"
        
        # Add description as comment
        if description:
            styled += f"// {description}\n\n"
        
        # Generate styled component for each element
        for element in elements:
            element_name = element["name"]
            styles = element["styles"]
            
            # Capitalize first letter for styled component name
            styled_name = element_name[0].upper() + element_name[1:]
            if element_name == "container":
                styled_name = "Container"
            else:
                styled_name = f"{styled_name}"
            
            # Determine HTML element based on element name
            html_element = "div"
            if element_name == "title" or element_name == "heading":
                html_element = "h2"
            elif element_name == "subtitle":
                html_element = "h3"
            elif element_name == "text" or element_name == "paragraph":
                html_element = "p"
            elif element_name == "button":
                html_element = "button"
            elif element_name == "input":
                html_element = "input"
            elif element_name == "image":
                html_element = "img"
            
            styled += f"export const Styled{styled_name} = styled.{html_element}`\n"
            
            # Add styles
            for property_name, value in styles.items():
                styled += f"  {property_name}: {value};\n"
            
            styled += "`;\n\n"
        
        return styled.strip()
    
    def _generate_css_modules(self,
                             component_name: str,
                             elements: List[Dict[str, Any]],
                             description: Optional[str] = None) -> str:
        """
        Generate CSS modules code.
        
        Args:
            component_name: Component name.
            elements: Elements to style.
            description: Style description.
            
        Returns:
            The generated CSS modules code.
        """
        css = ""
        
        # Add description as comment
        if description:
            css += f"/* {description} */\n\n"
        
        # Generate CSS for each element
        for element in elements:
            element_name = element["name"]
            styles = element["styles"]
            
            # Create class name
            class_name = element_name
            
            css += f".{class_name} {{\n"
            
            # Add styles
            for property_name, value in styles.items():
                css += f"  {property_name}: {value};\n"
            
            css += "}\n\n"
        
        return css.strip()
    
    def _generate_tailwind_classes(self,
                                  component_name: str,
                                  elements: List[Dict[str, Any]],
                                  description: Optional[str] = None) -> str:
        """
        Generate Tailwind CSS classes.
        
        Args:
            component_name: Component name.
            elements: Elements to style.
            description: Style description.
            
        Returns:
            The generated Tailwind classes.
        """
        tailwind = ""
        
        # Add description as comment
        if description:
            tailwind += f"/* {description} */\n\n"
        
        # CSS property to Tailwind class mapping (simplified)
        css_to_tailwind = {
            "display": {
                "flex": "flex",
                "block": "block",
                "inline": "inline",
                "grid": "grid",
                "none": "hidden"
            },
            "flex-direction": {
                "row": "flex-row",
                "column": "flex-col"
            },
            "align-items": {
                "center": "items-center",
                "flex-start": "items-start",
                "flex-end": "items-end"
            },
            "justify-content": {
                "center": "justify-center",
                "space-between": "justify-between",
                "flex-start": "justify-start",
                "flex-end": "justify-end"
            },
            "padding": {
                "1rem": "p-4",
                "0.5rem": "p-2",
                "0.25rem": "p-1"
            },
            "margin": {
                "1rem": "m-4",
                "0.5rem": "m-2",
                "0.25rem": "m-1"
            },
            "margin-bottom": {
                "1rem": "mb-4",
                "0.5rem": "mb-2",
                "0.25rem": "mb-1"
            },
            "font-size": {
                "1.5rem": "text-2xl",
                "1.25rem": "text-xl",
                "1rem": "text-base",
                "0.875rem": "text-sm"
            },
            "font-weight": {
                "bold": "font-bold",
                "normal": "font-normal",
                "600": "font-semibold"
            }
        }
        
        # Generate Tailwind classes for each element
        for element in elements:
            element_name = element["name"]
            styles = element["styles"]
            
            tailwind += f"<!-- {element_name} -->\n"
            tailwind += f"className=\""
            
            # Convert CSS styles to Tailwind classes
            tailwind_classes = []
            for property_name, value in styles.items():
                if property_name in css_to_tailwind and value in css_to_tailwind[property_name]:
                    tailwind_classes.append(css_to_tailwind[property_name][value])
                else:
                    # For properties/values not in our mapping, add a comment
                    tailwind += f"/* {property_name}: {value} */\n"
            
            tailwind += " ".join(tailwind_classes)
            tailwind += "\"\n\n"
        
        return tailwind.strip()


# Add more frontend tools as needed