"""
Backend development tools for generating and manipulating backend code.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class ApiEndpointTool(BaseTool):
    """
    Tool for generating API endpoint code for various frameworks.
    """
    
    name = "api_endpoint"
    description = "Generate API endpoint code for various frameworks"
    parameters = {
        "type": "object",
        "properties": {
            "endpoint_name": {
                "type": "string",
                "description": "Name of the API endpoint to generate"
            },
            "http_method": {
                "type": "string",
                "description": "HTTP method for the endpoint",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
            },
            "framework": {
                "type": "string",
                "description": "Backend framework to use",
                "enum": ["express", "fastapi", "flask", "django", "spring"]
            },
            "parameters": {
                "type": "array",
                "description": "List of parameters for the endpoint",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the parameter"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of the parameter (string, number, boolean, etc.)"
                        },
                        "location": {
                            "type": "string",
                            "description": "Where the parameter is located (query, path, body, header)",
                            "enum": ["query", "path", "body", "header"]
                        },
                        "required": {
                            "type": "boolean",
                            "description": "Whether the parameter is required"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the parameter"
                        }
                    },
                    "required": ["name", "type", "location"]
                }
            },
            "response": {
                "type": "object",
                "description": "Description of the response",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Response type (json, xml, text, etc.)"
                    },
                    "schema": {
                        "type": "object",
                        "description": "Schema of the response"
                    }
                },
                "required": ["type"]
            },
            "description": {
                "type": "string",
                "description": "Description of the endpoint"
            },
            "use_types": {
                "type": "boolean",
                "description": "Whether to use TypeScript/Python type hints",
                "default": True
            }
        },
        "required": ["endpoint_name", "http_method", "framework"]
    }
    
    def execute(self,
                endpoint_name: str,
                http_method: str,
                framework: str,
                parameters: Optional[List[Dict[str, Any]]] = None,
                response: Optional[Dict[str, Any]] = None,
                description: Optional[str] = None,
                use_types: bool = True,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate API endpoint code based on the given specifications.
        
        Args:
            endpoint_name: Name of the API endpoint to generate.
            http_method: HTTP method for the endpoint (GET, POST, PUT, DELETE, PATCH).
            framework: Backend framework to use.
            parameters: List of parameters for the endpoint.
            response: Description of the response.
            description: Description of the endpoint.
            use_types: Whether to use TypeScript/Python type hints.
            **kwargs: Additional parameters.
            
        Returns:
            The generated API endpoint code.
        """
        try:
            # Validate inputs
            if http_method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid HTTP method: {http_method}. Valid methods are: GET, POST, PUT, DELETE, PATCH."
                )
            
            if framework not in ["express", "fastapi", "flask", "django", "spring"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid framework: {framework}. Valid frameworks are: express, fastapi, flask, django, spring."
                )
            
            # Normalize parameters and response
            parameters = parameters or []
            response = response or {"type": "json", "schema": {"message": "string", "data": "object"}}
            
            # Generate appropriate endpoint code
            if framework == "express":
                code = self._generate_express_endpoint(endpoint_name, http_method, parameters, response, description, use_types)
                file_extension = "js" if not use_types else "ts"
            elif framework == "fastapi":
                code = self._generate_fastapi_endpoint(endpoint_name, http_method, parameters, response, description)
                file_extension = "py"
            elif framework == "flask":
                code = self._generate_flask_endpoint(endpoint_name, http_method, parameters, response, description, use_types)
                file_extension = "py"
            elif framework == "django":
                code = self._generate_django_endpoint(endpoint_name, http_method, parameters, response, description, use_types)
                file_extension = "py"
            else:  # spring
                code = self._generate_spring_endpoint(endpoint_name, http_method, parameters, response, description)
                file_extension = "java"
            
            # Determine route from endpoint name
            route = self._endpoint_name_to_route(endpoint_name)
            
            return ToolResult.success(
                self.name,
                {
                    "code": code,
                    "endpoint_name": endpoint_name,
                    "file_name": f"{self._endpoint_name_to_filename(endpoint_name)}.{file_extension}",
                    "framework": framework,
                    "http_method": http_method,
                    "route": route
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating API endpoint: {e}")
            return ToolResult.error(self.name, f"Failed to generate API endpoint: {str(e)}")
    
    def _endpoint_name_to_route(self, name: str) -> str:
        """
        Convert an endpoint name to a route path.
        
        Args:
            name: The endpoint name.
            
        Returns:
            The route path.
        """
        # Convert camelCase or PascalCase to kebab-case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        route = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
        
        # Add leading slash
        if not route.startswith('/'):
            route = '/' + route
        
        return route
    
    def _endpoint_name_to_filename(self, name: str) -> str:
        """
        Convert an endpoint name to a filename.
        
        Args:
            name: The endpoint name.
            
        Returns:
            The filename.
        """
        # Convert camelCase or PascalCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _generate_express_endpoint(self,
                                   endpoint_name: str,
                                   http_method: str,
                                   parameters: List[Dict[str, Any]],
                                   response: Dict[str, Any],
                                   description: Optional[str] = None,
                                   use_types: bool = True) -> str:
        """
        Generate Express.js (Node.js) API endpoint code.
        
        Args:
            endpoint_name: Endpoint name.
            http_method: HTTP method.
            parameters: Endpoint parameters.
            response: Response description.
            description: Endpoint description.
            use_types: Whether to use TypeScript.
            
        Returns:
            The generated Express.js endpoint code.
        """
        http_method = http_method.lower()
        route = self._endpoint_name_to_route(endpoint_name)
        
        # Start with imports
        if use_types:
            code = "import express, { Request, Response } from 'express';\n\n"
        else:
            code = "const express = require('express');\n\n"
        
        # Create router
        code += "const router = express.Router();\n\n"
        
        # Add JSDoc comment
        if description:
            code += "/**\n"
            code += f" * {description}\n"
            
            # Add parameter documentation
            for param in parameters:
                param_name = param["name"]
                param_type = param["type"]
                param_desc = param.get("description", f"The {param_name} parameter")
                location = param["location"]
                code += f" * @param {{{param_type}}} {param_name} - {param_desc} ({location})\n"
            
            # Add response documentation
            response_type = response.get("type", "json")
            code += f" * @returns {{object}} {response_type.upper()} response\n"
            code += " */\n"
        
        # Generate the endpoint
        code += f"router.{http_method}('{route}', "
        
        # Start the handler function
        if use_types:
            code += "(req: Request, res: Response) => {\n"
        else:
            code += "(req, res) => {\n"
        
        # Add parameter validation
        code += "  try {\n"
        
        # Extract parameters from request
        for param in parameters:
            param_name = param["name"]
            param_location = param["location"]
            required = param.get("required", False)
            
            # Get parameter based on location
            if param_location == "query":
                code += f"    const {param_name} = req.query.{param_name};\n"
            elif param_location == "path":
                code += f"    const {param_name} = req.params.{param_name};\n"
            elif param_location == "body":
                code += f"    const {param_name} = req.body.{param_name};\n"
            elif param_location == "header":
                code += f"    const {param_name} = req.headers['{param_name.toLowerCase()}'];\n"
            
            # Add validation for required parameters
            if required:
                code += f"    if ({param_name} === undefined || {param_name} === null) {{\n"
                code += f"      return res.status(400).json({{ error: '{param_name} is required' }});\n"
                code += "    }\n"
        
        code += "\n    // TODO: Implement the endpoint logic\n"
        
        # Prepare example response
        response_schema = response.get("schema", {})
        example_response = json.dumps(response_schema, indent=2)
        code += f"    const responseData = {example_response};\n\n"
        
        # Return response
        code += f"    return res.json(responseData);\n"
        code += "  } catch (error) {\n"
        code += "    console.error('Error handling request:', error);\n"
        code += "    return res.status(500).json({ error: 'Internal server error' });\n"
        code += "  }\n"
        code += "});\n\n"
        
        # Export the router
        if use_types:
            code += "export default router;\n"
        else:
            code += "module.exports = router;\n"
        
        return code
    
    def _generate_fastapi_endpoint(self,
                                  endpoint_name: str,
                                  http_method: str,
                                  parameters: List[Dict[str, Any]],
                                  response: Dict[str, Any],
                                  description: Optional[str] = None) -> str:
        """
        Generate FastAPI (Python) API endpoint code.
        
        Args:
            endpoint_name: Endpoint name.
            http_method: HTTP method.
            parameters: Endpoint parameters.
            response: Response description.
            description: Endpoint description.
            
        Returns:
            The generated FastAPI endpoint code.
        """
        http_method = http_method.lower()
        route = self._endpoint_name_to_route(endpoint_name)
        
        # Start with imports
        code = "from fastapi import APIRouter, Query, Path, Body, Header, HTTPException\n"
        code += "from typing import Optional, List, Dict, Any\n"
        code += "from pydantic import BaseModel\n\n"
        
        # Create router
        code += "router = APIRouter()\n\n"
        
        # Define request and response models if needed
        body_params = [p for p in parameters if p["location"] == "body"]
        if body_params:
            # Create request model
            code += f"class {endpoint_name.capitalize()}Request(BaseModel):\n"
            for param in body_params:
                param_name = param["name"]
                param_type = self._convert_type_to_python(param["type"])
                required = param.get("required", False)
                
                if required:
                    code += f"    {param_name}: {param_type}\n"
                else:
                    code += f"    {param_name}: Optional[{param_type}] = None\n"
            code += "\n"
        
        # Create response model
        code += f"class {endpoint_name.capitalize()}Response(BaseModel):\n"
        for key, value in response.get("schema", {}).items():
            py_type = self._convert_type_to_python(value)
            code += f"    {key}: {py_type}\n"
        code += "\n"
        
        # Generate the endpoint
        code += f"@router.{http_method}('{route}'"
        
        # Add response model
        code += f", response_model={endpoint_name.capitalize()}Response"
        
        # Add tags and description
        code += f", tags=['{endpoint_name.split('_')[0]}']"
        if description:
            code += f", description='{description}'"
        
        code += ")\n"
        
        # Start the function definition
        code += f"async def {self._endpoint_name_to_filename(endpoint_name)}("
        
        # Add function parameters
        function_params = []
        
        # Add path parameters
        path_params = [p for p in parameters if p["location"] == "path"]
        for param in path_params:
            param_name = param["name"]
            param_type = self._convert_type_to_python(param["type"])
            required = param.get("required", True)  # Path params are typically required
            
            param_str = f"{param_name}: {param_type} = Path(..., description='{param.get('description', '')}')"
            function_params.append(param_str)
        
        # Add query parameters
        query_params = [p for p in parameters if p["location"] == "query"]
        for param in query_params:
            param_name = param["name"]
            param_type = self._convert_type_to_python(param["type"])
            required = param.get("required", False)
            
            if required:
                param_str = f"{param_name}: {param_type} = Query(..., description='{param.get('description', '')}')"
            else:
                param_str = f"{param_name}: Optional[{param_type}] = Query(None, description='{param.get('description', '')}')"
            
            function_params.append(param_str)
        
        # Add body parameter
        if body_params:
            function_params.append(f"request: {endpoint_name.capitalize()}Request = Body(...)")
        
        # Add header parameters
        header_params = [p for p in parameters if p["location"] == "header"]
        for param in header_params:
            param_name = param["name"]
            param_type = self._convert_type_to_python(param["type"])
            required = param.get("required", False)
            
            if required:
                param_str = f"{param_name}: {param_type} = Header(..., description='{param.get('description', '')}')"
            else:
                param_str = f"{param_name}: Optional[{param_type}] = Header(None, description='{param.get('description', '')}')"
            
            function_params.append(param_str)
        
        # Add parameters to function definition
        code += ", ".join(function_params)
        code += "):\n"
        
        # Add docstring
        if description:
            code += f'    """{description}\n'
            code += '    """\n'
        
        # Add function body
        code += "    try:\n"
        code += "        # TODO: Implement the endpoint logic\n"
        
        # Prepare example response
        example_response = {}
        for key in response.get("schema", {}).keys():
            if key == "message":
                example_response[key] = "Success"
            elif key == "data":
                example_response[key] = "{}"
            else:
                example_response[key] = "example_value"
        
        code += f"        return {example_response}\n"
        code += "    except Exception as e:\n"
        code += "        raise HTTPException(status_code=500, detail=str(e))\n"
        
        return code
    
    def _generate_flask_endpoint(self,
                                endpoint_name: str,
                                http_method: str,
                                parameters: List[Dict[str, Any]],
                                response: Dict[str, Any],
                                description: Optional[str] = None,
                                use_types: bool = True) -> str:
        """
        Generate Flask (Python) API endpoint code.
        
        Args:
            endpoint_name: Endpoint name.
            http_method: HTTP method.
            parameters: Endpoint parameters.
            response: Response description.
            description: Endpoint description.
            use_types: Whether to use type hints.
            
        Returns:
            The generated Flask endpoint code.
        """
        http_method = http_method.upper()
        route = self._endpoint_name_to_route(endpoint_name)
        
        # Start with imports
        code = "from flask import Blueprint, request, jsonify"
        if use_types:
            code += ", Response"
        code += "\n"
        
        if use_types:
            code += "from typing import Dict, Any, Optional, List\n"
        
        code += "\n"
        
        # Create blueprint
        code += f"blueprint = Blueprint('{endpoint_name}', __name__)\n\n"
        
        # Generate the endpoint
        code += f"@blueprint.route('{route}', methods=['{http_method}'])\n"
        
        # Start the function definition
        function_name = self._endpoint_name_to_filename(endpoint_name)
        if use_types:
            code += f"def {function_name}() -> Response:\n"
        else:
            code += f"def {function_name}():\n"
        
        # Add docstring
        if description:
            code += f'    """{description}\n'
            
            # Add parameter documentation
            for param in parameters:
                param_name = param["name"]
                param_type = param["type"]
                param_desc = param.get("description", f"The {param_name} parameter")
                location = param["location"]
                code += f"    :param {param_name}: {param_desc} ({location})\n"
                code += f"    :type {param_name}: {param_type}\n"
            
            # Add response documentation
            code += f"    :return: JSON response\n"
            code += '    """\n'
        
        # Add function body
        code += "    try:\n"
        
        # Extract parameters from request
        for param in parameters:
            param_name = param["name"]
            param_location = param["location"]
            param_type = param["type"]
            required = param.get("required", False)
            
            # Get parameter based on location
            if param_location == "query":
                code += f"        {param_name} = request.args.get('{param_name}')"
            elif param_location == "path":
                # In Flask, path params are accessed via the view function parameters
                continue
            elif param_location == "body":
                code += f"        {param_name} = request.json.get('{param_name}')"
            elif param_location == "header":
                code += f"        {param_name} = request.headers.get('{param_name}')"
            
            # Add type conversion if using types
            if use_types:
                if param_type == "integer" or param_type == "number":
                    code += f" and int(request.args.get('{param_name}'))" if param_location == "query" else ""
                elif param_type == "boolean":
                    code += f" and bool(request.args.get('{param_name}'))" if param_location == "query" else ""
            
            code += "\n"
            
            # Add validation for required parameters
            if required:
                code += f"        if {param_name} is None:\n"
                code += f"            return jsonify({{'error': '{param_name} is required'}}), 400\n"
        
        code += "\n        # TODO: Implement the endpoint logic\n"
        
        # Prepare example response
        response_schema = response.get("schema", {})
        example_response = json.dumps(response_schema, indent=8)
        code += f"        response_data = {example_response}\n\n"
        
        # Return response
        code += f"        return jsonify(response_data)\n"
        code += "    except Exception as e:\n"
        code += "        return jsonify({'error': str(e)}), 500\n"
        
        return code
    
    def _generate_django_endpoint(self,
                                 endpoint_name: str,
                                 http_method: str,
                                 parameters: List[Dict[str, Any]],
                                 response: Dict[str, Any],
                                 description: Optional[str] = None,
                                 use_types: bool = True) -> str:
        """
        Generate Django (Python) API endpoint code.
        
        Args:
            endpoint_name: Endpoint name.
            http_method: HTTP method.
            parameters: Endpoint parameters.
            response: Response description.
            description: Endpoint description.
            use_types: Whether to use type hints.
            
        Returns:
            The generated Django endpoint code.
        """
        http_method = http_method.lower()
        
        # Start with imports
        code = "from django.http import JsonResponse\n"
        code += "from django.views import View\n"
        
        if use_types:
            code += "from typing import Dict, Any, Optional, List, Type\n"
            code += "from django.http import HttpRequest, HttpResponse\n"
        
        code += "import json\n\n"
        
        # Create view class
        class_name = "".join(word.capitalize() for word in endpoint_name.split("_")) + "View"
        code += f"class {class_name}(View):\n"
        
        # Add class docstring
        if description:
            code += f'    """{description}\n'
            code += '    """\n\n'
        
        # Generate the endpoint method
        if use_types:
            code += f"    def {http_method}(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:\n"
        else:
            code += f"    def {http_method}(self, request, *args, **kwargs):\n"
        
        # Add method docstring
        if description:
            code += f'        """{description}\n'
            
            # Add parameter documentation
            for param in parameters:
                param_name = param["name"]
                param_desc = param.get("description", f"The {param_name} parameter")
                location = param["location"]
                code += f"        :param {param_name}: {param_desc} ({location})\n"
            
            # Add response documentation
            code += f"        :return: JSON response\n"
            code += '        """\n'
        
        # Add method body
        code += "        try:\n"
        
        # Extract parameters from request
        for param in parameters:
            param_name = param["name"]
            param_location = param["location"]
            required = param.get("required", False)
            
            # Get parameter based on location
            if param_location == "query":
                code += f"            {param_name} = request.GET.get('{param_name}')\n"
            elif param_location == "path":
                code += f"            {param_name} = kwargs.get('{param_name}')\n"
            elif param_location == "body":
                code += "            body_data = json.loads(request.body)\n"
                code += f"            {param_name} = body_data.get('{param_name}')\n"
            elif param_location == "header":
                code += f"            {param_name} = request.META.get('HTTP_{param_name.upper().replace('-', '_')}')\n"
            
            # Add validation for required parameters
            if required:
                code += f"            if {param_name} is None:\n"
                code += f"                return JsonResponse({{'error': '{param_name} is required'}}, status=400)\n"
        
        code += "\n            # TODO: Implement the endpoint logic\n"
        
        # Prepare example response
        response_schema = response.get("schema", {})
        example_response = json.dumps(response_schema, indent=12)
        code += f"            response_data = {example_response}\n\n"
        
        # Return response
        code += f"            return JsonResponse(response_data)\n"
        code += "        except Exception as e:\n"
        code += "            return JsonResponse({'error': str(e)}, status=500)\n"
        
        # Add URL routing snippet
        code += "\n\n# Add to urls.py:\n"
        route = self._endpoint_name_to_route(endpoint_name)
        code += f"# from django.urls import path\n"
        code += f"# from .views import {class_name}\n"
        code += f"#\n"
        code += f"# urlpatterns = [\n"
        code += f"#     path('{route[1:]}/', {class_name}.as_view(), name='{endpoint_name}'),\n"
        code += f"# ]\n"
        
        return code
    
    def _generate_spring_endpoint(self,
                                 endpoint_name: str,
                                 http_method: str,
                                 parameters: List[Dict[str, Any]],
                                 response: Dict[str, Any],
                                 description: Optional[str] = None) -> str:
        """
        Generate Spring Boot (Java) API endpoint code.
        
        Args:
            endpoint_name: Endpoint name.
            http_method: HTTP method.
            parameters: Endpoint parameters.
            response: Response description.
            description: Endpoint description.
            
        Returns:
            The generated Spring Boot endpoint code.
        """
        http_method = http_method.upper()
        route = self._endpoint_name_to_route(endpoint_name)
        
        # Convert endpoint name to CamelCase for Java class
        class_name = "".join(word.capitalize() for word in endpoint_name.split("_")) + "Controller"
        method_name = endpoint_name.lower()
        
        # Create response class name
        response_class = "".join(word.capitalize() for word in endpoint_name.split("_")) + "Response"
        
        # Start with imports
        code = "package com.example.api.controller;\n\n"
        code += "import org.springframework.web.bind.annotation.*;\n"
        code += "import org.springframework.http.ResponseEntity;\n"
        code += "import org.springframework.http.HttpStatus;\n"
        code += "import java.util.HashMap;\n"
        code += "import java.util.Map;\n"
        
        # Add request body class import if needed
        body_params = [p for p in parameters if p["location"] == "body"]
        if body_params:
            code += "import com.example.api.model.request." + "".join(word.capitalize() for word in endpoint_name.split("_")) + "Request;\n"
        
        # Add response class import
        code += "import com.example.api.model.response." + response_class + ";\n"
        
        code += "\n"
        
        # Generate class-level annotations
        code += "@RestController\n"
        code += "@RequestMapping(\"/api\")\n"
        
        # Start class definition
        code += f"public class {class_name} {{\n\n"
        
        # Generate method-level annotations
        code += f"    @{http_method}Mapping(\"{route}\")\n"
        
        # Add method-level documentation
        if description:
            code += "    /**\n"
            code += f"     * {description}\n"
            
            # Add parameter documentation
            for param in parameters:
                param_name = param["name"]
                param_desc = param.get("description", f"The {param_name} parameter")
                code += f"     * @param {param_name} {param_desc}\n"
            
            # Add response documentation
            code += "     * @return ResponseEntity containing the response\n"
            code += "     */\n"
        
        # Start method definition
        code += f"    public ResponseEntity<{response_class}> {method_name}(\n"
        
        # Add method parameters
        method_params = []
        
        # Add path parameters
        path_params = [p for p in parameters if p["location"] == "path"]
        for param in path_params:
            param_name = param["name"]
            param_type = self._convert_type_to_java(param["type"])
            method_params.append(f"        @PathVariable(\"{param_name}\") {param_type} {param_name}")
        
        # Add query parameters
        query_params = [p for p in parameters if p["location"] == "query"]
        for param in query_params:
            param_name = param["name"]
            param_type = self._convert_type_to_java(param["type"])
            required = param.get("required", False)
            
            if required:
                method_params.append(f"        @RequestParam(\"{param_name}\") {param_type} {param_name}")
            else:
                method_params.append(f"        @RequestParam(value = \"{param_name}\", required = false) {param_type} {param_name}")
        
        # Add body parameter
        if body_params:
            request_class = "".join(word.capitalize() for word in endpoint_name.split("_")) + "Request"
            method_params.append(f"        @RequestBody {request_class} request")
        
        # Add header parameters
        header_params = [p for p in parameters if p["location"] == "header"]
        for param in header_params:
            param_name = param["name"]
            param_type = self._convert_type_to_java(param["type"])
            required = param.get("required", False)
            
            if required:
                method_params.append(f"        @RequestHeader(\"{param_name}\") {param_type} {param_name}")
            else:
                method_params.append(f"        @RequestHeader(value = \"{param_name}\", required = false) {param_type} {param_name}")
        
        # Add parameters to method definition
        code += ",\n".join(method_params)
        code += "\n    ) {\n"
        
        # Add method body
        code += "        try {\n"
        code += "            // TODO: Implement the endpoint logic\n"
        
        # Create response object
        code += f"            {response_class} response = new {response_class}();\n"
        
        # Set response properties based on schema
        for key in response.get("schema", {}).keys():
            if key == "message":
                code += f"            response.setMessage(\"Success\");\n"
            else:
                code += f"            // response.set{key.capitalize()}(value);\n"
        
        # Return response
        code += f"\n            return new ResponseEntity<>(response, HttpStatus.OK);\n"
        code += "        } catch (Exception e) {\n"
        code += "            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);\n"
        code += "        }\n"
        code += "    }\n"
        
        # Close class
        code += "}\n"
        
        # Add response class definition
        code += "\n\n// Create this class in the com.example.api.model.response package\n"
        code += f"// {response_class}.java\n"
        code += "/*\n"
        code += "package com.example.api.model.response;\n\n"
        code += f"public class {response_class} {{\n"
        
        # Add fields based on response schema
        for key, value in response.get("schema", {}).items():
            java_type = self._convert_type_to_java(value)
            code += f"    private {java_type} {key};\n"
        
        code += "\n    // Getters and setters\n"
        
        # Add getters and setters
        for key, value in response.get("schema", {}).items():
            java_type = self._convert_type_to_java(value)
            
            # Getter
            code += f"    public {java_type} get{key.capitalize()}() {{\n"
            code += f"        return {key};\n"
            code += "    }\n\n"
            
            # Setter
            code += f"    public void set{key.capitalize()}({java_type} {key}) {{\n"
            code += f"        this.{key} = {key};\n"
            code += "    }\n\n"
        
        code += "}\n*/\n"
        
        # Add request class definition if needed
        if body_params:
            request_class = "".join(word.capitalize() for word in endpoint_name.split("_")) + "Request"
            code += f"\n\n// Create this class in the com.example.api.model.request package\n"
            code += f"// {request_class}.java\n"
            code += "/*\n"
            code += "package com.example.api.model.request;\n\n"
            code += f"public class {request_class} {{\n"
            
            # Add fields based on body parameters
            for param in body_params:
                param_name = param["name"]
                param_type = self._convert_type_to_java(param["type"])
                code += f"    private {param_type} {param_name};\n"
            
            code += "\n    // Getters and setters\n"
            
            # Add getters and setters
            for param in body_params:
                param_name = param["name"]
                param_type = self._convert_type_to_java(param["type"])
                
                # Getter
                code += f"    public {param_type} get{param_name.capitalize()}() {{\n"
                code += f"        return {param_name};\n"
                code += "    }\n\n"
                
                # Setter
                code += f"    public void set{param_name.capitalize()}({param_type} {param_name}) {{\n"
                code += f"        this.{param_name} = {param_name};\n"
                code += "    }\n\n"
            
            code += "}\n*/\n"
        
        return code
    
    def _convert_type_to_python(self, type_str: str) -> str:
        """
        Convert a generic type to a Python type.
        
        Args:
            type_str: The generic type string.
            
        Returns:
            The Python type string.
        """
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List",
            "object": "Dict[str, Any]",
            "any": "Any"
        }
        
        return type_mapping.get(type_str.lower(), "str")
    
    def _convert_type_to_java(self, type_str: str) -> str:
        """
        Convert a generic type to a Java type.
        
        Args:
            type_str: The generic type string.
            
        Returns:
            The Java type string.
        """
        type_mapping = {
            "string": "String",
            "integer": "Integer",
            "number": "Double",
            "boolean": "Boolean",
            "array": "List<Object>",
            "object": "Map<String, Object>",
            "any": "Object"
        }
        
        return type_mapping.get(type_str.lower(), "String")


