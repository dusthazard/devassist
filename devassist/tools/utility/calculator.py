"""
Calculator tool for mathematical operations in development.

This tool provides safe evaluation of mathematical expressions, unit conversions,
and other calculation capabilities useful in development contexts.
"""

import logging
import ast
import operator
import math
import re
from typing import Dict, Any, Union

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class CalculatorTool(BaseTool):
    """
    A tool for performing mathematical calculations in development contexts.
    
    Supports:
    - Basic arithmetic operations
    - Mathematical functions
    - Unit conversions
    - Numeric base conversions
    - Programming-related calculations
    """
    
    name = "calculator"
    description = "Perform mathematical calculations for development tasks"
    category = "Utility"
    
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            },
            "operation": {
                "type": "string",
                "description": "Specific operation type (calc, convert, base)",
                "enum": ["calc", "convert", "base"]
            },
            "from_unit": {
                "type": "string",
                "description": "Source unit for conversion (for convert operation)"
            },
            "to_unit": {
                "type": "string",
                "description": "Target unit for conversion (for convert operation)"
            },
            "from_base": {
                "type": "string",
                "description": "Source base for conversion (for base operation)",
                "enum": ["binary", "octal", "decimal", "hex"]
            },
            "to_base": {
                "type": "string",
                "description": "Target base for conversion (for base operation)",
                "enum": ["binary", "octal", "decimal", "hex"]
            }
        },
        "required": ["expression"]
    }
    
    # Supported operators and their corresponding functions
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.USub: operator.neg,  # Unary minus
        ast.UAdd: operator.pos   # Unary plus
    }
    
    # Supported math functions
    _MATH_FUNCTIONS = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sqrt': math.sqrt,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
        'pow': pow,
        'max': max,
        'min': min
    }
    
    # Constants
    _CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
        'nan': math.nan
    }
    
    # Unit conversion factors (to base unit)
    _UNIT_CONVERSIONS = {
        # Length - base: meter
        'mm': 0.001,
        'cm': 0.01,
        'm': 1.0,
        'km': 1000.0,
        'in': 0.0254,
        'ft': 0.3048,
        'yd': 0.9144,
        'mi': 1609.344,
        # Time - base: second
        'ms': 0.001,
        'sec': 1.0,
        'min': 60.0,
        'hr': 3600.0,
        'day': 86400.0,
        # Data - base: byte
        'bit': 0.125,
        'byte': 1.0,
        'kb': 1024.0,
        'mb': 1048576.0,
        'gb': 1073741824.0,
        'tb': 1099511627776.0
    }
    
    # Base conversion mappings
    _BASE_MAPPINGS = {
        'binary': 2,
        'octal': 8,
        'decimal': 10,
        'hex': 16
    }
    
    def __init__(self):
        """Initialize the calculator tool."""
        self.logger = logging.getLogger("devassist.tools.calculator")
    
    def execute(self, expression: str, operation: str = "calc", 
                from_unit: str = None, to_unit: str = None,
                from_base: str = None, to_base: str = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Execute the calculator tool.
        
        Args:
            expression: The expression to evaluate or value to convert.
            operation: The type of operation to perform (calc, convert, base).
            from_unit: Source unit for conversion.
            to_unit: Target unit for conversion.
            from_base: Source base for numeric base conversion.
            to_base: Target base for numeric base conversion.
            **kwargs: Additional parameters (ignored).
            
        Returns:
            The calculation result.
        """
        try:
            # Select the appropriate operation
            if operation == "convert" and from_unit and to_unit:
                return self._perform_unit_conversion(expression, from_unit, to_unit)
            elif operation == "base" and from_base and to_base:
                return self._perform_base_conversion(expression, from_base, to_base)
            else:
                # Default to mathematical expression evaluation
                return self._evaluate_expression(expression)
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Calculator error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Calculation error: {error_msg}"
            )
    
    def validate_input(self, expression: str = None, **kwargs) -> bool:
        """
        Validate the input parameters.
        
        Args:
            expression: The expression to validate.
            **kwargs: Additional parameters.
            
        Returns:
            True if the input is valid, False otherwise.
        """
        if expression is None:
            return False
        
        # Check operation-specific parameters
        operation = kwargs.get("operation", "calc")
        
        if operation == "convert":
            from_unit = kwargs.get("from_unit")
            to_unit = kwargs.get("to_unit")
            if not from_unit or not to_unit:
                return False
            if from_unit not in self._UNIT_CONVERSIONS or to_unit not in self._UNIT_CONVERSIONS:
                return False
                
        elif operation == "base":
            from_base = kwargs.get("from_base")
            to_base = kwargs.get("to_base")
            if not from_base or not to_base:
                return False
            if from_base not in self._BASE_MAPPINGS or to_base not in self._BASE_MAPPINGS:
                return False
        
        return True
    
    def _evaluate_expression(self, expression: str) -> ToolResult:
        """
        Evaluate a mathematical expression.
        
        Args:
            expression: The expression to evaluate.
            
        Returns:
            A ToolResult with the evaluation result.
        """
        # Clean and parse the expression
        cleaned_expr = self._clean_expression(expression)
        self.logger.debug(f"Evaluating expression: {cleaned_expr}")
        
        try:
            # Parse using abstract syntax tree
            tree = ast.parse(cleaned_expr, mode='eval')
            self.logger.debug(f"AST tree: {ast.dump(tree)}")
            
            # Evaluate the expression
            result = self._eval_node(tree.body)
            
            # Format the result
            if isinstance(result, float):
                # Handle floating-point precision
                if result.is_integer():
                    formatted_result = str(int(result))
                else:
                    # Round to 10 decimal places to avoid floating point issues
                    result = round(result, 10)
                    # Remove trailing zeros
                    formatted_result = str(result).rstrip('0').rstrip('.')
            else:
                formatted_result = str(result)
            
            # Return success result
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "expression": expression,
                    "cleaned_expression": cleaned_expr,
                    "result": formatted_result,
                    "result_type": type(result).__name__
                }
            )
            
        except Exception as e:
            self.logger.error(f"Expression evaluation error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Error evaluating expression: {str(e)}"
            )
    
    def _perform_unit_conversion(self, value: str, from_unit: str, to_unit: str) -> ToolResult:
        """
        Perform unit conversion.
        
        Args:
            value: The value to convert.
            from_unit: Source unit.
            to_unit: Target unit.
            
        Returns:
            A ToolResult with the conversion result.
        """
        try:
            # Parse the input value
            try:
                numeric_value = float(value)
            except ValueError:
                # Try to evaluate as an expression
                eval_result = self._evaluate_expression(value)
                if eval_result.status == "error":
                    return eval_result
                numeric_value = float(eval_result.result["result"])
            
            # Check if units are in the same category
            from_factor = self._UNIT_CONVERSIONS.get(from_unit.lower())
            to_factor = self._UNIT_CONVERSIONS.get(to_unit.lower())
            
            if not from_factor or not to_factor:
                return ToolResult(
                    tool_name=self.name,
                    status="error",
                    error=f"Unsupported units: {from_unit} or {to_unit}"
                )
            
            # Check if units are compatible
            from_category = self._get_unit_category(from_unit)
            to_category = self._get_unit_category(to_unit)
            
            if from_category != to_category:
                return ToolResult(
                    tool_name=self.name,
                    status="error",
                    error=f"Incompatible unit categories: {from_category} and {to_category}"
                )
            
            # Convert to base unit, then to target unit
            base_value = numeric_value * from_factor
            result_value = base_value / to_factor
            
            # Format the result
            if result_value.is_integer():
                formatted_result = str(int(result_value))
            else:
                # Round to 6 decimal places
                result_value = round(result_value, 6)
                # Remove trailing zeros
                formatted_result = str(result_value).rstrip('0').rstrip('.')
            
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "value": value,
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                    "result": formatted_result,
                    "full_result": f"{formatted_result} {to_unit}"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Unit conversion error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Error during unit conversion: {str(e)}"
            )
    
    def _perform_base_conversion(self, value: str, from_base: str, to_base: str) -> ToolResult:
        """
        Perform numeric base conversion.
        
        Args:
            value: The value to convert.
            from_base: Source base.
            to_base: Target base.
            
        Returns:
            A ToolResult with the conversion result.
        """
        try:
            # Get the base numbers
            from_base_num = self._BASE_MAPPINGS.get(from_base.lower())
            to_base_num = self._BASE_MAPPINGS.get(to_base.lower())
            
            if not from_base_num or not to_base_num:
                return ToolResult(
                    tool_name=self.name,
                    status="error",
                    error=f"Unsupported bases: {from_base} or {to_base}"
                )
            
            # Clean the input value
            clean_value = value.strip().lower()
            if from_base == "hex" and clean_value.startswith("0x"):
                clean_value = clean_value[2:]
            elif from_base == "binary" and clean_value.startswith("0b"):
                clean_value = clean_value[2:]
            elif from_base == "octal" and clean_value.startswith("0o"):
                clean_value = clean_value[2:]
                
            # Convert to decimal first
            try:
                decimal_value = int(clean_value, from_base_num)
            except ValueError:
                return ToolResult(
                    tool_name=self.name,
                    status="error",
                    error=f"Invalid {from_base} value: {value}"
                )
            
            # Convert to target base
            if to_base == "binary":
                result = bin(decimal_value)[2:]
                prefixed_result = f"0b{result}"
            elif to_base == "octal":
                result = oct(decimal_value)[2:]
                prefixed_result = f"0o{result}"
            elif to_base == "decimal":
                result = str(decimal_value)
                prefixed_result = result
            elif to_base == "hex":
                result = hex(decimal_value)[2:]
                prefixed_result = f"0x{result}"
            else:
                result = str(decimal_value)
                prefixed_result = result
            
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "value": value,
                    "from_base": from_base,
                    "to_base": to_base,
                    "result": result,
                    "prefixed_result": prefixed_result,
                    "decimal_value": str(decimal_value)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Base conversion error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Error during base conversion: {str(e)}"
            )
    
    def _clean_expression(self, expression: str) -> str:
        """
        Clean and prepare an expression for evaluation.
        
        Args:
            expression: The expression to clean.
            
        Returns:
            The cleaned expression.
        """
        # Remove whitespace
        cleaned = expression.strip()
        
        # Replace constants with their values
        for const, value in self._CONSTANTS.items():
            pattern = r'\b' + const + r'\b'
            cleaned = re.sub(pattern, str(value), cleaned)
            
        # Replace math functions with __func_name notation for later handling
        for func_name in self._MATH_FUNCTIONS.keys():
            pattern = r'\b' + func_name + r'\s*\('
            replacement = f'__func_{func_name}('
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned
    
    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        """
        Recursively evaluate an AST node.
        
        Args:
            node: The node to evaluate.
            
        Returns:
            The evaluated result.
            
        Raises:
            ValueError: If the expression contains unsupported operations.
        """
        # Handle numbers
        if isinstance(node, ast.Num):
            return node.n
        
        # Handle constants
        elif isinstance(node, ast.Constant):
            return node.value
        
        # Handle names (variables, constants)
        elif isinstance(node, ast.Name):
            if node.id in self._CONSTANTS:
                return self._CONSTANTS[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        
        # Handle binary operations (e.g., a + b)
        elif isinstance(node, ast.BinOp):
            # Get operator function
            if type(node.op) not in self._OPERATORS:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            
            # Evaluate left and right operands
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            
            # Check for division by zero
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division by zero")
            
            # Apply the operator
            return self._OPERATORS[type(node.op)](left, right)
        
        # Handle unary operations (e.g., -a)
        elif isinstance(node, ast.UnaryOp):
            # Get operator function
            if type(node.op) not in self._OPERATORS:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            
            # Evaluate the operand
            operand = self._eval_node(node.operand)
            
            # Apply the operator
            return self._OPERATORS[type(node.op)](operand)
        
        # Handle function calls
        elif isinstance(node, ast.Call):
            # Check if it's one of our supported functions
            if isinstance(node.func, ast.Name) and node.func.id.startswith("__func_"):
                func_name = node.func.id[7:]  # Remove "__func_" prefix
                if func_name in self._MATH_FUNCTIONS:
                    # Evaluate arguments
                    args = [self._eval_node(arg) for arg in node.args]
                    
                    # Call the function
                    return self._MATH_FUNCTIONS[func_name](*args)
            
            raise ValueError(f"Unsupported function call: {getattr(node.func, 'id', 'unknown')}")
        
        # Handle other node types
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    def _get_unit_category(self, unit: str) -> str:
        """
        Get the category of a unit.
        
        Args:
            unit: The unit to categorize.
            
        Returns:
            The unit category.
        """
        unit = unit.lower()
        
        # Length units
        if unit in ['mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi']:
            return 'length'
        
        # Time units
        elif unit in ['ms', 'sec', 'min', 'hr', 'day']:
            return 'time'
        
        # Data units
        elif unit in ['bit', 'byte', 'kb', 'mb', 'gb', 'tb']:
            return 'data'
        
        return 'unknown'