class DatabaseModelTool(BaseTool):
    """
    Tool for generating database model code for various frameworks and ORMs.
    """
    
    name = "database_model"
    description = "Generate database model code for various ORMs and frameworks"
    parameters = {
        "type": "object",
        "properties": {
            "model_name": {
                "type": "string",
                "description": "Name of the database model to generate"
            },
            "framework": {
                "type": "string",
                "description": "ORM/framework to use",
                "enum": ["sequelize", "mongoose", "sqlalchemy", "django", "typeorm"]
            },
            "fields": {
                "type": "array",
                "description": "List of fields/columns for the model",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the field"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of the field (string, integer, boolean, etc.)"
                        },
                        "required": {
                            "type": "boolean",
                            "description": "Whether the field is required"
                        },
                        "unique": {
                            "type": "boolean",
                            "description": "Whether the field value should be unique"
                        },
                        "default": {
                            "type": "string",
                            "description": "Default value for the field (as a string)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the field"
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "relationships": {
                "type": "array",
                "description": "List of relationships with other models",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the relationship"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of relationship (one-to-one, one-to-many, many-to-many)",
                            "enum": ["one-to-one", "one-to-many", "many-to-many"]
                        },
                        "target": {
                            "type": "string",
                            "description": "Target model name"
                        },
                        "foreign_key": {
                            "type": "string",
                            "description": "Foreign key field name"
                        }
                    },
                    "required": ["name", "type", "target"]
                }
            },
            "description": {
                "type": "string",
                "description": "Description of the model"
            }
        },
        "required": ["model_name", "framework", "fields"]
    }
    
    def execute(self,
                model_name: str,
                framework: str,
                fields: List[Dict[str, Any]],
                relationships: Optional[List[Dict[str, Any]]] = None,
                description: Optional[str] = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Generate database model code based on the given specifications.
        
        Args:
            model_name: Name of the database model to generate.
            framework: ORM/framework to use.
            fields: List of fields/columns for the model.
            relationships: List of relationships with other models.
            description: Description of the model.
            **kwargs: Additional parameters.
            
        Returns:
            The generated database model code.
        """
        try:
            # Validate inputs
            if framework not in ["sequelize", "mongoose", "sqlalchemy", "django", "typeorm"]:
                return ToolResult.error(
                    self.name,
                    f"Invalid framework: {framework}. Valid frameworks are: sequelize, mongoose, sqlalchemy, django, typeorm."
                )
            
            # Normalize relationships
            relationships = relationships or []
            
            # Generate model code based on framework
            if framework == "sequelize":
                code = self._generate_sequelize_model(model_name, fields, relationships, description)
                file_extension = "js"
            elif framework == "mongoose":
                code = self._generate_mongoose_model(model_name, fields, relationships, description)
                file_extension = "js"
            elif framework == "sqlalchemy":
                code = self._generate_sqlalchemy_model(model_name, fields, relationships, description)
                file_extension = "py"
            elif framework == "django":
                code = self._generate_django_model(model_name, fields, relationships, description)
                file_extension = "py"
            else:  # typeorm
                code = self._generate_typeorm_model(model_name, fields, relationships, description)
                file_extension = "ts"
            
            return ToolResult.success(
                self.name,
                {
                    "code": code,
                    "model_name": model_name,
                    "file_name": f"{self._model_name_to_filename(model_name)}.{file_extension}",
                    "framework": framework
                }
            )
            
        except Exception as e:
            logging.error(f"Error generating database model: {e}")
            return ToolResult.error(self.name, f"Failed to generate database model: {str(e)}")
    
    def _model_name_to_filename(self, name: str) -> str:
        """
        Convert a model name to a filename.
        
        Args:
            name: The model name.
            
        Returns:
            The filename.
        """
        # Convert camelCase or PascalCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _generate_sequelize_model(self,
                                model_name: str,
                                fields: List[Dict[str, Any]],
                                relationships: List[Dict[str, Any]],
                                description: Optional[str] = None) -> str:
        """
        Generate Sequelize (Node.js/JavaScript) model code.
        
        Args:
            model_name: Model name.
            fields: Model fields.
            relationships: Model relationships.
            description: Model description.
            
        Returns:
            The generated Sequelize model code.
        """
        # Convert model name to various formats
        pascal_case = "".join(word.capitalize() for word in model_name.split("_"))
        
        # Start with imports
        code = "const { DataTypes, Model } = require('sequelize');\n\n"
        
        # Add module exports
        code += "module.exports = (sequelize) => {\n"
        
        # Add model class
        code += f"  class {pascal_case} extends Model {{\n"
        
        # Add static associate method for relationships
        if relationships:
            code += "    static associate(models) {\n"
            
            for rel in relationships:
                rel_type = rel["type"]
                target = rel["target"]
                rel_name = rel["name"]
                
                # Convert target name to PascalCase
                target_pascal = "".join(word.capitalize() for word in target.split("_"))
                
                if rel_type == "one-to-one":
                    code += f"      this.hasOne(models.{target_pascal}, {{\n"
                    code += f"        as: '{rel_name}',\n"
                    if "foreign_key" in rel:
                        code += f"        foreignKey: '{rel['foreign_key']}',\n"
                    code += "      });\n"
                elif rel_type == "one-to-many":
                    code += f"      this.hasMany(models.{target_pascal}, {{\n"
                    code += f"        as: '{rel_name}',\n"
                    if "foreign_key" in rel:
                        code += f"        foreignKey: '{rel['foreign_key']}',\n"
                    code += "      });\n"
                elif rel_type == "many-to-many":
                    # For many-to-many, we need a through table
                    through = f"{model_name}_{target}"
                    code += f"      this.belongsToMany(models.{target_pascal}, {{\n"
                    code += f"        through: '{through}',\n"
                    code += f"        as: '{rel_name}',\n"
                    if "foreign_key" in rel:
                        code += f"        foreignKey: '{rel['foreign_key']}',\n"
                    code += "      });\n"
            
            code += "    }\n"
        
        # Close model class
        code += "  }\n\n"
        
        # Initialize model with fields
        code += f"  {pascal_case}.init({\n"
        
        # Add ID field if not explicitly defined
        if not any(field["name"] == "id" for field in fields):
            code += "    id: {\n"
            code += "      type: DataTypes.INTEGER,\n"
            code += "      autoIncrement: true,\n"
            code += "      primaryKey: true,\n"
            code += "    },\n"
        
        # Add fields
        for field in fields:
            field_name = field["name"]
            field_type = field["type"].lower()
            
            code += f"    {field_name}: {{\n"
            
            # Map field type to Sequelize DataType
            if field_type in ["string", "text", "char"]:
                code += "      type: DataTypes.STRING,\n"
            elif field_type == "text":
                code += "      type: DataTypes.TEXT,\n"
            elif field_type in ["integer", "int"]:
                code += "      type: DataTypes.INTEGER,\n"
            elif field_type == "bigint":
                code += "      type: DataTypes.BIGINT,\n"
            elif field_type in ["float", "number", "decimal"]:
                code += "      type: DataTypes.FLOAT,\n"
            elif field_type == "boolean":
                code += "      type: DataTypes.BOOLEAN,\n"
            elif field_type == "date":
                code += "      type: DataTypes.DATEONLY,\n"
            elif field_type == "datetime":
                code += "      type: DataTypes.DATE,\n"
            elif field_type == "time":
                code += "      type: DataTypes.TIME,\n"
            elif field_type == "json":
                code += "      type: DataTypes.JSON,\n"
            else:
                code += "      type: DataTypes.STRING,\n"
            
            # Add field attributes
            if field.get("required", False):
                code += "      allowNull: false,\n"
                
            if field.get("unique", False):
                code += "      unique: true,\n"
                
            if "default" in field:
                default_value = field["default"]
                
                # Format default value based on type
                if field_type in ["string", "text", "char"]:
                    code += f"      defaultValue: '{default_value}',\n"
                elif field_type in ["integer", "int", "bigint", "float", "number", "decimal"]:
                    code += f"      defaultValue: {default_value},\n"
                elif field_type == "boolean":
                    code += f"      defaultValue: {default_value.lower()},\n"
                else:
                    code += f"      defaultValue: '{default_value}',\n"
                    
            # Add field description as comment
            if "description" in field:
                code += f"      comment: '{field['description']}',\n"
            
            code += "    },\n"
        
        # Add timestamps
        code += "    createdAt: {\n"
        code += "      type: DataTypes.DATE,\n"
        code += "      allowNull: false,\n"
        code += "      defaultValue: DataTypes.NOW,\n"
        code += "    },\n"
        code += "    updatedAt: {\n"
        code += "      type: DataTypes.DATE,\n"
        code += "      allowNull: false,\n"
        code += "      defaultValue: DataTypes.NOW,\n"
        code += "    },\n"
        
        # Close field definitions
        code += "  }, {\n"
        
        # Add model options
        code += "    sequelize,\n"
        code += f"    modelName: '{pascal_case}',\n"
        code += f"    tableName: '{self._model_name_to_filename(model_name)}s',\n"
        
        # Add model description as comment
        if description:
            code += f"    comment: '{description}',\n"
        
        code += "  });\n\n"
        
        # Return model
        code += f"  return {pascal_case};\n"
        code += "};\n"
        
        return code
    
    def _generate_mongoose_model(self,
                               model_name: str,
                               fields: List[Dict[str, Any]],
                               relationships: List[Dict[str, Any]],
                               description: Optional[str] = None) -> str:
        """
        Generate Mongoose (Node.js/MongoDB) model code.
        
        Args:
            model_name: Model name.
            fields: Model fields.
            relationships: Model relationships.
            description: Model description.
            
        Returns:
            The generated Mongoose model code.
        """
        # Convert model name to various formats
        pascal_case = "".join(word.capitalize() for word in model_name.split("_"))
        
        # Start with imports
        code = "const mongoose = require('mongoose');\n"
        code += "const { Schema } = mongoose;\n\n"
        
        # Add schema definition
        code += f"const {model_name}Schema = new Schema({{\n"
        
        # Add fields
        for field in fields:
            field_name = field["name"]
            field_type = field["type"].lower()
            
            # Map field type to Mongoose type
            if field_type in ["string", "text", "char"]:
                type_str = "String"
            elif field_type in ["integer", "int", "number", "float", "decimal"]:
                type_str = "Number"
            elif field_type == "boolean":
                type_str = "Boolean"
            elif field_type in ["date", "datetime"]:
                type_str = "Date"
            elif field_type in ["object", "json"]:
                type_str = "Schema.Types.Mixed"
            elif field_type == "objectid":
                type_str = "Schema.Types.ObjectId"
            else:
                type_str = "String"
            
            # Simple field or complex field with options
            if not any(key in field for key in ["required", "unique", "default", "description"]):
                code += f"  {field_name}: {type_str},\n"
            else:
                code += f"  {field_name}: {{\n"
                code += f"    type: {type_str},\n"
                
                # Add field attributes
                if field.get("required", False):
                    code += "    required: true,\n"
                    
                if field.get("unique", False):
                    code += "    unique: true,\n"
                    
                if "default" in field:
                    default_value = field["default"]
                    
                    # Format default value based on type
                    if field_type in ["string", "text", "char"]:
                        code += f"    default: '{default_value}',\n"
                    elif field_type in ["integer", "int", "number", "float", "decimal"]:
                        code += f"    default: {default_value},\n"
                    elif field_type == "boolean":
                        code += f"    default: {default_value.lower()},\n"
                    else:
                        code += f"    default: '{default_value}',\n"
                        
                # Add field description as comment
                if "description" in field:
                    code += f"    // {field['description']}\n"
                
                code += "  },\n"
        
        # Add relationships
        for rel in relationships:
            rel_type = rel["type"]
            target = rel["target"]
            rel_name = rel["name"]
            
            if rel_type == "one-to-one" or rel_type == "many-to-one":
                code += f"  {rel_name}: {{\n"
                code += f"    type: Schema.Types.ObjectId,\n"
                code += f"    ref: '{target}',\n"
                code += "  },\n"
            elif rel_type == "one-to-many":
                code += f"  {rel_name}: [{{\n"
                code += f"    type: Schema.Types.ObjectId,\n"
                code += f"    ref: '{target}',\n"
                code += "  }],\n"
            elif rel_type == "many-to-many":
                code += f"  {rel_name}: [{{\n"
                code += f"    type: Schema.Types.ObjectId,\n"
                code += f"    ref: '{target}',\n"
                code += "  }],\n"
        
        # Add timestamps
        code += "}, {\n"
        code += "  timestamps: true\n"
        code += "});\n\n"
        
        # Add schema methods or virtuals if needed
        
        # Add model description as comment
        if description:
            code += f"// {description}\n"
        
        # Create and export model
        code += f"const {pascal_case} = mongoose.model('{pascal_case}', {model_name}Schema);\n\n"
        code += f"module.exports = {pascal_case};\n"
        
        return code
    
    def _generate_sqlalchemy_model(self,
                                  model_name: str,
                                  fields: List[Dict[str, Any]],
                                  relationships: List[Dict[str, Any]],
                                  description: Optional[str] = None) -> str:
        """
        Generate SQLAlchemy (Python) model code.
        
        Args:
            model_name: Model name.
            fields: Model fields.
            relationships: Model relationships.
            description: Model description.
            
        Returns:
            The generated SQLAlchemy model code.
        """
        # Convert model name to various formats
        pascal_case = "".join(word.capitalize() for word in model_name.split("_"))
        table_name = self._model_name_to_filename(model_name)
        
        # Start with imports
        code = "from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Table\n"
        code += "from sqlalchemy.ext.declarative import declarative_base\n"
        code += "from sqlalchemy.orm import relationship\n"
        code += "from datetime import datetime\n\n"
        
        # Add Base
        code += "Base = declarative_base()\n\n"
        
        # Add many-to-many association tables if needed
        for rel in relationships:
            if rel["type"] == "many-to-many":
                rel_name = rel["name"]
                target = rel["target"]
                table1 = table_name
                table2 = self._model_name_to_filename(target)
                assoc_table_name = f"{table1}_{table2}_association"
                
                code += f"# Association table for {rel_name} relationship\n"
                code += f"{assoc_table_name} = Table(\n"
                code += f"    '{assoc_table_name}',\n"
                code += "    Base.metadata,\n"
                code += f"    Column('{table1}_id', Integer, ForeignKey('{table1}.id'), primary_key=True),\n"
                code += f"    Column('{table2}_id', Integer, ForeignKey('{table2}.id'), primary_key=True)\n"
                code += ")\n\n"
        
        # Add model class
        if description:
            code += f"# {description}\n"
        
        code += f"class {pascal_case}(Base):\n"
        code += f"    __tablename__ = '{table_name}'\n\n"
        
        # Add fields
        for field in fields:
            field_name = field["name"]
            field_type = field["type"].lower()
            field_opts = []
            
            # Map field type to SQLAlchemy type
            if field_name == "id" and field_type in ["integer", "int"]:
                type_str = "Integer"
                field_opts.append("primary_key=True")
            elif field_type in ["string", "char"]:
                type_str = "String"
            elif field_type == "text":
                type_str = "Text"
            elif field_type in ["integer", "int"]:
                type_str = "Integer"
            elif field_type in ["float", "number", "decimal"]:
                type_str = "Float"
            elif field_type == "boolean":
                type_str = "Boolean"
            elif field_type in ["date", "datetime"]:
                type_str = "DateTime"
            else:
                type_str = "String"
            
            # Add field attributes
            if field.get("required", False) and field_name != "id":  # Skip for id field which is primary key
                field_opts.append("nullable=False")
                
            if field.get("unique", False):
                field_opts.append("unique=True")
                
            if "default" in field:
                default_value = field["default"]
                
                # Format default value based on type
                if field_type in ["string", "text", "char"]:
                    field_opts.append(f"default='{default_value}'")
                elif field_type in ["integer", "int", "float", "number", "decimal"]:
                    field_opts.append(f"default={default_value}")
                elif field_type == "boolean":
                    field_opts.append(f"default={default_value.lower()}")
                elif field_type in ["date", "datetime"]:
                    field_opts.append("default=datetime.utcnow")
                else:
                    field_opts.append(f"default='{default_value}'")
            
            # Add field docstring
            if "description" in field:
                code += f"    # {field['description']}\n"
            
            # Add field with options
            if field_opts:
                code += f"    {field_name} = Column({type_str}, {', '.join(field_opts)})\n"
            else:
                code += f"    {field_name} = Column({type_str})\n"
                
            # Add a newline after each field for readability
            code += "\n"
        
        # Add relationships
        if relationships:
            for rel in relationships:
                rel_type = rel["type"]
                target = rel["target"]
                rel_name = rel["name"]
                
                # Convert target name to PascalCase
                target_pascal = "".join(word.capitalize() for word in target.split("_"))
                
                # Add relationship docstring
                code += f"    # Relationship: {rel_type} with {target}\n"
                
                if rel_type == "one-to-one":
                    # For one-to-one, we need a foreign key as well
                    if "foreign_key" in rel:
                        fk_name = rel["foreign_key"]
                        code += f"    {fk_name} = Column(Integer, ForeignKey('{target}.id'))\n"
                        code += f"    {rel_name} = relationship('{target_pascal}', uselist=False)\n"
                    else:
                        # If no foreign key specified, assume the foreign key is on the target model
                        code += f"    {rel_name} = relationship('{target_pascal}', uselist=False, back_populates='{table_name}')\n"
                        
                elif rel_type == "one-to-many":
                    # For one-to-many, the foreign key is on the target model
                    code += f"    {rel_name} = relationship('{target_pascal}', back_populates='{table_name}')\n"
                    
                elif rel_type == "many-to-many":
                    # For many-to-many, we use the association table
                    table1 = table_name
                    table2 = self._model_name_to_filename(target)
                    assoc_table_name = f"{table1}_{table2}_association"
                    
                    code += f"    {rel_name} = relationship('{target_pascal}', secondary={assoc_table_name}, backref='{table_name}')\n"
                
                # Add a newline after each relationship for readability
                code += "\n"
        
        # Add __repr__ method
        code += "    def __repr__(self):\n"
        code += f"        return f\"<{pascal_case}(id={{self.id}})>\"\n"
        
        return code
    
    def _generate_django_model(self,
                             model_name: str,
                             fields: List[Dict[str, Any]],
                             relationships: List[Dict[str, Any]],
                             description: Optional[str] = None) -> str:
        """
        Generate Django (Python) model code.
        
        Args:
            model_name: Model name.
            fields: Model fields.
            relationships: Model relationships.
            description: Model description.
            
        Returns:
            The generated Django model code.
        """
        # Convert model name to various formats
        pascal_case = "".join(word.capitalize() for word in model_name.split("_"))
        
        # Start with imports
        code = "from django.db import models\n\n"
        
        # Add model class
        if description:
            code += f"# {description}\n"
        
        code += f"class {pascal_case}(models.Model):\n"
        
        # Add fields
        for field in fields:
            field_name = field["name"]
            field_type = field["type"].lower()
            field_opts = []
            
            # Handle special ID field case - Django creates this automatically
            if field_name == "id" and field_type in ["integer", "int"]:
                continue
            
            # Map field type to Django model field
            if field_type in ["string", "char"]:
                type_str = "models.CharField(max_length=255"
            elif field_type == "text":
                type_str = "models.TextField("
            elif field_type in ["integer", "int"]:
                type_str = "models.IntegerField("
            elif field_type in ["float", "number"]:
                type_str = "models.FloatField("
            elif field_type == "decimal":
                type_str = "models.DecimalField(max_digits=10, decimal_places=2"
            elif field_type == "boolean":
                type_str = "models.BooleanField("
            elif field_type == "date":
                type_str = "models.DateField("
            elif field_type == "datetime":
                type_str = "models.DateTimeField("
            elif field_type == "email":
                type_str = "models.EmailField("
            elif field_type == "url":
                type_str = "models.URLField("
            elif field_type == "image":
                type_str = "models.ImageField(upload_to='images/'"
            elif field_type == "file":
                type_str = "models.FileField(upload_to='files/'"
            else:
                type_str = "models.CharField(max_length=255"
            
            # Add field attributes
            if field.get("required", False):
                field_opts.append("null=False")
                field_opts.append("blank=False")
            else:
                field_opts.append("null=True")
                field_opts.append("blank=True")
                
            if field.get("unique", False):
                field_opts.append("unique=True")
                
            if "default" in field:
                default_value = field["default"]
                
                # Format default value based on type
                if field_type in ["string", "text", "char", "email", "url"]:
                    field_opts.append(f"default='{default_value}'")
                elif field_type in ["integer", "int", "float", "number", "decimal"]:
                    field_opts.append(f"default={default_value}")
                elif field_type == "boolean":
                    field_opts.append(f"default={default_value.lower()}")
                else:
                    field_opts.append(f"default='{default_value}'")
            
            # Add field description as help_text
            if "description" in field:
                field_opts.append(f"help_text='{field['description']}'")
            
            # Add field with options
            if field_opts:
                code += f"    {field_name} = {type_str}, {', '.join(field_opts)})\n"
            else:
                code += f"    {field_name} = {type_str})\n"
        
        # Add relationships
        if relationships:
            code += "\n    # Relationships\n"
            for rel in relationships:
                rel_type = rel["type"]
                target = rel["target"]
                rel_name = rel["name"]
                
                # Convert target name to PascalCase
                target_pascal = "".join(word.capitalize() for word in target.split("_"))
                
                if rel_type == "one-to-one":
                    code += f"    {rel_name} = models.OneToOneField(\n"
                    code += f"        '{target_pascal}',\n"
                    code += "        on_delete=models.CASCADE,\n"
                    if "foreign_key" in rel:
                        code += f"        db_column='{rel['foreign_key']}',\n"
                    code += "        related_name='+',\n"
                    code += "        null=True,\n"
                    code += "        blank=True\n"
                    code += "    )\n"
                elif rel_type == "one-to-many":
                    # In Django, one-to-many is defined from the "many" side using ForeignKey
                    # So this would typically be defined in the target model
                    code += f"    # Note: This is the 'one' side of a one-to-many relationship with {target_pascal}\n"
                    code += f"    # In {target_pascal} model, define: {self._model_name_to_filename(model_name)} = models.ForeignKey('{pascal_case}', on_delete=models.CASCADE)\n"
                elif rel_type == "many-to-many":
                    code += f"    {rel_name} = models.ManyToManyField(\n"
                    code += f"        '{target_pascal}',\n"
                    if "foreign_key" in rel:
                        code += f"        db_column='{rel['foreign_key']}',\n"
                    code += "        related_name='+',\n"
                    code += "        blank=True\n"
                    code += "    )\n"
        
        # Add Meta class
        code += "\n    class Meta:\n"
        code += f"        db_table = '{self._model_name_to_filename(model_name)}'\n"
        
        if description:
            code += f"        verbose_name = '{model_name}'\n"
            code += f"        verbose_name_plural = '{model_name}s'\n"
        
        # Add __str__ method
        code += "\n    def __str__(self):\n"
        
        # Try to find a suitable field for __str__
        str_field = next((f["name"] for f in fields if f["name"] in ["name", "title", "label"]), None)
        if str_field:
            code += f"        return str(self.{str_field})\n"
        else:
            code += f"        return f\"{pascal_case} {{{model_name}.id}}\"\n"
        
        return code
    
    def _generate_typeorm_model(self,
                               model_name: str,
                               fields: List[Dict[str, Any]],
                               relationships: List[Dict[str, Any]],
                               description: Optional[str] = None) -> str:
        """
        Generate TypeORM (TypeScript) model code.
        
        Args:
            model_name: Model name.
            fields: Model fields.
            relationships: Model relationships.
            description: Model description.
            
        Returns:
            The generated TypeORM model code.
        """
        # Convert model name to various formats
        pascal_case = "".join(word.capitalize() for word in model_name.split("_"))
        table_name = self._model_name_to_filename(model_name)
        
        # Start with imports
        code = "import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn, OneToOne, OneToMany, ManyToOne, ManyToMany, JoinTable, JoinColumn } from 'typeorm';\n"
        
        # Add related entity imports
        if relationships:
            for rel in relationships:
                target = rel["target"]
                target_pascal = "".join(word.capitalize() for word in target.split("_"))
                code += f"import {{ {target_pascal} }} from './{self._model_name_to_filename(target)}.entity';\n"
        
        code += "\n"
        
        # Add entity class
        if description:
            code += "/**\n"
            code += f" * {description}\n"
            code += " */\n"
        
        code += "@Entity()\n"
        code += f"export class {pascal_case} {{\n"
        
        # Add ID field if not explicitly defined
        if not any(field["name"] == "id" for field in fields):
            code += "    @PrimaryGeneratedColumn()\n"
            code += "    id: number;\n\n"
        
        # Add fields
        for field in fields:
            field_name = field["name"]
            field_type = field["type"].lower()
            
            # Skip id field if it's already defined above
            if field_name == "id" and field_type in ["integer", "int"]:
                code += "    @PrimaryGeneratedColumn()\n"
                code += "    id: number;\n\n"
                continue
            
            # Add field description as comment
            if "description" in field:
                code += "    /**\n"
                code += f"     * {field['description']}\n"
                code += "     */\n"
            
            # Add column decorator
            code += "    @Column({\n"
            
            # Map field type to TypeORM/TypeScript type
            column_type = ""
            ts_type = ""
            
            if field_type in ["string", "char"]:
                column_type = "varchar"
                ts_type = "string"
            elif field_type == "text":
                column_type = "text"
                ts_type = "string"
            elif field_type in ["integer", "int"]:
                column_type = "int"
                ts_type = "number"
            elif field_type in ["float", "number"]:
                column_type = "float"
                ts_type = "number"
            elif field_type == "decimal":
                column_type = "decimal"
                ts_type = "number"
            elif field_type == "boolean":
                column_type = "boolean"
                ts_type = "boolean"
            elif field_type == "date":
                column_type = "date"
                ts_type = "Date"
            elif field_type == "datetime":
                column_type = "datetime"
                ts_type = "Date"
            elif field_type == "json":
                column_type = "json"
                ts_type = "any"
            else:
                column_type = "varchar"
                ts_type = "string"
            
            code += f"        type: '{column_type}',\n"
            
            # Add field attributes
            if field.get("required", False):
                code += "        nullable: false,\n"
            else:
                code += "        nullable: true,\n"
                
            if field.get("unique", False):
                code += "        unique: true,\n"
                
            if "default" in field:
                default_value = field["default"]
                
                # Format default value based on type
                if field_type in ["string", "text", "char"]:
                    code += f"        default: '{default_value}',\n"
                elif field_type in ["integer", "int", "float", "number", "decimal"]:
                    code += f"        default: {default_value},\n"
                elif field_type == "boolean":
                    code += f"        default: {default_value.lower()},\n"
                else:
                    code += f"        default: '{default_value}',\n"
            
            code += "    })\n"
            code += f"    {field_name}: {ts_type};\n\n"
        
        # Add timestamps
        code += "    @CreateDateColumn()\n"
        code += "    createdAt: Date;\n\n"
        
        code += "    @UpdateDateColumn()\n"
        code += "    updatedAt: Date;\n\n"
        
        # Add relationships
        if relationships:
            for rel in relationships:
                rel_type = rel["type"]
                target = rel["target"]
                rel_name = rel["name"]
                
                # Convert target name to PascalCase
                target_pascal = "".join(word.capitalize() for word in target.split("_"))
                
                # Add relationship docstring
                code += "    /**\n"
                code += f"     * {rel_type} relationship with {target_pascal}\n"
                code += "     */\n"
                
                if rel_type == "one-to-one":
                    code += "    @OneToOne(() => " + target_pascal 
                    if "foreign_key" in rel:
                        code += ", { cascade: true })\n"
                        code += f"    @JoinColumn({{ name: '{rel['foreign_key']}' }})\n"
                    else:
                        code += ")\n"
                    code += f"    {rel_name}: {target_pascal};\n\n"
                    
                elif rel_type == "one-to-many":
                    code += "    @OneToMany(() => " + target_pascal + ", " + table_name + " => " + table_name + "." + pascal_case.lower() + ")\n"
                    code += f"    {rel_name}: {target_pascal}[];\n\n"
                    
                elif rel_type == "many-to-one":
                    code += "    @ManyToOne(() => " + target_pascal + ", { cascade: true })\n"
                    if "foreign_key" in rel:
                        code += f"    @JoinColumn({{ name: '{rel['foreign_key']}' }})\n"
                    code += f"    {rel_name}: {target_pascal};\n\n"
                    
                elif rel_type == "many-to-many":
                    code += "    @ManyToMany(() => " + target_pascal + ")\n"
                    code += "    @JoinTable({\n"
                    code += f"        name: '{table_name}_{self._model_name_to_filename(target)}',\n"
                    code += f"        joinColumn: {{ name: '{table_name}_id' }},\n"
                    code += f"        inverseJoinColumn: {{ name: '{self._model_name_to_filename(target)}_id' }}\n"
                    code += "    })\n"
                    code += f"    {rel_name}: {target_pascal}[];\n\n"
        
        # Close class
        code += "}\n"
        
        return code


# Add more backend tools as needed