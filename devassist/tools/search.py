"""
Search tool for finding development resources and information.

This tool provides capabilities for searching documentation, code examples,
libraries, APIs, and other resources useful for software development.
"""

import logging
import json
import re
import random
from typing import Dict, List, Any, Union, Optional

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class SearchTool(BaseTool):
    """
    A tool for searching development resources and information.
    
    Supports:
    - Documentation lookup
    - Code example search
    - Library/package search
    - API reference lookup
    - Error message search
    - Best practices lookup
    """
    
    name = "search"
    description = "Search for development resources and information"
    category = "Information"
    
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "search_type": {
                "type": "string",
                "description": "Type of search to perform",
                "enum": ["general", "documentation", "code", "library", "api", "error", "best_practices"]
            },
            "technology": {
                "type": "string",
                "description": "Specific technology to search within (e.g., 'python', 'react', 'docker')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5
            },
            "filter": {
                "type": "object",
                "description": "Additional filters for the search"
            }
        },
        "required": ["query"]
    }
    
    # Mock data for different search types
    _MOCK_DATA = {
        "documentation": {
            "python": [
                {"title": "Python 3.11 Documentation", "url": "https://docs.python.org/3.11/", "description": "Official Python documentation with language reference, library reference, and tutorials."},
                {"title": "The Python Tutorial", "url": "https://docs.python.org/3/tutorial/", "description": "Start here for a hands-on introduction to Python."},
                {"title": "The Python Standard Library", "url": "https://docs.python.org/3/library/", "description": "This library reference manual documents Python's standard library."},
                {"title": "The Python Language Reference", "url": "https://docs.python.org/3/reference/", "description": "This reference manual describes the syntax and core semantics of the language."},
                {"title": "PEP 8 -- Style Guide for Python Code", "url": "https://www.python.org/dev/peps/pep-0008/", "description": "The official style guide for Python code."}
            ],
            "javascript": [
                {"title": "JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "description": "A comprehensive guide to JavaScript on MDN."},
                {"title": "JavaScript Reference", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference", "description": "Complete reference documentation for JavaScript on MDN."},
                {"title": "ECMAScript 6 Features", "url": "https://github.com/lukehoban/es6features", "description": "Overview of ECMAScript 6 features."},
                {"title": "Node.js Documentation", "url": "https://nodejs.org/en/docs/", "description": "Official documentation for Node.js."},
                {"title": "npm Documentation", "url": "https://docs.npmjs.com/", "description": "Official documentation for npm."}
            ],
            "react": [
                {"title": "React Documentation", "url": "https://react.dev/docs/getting-started", "description": "Official React documentation."},
                {"title": "React Hooks", "url": "https://react.dev/docs/hooks-intro", "description": "Introduction to React Hooks."},
                {"title": "React Router Documentation", "url": "https://reactrouter.com/en/main", "description": "Documentation for React Router."},
                {"title": "Redux Documentation", "url": "https://redux.js.org/", "description": "Official Redux documentation."},
                {"title": "Create React App Documentation", "url": "https://create-react-app.dev/docs/getting-started", "description": "Documentation for Create React App."}
            ]
        },
        "code": {
            "python": [
                {"title": "List Comprehension Example", "url": "https://github.com/example/python-examples/list-comprehension", "code": "[x for x in range(10) if x % 2 == 0]", "description": "Example of list comprehension in Python."},
                {"title": "Context Manager Example", "url": "https://github.com/example/python-examples/context-manager", "code": "with open('file.txt', 'r') as f:\n    content = f.read()", "description": "Example of a context manager in Python."},
                {"title": "Decorator Example", "url": "https://github.com/example/python-examples/decorator", "code": "@decorator\ndef function():\n    pass", "description": "Example of a decorator in Python."},
                {"title": "Generator Example", "url": "https://github.com/example/python-examples/generator", "code": "def generator():\n    yield 1\n    yield 2", "description": "Example of a generator in Python."},
                {"title": "Class Example", "url": "https://github.com/example/python-examples/class", "code": "class MyClass:\n    def __init__(self):\n        self.value = 42", "description": "Example of a class in Python."}
            ],
            "javascript": [
                {"title": "Array Map Example", "url": "https://github.com/example/js-examples/array-map", "code": "const doubled = [1, 2, 3].map(x => x * 2);", "description": "Example of Array.map() in JavaScript."},
                {"title": "Promise Example", "url": "https://github.com/example/js-examples/promise", "code": "fetch('https://api.example.com/data')\n  .then(response => response.json())\n  .then(data => console.log(data))\n  .catch(error => console.error(error));", "description": "Example of Promise in JavaScript."},
                {"title": "Async/Await Example", "url": "https://github.com/example/js-examples/async-await", "code": "async function fetchData() {\n  try {\n    const response = await fetch('https://api.example.com/data');\n    const data = await response.json();\n    console.log(data);\n  } catch (error) {\n    console.error(error);\n  }\n}", "description": "Example of async/await in JavaScript."},
                {"title": "Destructuring Example", "url": "https://github.com/example/js-examples/destructuring", "code": "const { name, age } = person;", "description": "Example of destructuring in JavaScript."},
                {"title": "Spread Operator Example", "url": "https://github.com/example/js-examples/spread", "code": "const combined = [...array1, ...array2];", "description": "Example of spread operator in JavaScript."}
            ],
            "react": [
                {"title": "Function Component Example", "url": "https://github.com/example/react-examples/function-component", "code": "function Welcome(props) {\n  return <h1>Hello, {props.name}</h1>;\n}", "description": "Example of a function component in React."},
                {"title": "useState Hook Example", "url": "https://github.com/example/react-examples/usestate", "code": "function Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    <div>\n      <p>You clicked {count} times</p>\n      <button onClick={() => setCount(count + 1)}>\n        Click me\n      </button>\n    </div>\n  );\n}", "description": "Example of the useState hook in React."},
                {"title": "useEffect Hook Example", "url": "https://github.com/example/react-examples/useeffect", "code": "useEffect(() => {\n  document.title = `You clicked ${count} times`;\n}, [count]);", "description": "Example of the useEffect hook in React."},
                {"title": "Context API Example", "url": "https://github.com/example/react-examples/context", "code": "const ThemeContext = React.createContext('light');\n\nfunction App() {\n  return (\n    <ThemeContext.Provider value=\"dark\">\n      <ThemedButton />\n    </ThemeContext.Provider>\n  );\n}", "description": "Example of the Context API in React."},
                {"title": "React Router Example", "url": "https://github.com/example/react-examples/router", "code": "<Router>\n  <Switch>\n    <Route exact path=\"/\">\n      <Home />\n    </Route>\n    <Route path=\"/about\">\n      <About />\n    </Route>\n  </Switch>\n</Router>", "description": "Example of React Router."}
            ]
        },
        "library": {
            "python": [
                {"name": "requests", "version": "2.31.0", "description": "HTTP library for Python", "url": "https://pypi.org/project/requests/", "popularity": "Very High"},
                {"name": "pandas", "version": "2.1.1", "description": "Data analysis and manipulation library", "url": "https://pypi.org/project/pandas/", "popularity": "Very High"},
                {"name": "numpy", "version": "1.26.0", "description": "Fundamental package for scientific computing", "url": "https://pypi.org/project/numpy/", "popularity": "Very High"},
                {"name": "matplotlib", "version": "3.8.0", "description": "Visualization library", "url": "https://pypi.org/project/matplotlib/", "popularity": "High"},
                {"name": "scikit-learn", "version": "1.3.1", "description": "Machine learning library", "url": "https://pypi.org/project/scikit-learn/", "popularity": "High"}
            ],
            "javascript": [
                {"name": "lodash", "version": "4.17.21", "description": "Utility library for JavaScript", "url": "https://www.npmjs.com/package/lodash", "popularity": "Very High"},
                {"name": "axios", "version": "1.5.1", "description": "Promise based HTTP client", "url": "https://www.npmjs.com/package/axios", "popularity": "Very High"},
                {"name": "moment", "version": "2.29.4", "description": "Date manipulation library", "url": "https://www.npmjs.com/package/moment", "popularity": "High"},
                {"name": "express", "version": "4.18.2", "description": "Web application framework", "url": "https://www.npmjs.com/package/express", "popularity": "Very High"},
                {"name": "react-redux", "version": "8.1.3", "description": "Official React bindings for Redux", "url": "https://www.npmjs.com/package/react-redux", "popularity": "High"}
            ],
            "react": [
                {"name": "react-router-dom", "version": "6.16.0", "description": "DOM bindings for React Router", "url": "https://www.npmjs.com/package/react-router-dom", "popularity": "Very High"},
                {"name": "styled-components", "version": "6.0.8", "description": "CSS-in-JS library for React", "url": "https://www.npmjs.com/package/styled-components", "popularity": "High"},
                {"name": "react-query", "version": "3.39.3", "description": "Data fetching library for React", "url": "https://www.npmjs.com/package/react-query", "popularity": "High"},
                {"name": "framer-motion", "version": "10.16.4", "description": "Animation library for React", "url": "https://www.npmjs.com/package/framer-motion", "popularity": "Medium"},
                {"name": "react-hook-form", "version": "7.47.0", "description": "Form validation library for React", "url": "https://www.npmjs.com/package/react-hook-form", "popularity": "High"}
            ]
        },
        "error": {
            "python": [
                {"error": "IndentationError: unexpected indent", "solution": "Check your code for inconsistent indentation. Python uses indentation to define blocks.", "example": "if condition:\nprint('indented')  # Incorrect\n\nif condition:\n    print('indented')  # Correct"},
                {"error": "NameError: name 'variable' is not defined", "solution": "The variable you're trying to use doesn't exist in the current scope. Check for typos or make sure it's defined before use.", "example": "# Solution: Define the variable before using it\nvariable = 'value'\nprint(variable)"},
                {"error": "TypeError: can only concatenate str (not \"int\") to str", "solution": "You're trying to concatenate a string and an integer. Convert the integer to a string first.", "example": "name = 'John'\nage = 30\n# Error: print(name + age)\n# Solution: \nprint(name + str(age))"},
                {"error": "ImportError: No module named 'module'", "solution": "The module you're trying to import isn't installed or in your Python path.", "example": "# Solution: Install the module\n# pip install module_name"},
                {"error": "KeyError: 'key'", "solution": "The key you're trying to access doesn't exist in the dictionary.", "example": "data = {'a': 1, 'b': 2}\n# Error: data['c']\n# Solution:\nif 'c' in data:\n    value = data['c']\nelse:\n    value = None\n# Or use .get() method\nvalue = data.get('c')"}
            ],
            "javascript": [
                {"error": "TypeError: Cannot read property 'property' of undefined", "solution": "You're trying to access a property of an undefined value. Check if the object exists before accessing its properties.", "example": "// Error: const value = obj.prop.nestedProp\n// Solution:\nconst value = obj && obj.prop && obj.prop.nestedProp;\n// Or with optional chaining:\nconst value = obj?.prop?.nestedProp;"},
                {"error": "SyntaxError: Unexpected token", "solution": "There's a syntax error in your code. Check for missing brackets, parentheses, or commas.", "example": "// Various syntax error examples and fixes would go here"},
                {"error": "ReferenceError: variable is not defined", "solution": "You're trying to use a variable that doesn't exist in the current scope.", "example": "// Solution: Declare the variable before using it\nlet variable = 'value';\nconsole.log(variable);"},
                {"error": "Uncaught (in promise) TypeError", "solution": "An error occurred inside a Promise that wasn't caught with a .catch() or try/catch in an async function.", "example": "// Solution: Add error handling\nfetch('/api/data')\n  .then(response => response.json())\n  .then(data => console.log(data))\n  .catch(error => console.error('Error:', error));"},
                {"error": "TypeError: X is not a function", "solution": "You're trying to call something that's not a function. Check variable types and typos.", "example": "// Error: const result = object.methd();\n// Solution: Fix the typo\nconst result = object.method();"}
            ],
            "react": [
                {"error": "Error: Too many re-renders", "solution": "This usually happens when you update state in a component render function, creating an infinite loop.", "example": "// Error:\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  setCount(count + 1); // This causes infinite re-renders\n  return <div>{count}</div>;\n}\n\n// Solution:\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  useEffect(() => {\n    setCount(count + 1);\n  }, []); // Run once on mount\n  return <div>{count}</div>;\n}"},
                {"error": "Warning: Each child in a list should have a unique \"key\" prop", "solution": "When rendering a list in React, each item needs a unique key prop for efficient updates.", "example": "// Error:\nfunction List({ items }) {\n  return (\n    <ul>\n      {items.map(item => <li>{item.text}</li>)}\n    </ul>\n  );\n}\n\n// Solution:\nfunction List({ items }) {\n  return (\n    <ul>\n      {items.map(item => <li key={item.id}>{item.text}</li>)}\n    </ul>\n  );\n}"},
                {"error": "Error: Invalid hook call", "solution": "Hooks can only be called inside function components or custom hooks, not in regular functions or class components.", "example": "// Solution: Ensure hooks are only called in function components or custom hooks"},
                {"error": "Error: Objects are not valid as a React child", "solution": "You're trying to render an object directly, which React doesn't support. Convert it to a string or other renderable format.", "example": "// Error:\nreturn <div>{someObject}</div>;\n\n// Solution:\nreturn <div>{JSON.stringify(someObject)}</div>;"},
                {"error": "Warning: Can't perform a React state update on an unmounted component", "solution": "You're trying to update state in a component that has already unmounted, often in an async callback.", "example": "// Solution: Use a cleanup function in useEffect\nuseEffect(() => {\n  let isMounted = true;\n  fetchData().then(data => {\n    if (isMounted) {\n      setState(data);\n    }\n  });\n  return () => {\n    isMounted = false;\n  };\n}, []);"}
            ]
        }
    }
    
    def __init__(self):
        """Initialize the search tool."""
        self.logger = logging.getLogger("devassist.tools.search")
    
    def execute(self, query: str, search_type: str = "general", 
                technology: str = None, max_results: int = 5,
                filter: Dict[str, Any] = None, **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Execute the search tool to find development resources.
        
        Args:
            query: The search query.
            search_type: Type of search to perform.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            **kwargs: Additional parameters.
            
        Returns:
            Search results.
        """
        try:
            self.logger.info(f"Searching for '{query}' with type '{search_type}' in technology '{technology}'")
            
            # Normalize search parameters
            search_type = search_type.lower() if search_type else "general"
            technology = technology.lower() if technology else None
            max_results = min(max(1, max_results), 10)  # Limit between 1 and 10
            filter = filter or {}
            
            # Perform the appropriate search
            if search_type == "documentation":
                results = self._search_documentation(query, technology, max_results, filter)
            elif search_type == "code":
                results = self._search_code_examples(query, technology, max_results, filter)
            elif search_type == "library":
                results = self._search_libraries(query, technology, max_results, filter)
            elif search_type == "error":
                results = self._search_error_solutions(query, technology, max_results, filter)
            else:
                # General search combines results from multiple types
                results = self._search_general(query, technology, max_results, filter)
            
            # Return success result
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "query": query,
                    "search_type": search_type,
                    "technology": technology,
                    "result_count": len(results),
                    "results": results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Error during search: {str(e)}"
            )
    
    def _search_documentation(self, query: str, technology: str,
                             max_results: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for documentation resources.
        
        Args:
            query: The search query.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            
        Returns:
            A list of documentation resources.
        """
        results = []
        
        # Check if we have mock data for the specified technology
        if technology and technology in self._MOCK_DATA.get("documentation", {}):
            docs = self._MOCK_DATA["documentation"][technology]
            
            # Filter by query
            filtered_docs = self._filter_results(docs, query)
            
            # Add top results
            results.extend(filtered_docs[:max_results])
        else:
            # If technology not specified or not found, return general results
            for tech, docs in self._MOCK_DATA.get("documentation", {}).items():
                if len(results) >= max_results:
                    break
                    
                # Filter by query
                filtered_docs = self._filter_results(docs, query)
                
                # Add top results (limited to remaining slots)
                remaining = max_results - len(results)
                results.extend(filtered_docs[:remaining])
        
        return results
    
    def _search_code_examples(self, query: str, technology: str,
                             max_results: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for code examples.
        
        Args:
            query: The search query.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            
        Returns:
            A list of code examples.
        """
        results = []
        
        # Check if we have mock data for the specified technology
        if technology and technology in self._MOCK_DATA.get("code", {}):
            examples = self._MOCK_DATA["code"][technology]
            
            # Filter by query
            filtered_examples = self._filter_results(examples, query)
            
            # Add top results
            results.extend(filtered_examples[:max_results])
        else:
            # If technology not specified or not found, return general results
            for tech, examples in self._MOCK_DATA.get("code", {}).items():
                if len(results) >= max_results:
                    break
                    
                # Filter by query
                filtered_examples = self._filter_results(examples, query)
                
                # Add top results (limited to remaining slots)
                remaining = max_results - len(results)
                results.extend(filtered_examples[:remaining])
        
        return results
    
    def _search_libraries(self, query: str, technology: str,
                         max_results: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for libraries and packages.
        
        Args:
            query: The search query.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            
        Returns:
            A list of libraries.
        """
        results = []
        
        # Check if we have mock data for the specified technology
        if technology and technology in self._MOCK_DATA.get("library", {}):
            libraries = self._MOCK_DATA["library"][technology]
            
            # Filter by query
            filtered_libs = self._filter_results(libraries, query, key_field="name")
            
            # Add top results
            results.extend(filtered_libs[:max_results])
        else:
            # If technology not specified or not found, return general results
            for tech, libraries in self._MOCK_DATA.get("library", {}).items():
                if len(results) >= max_results:
                    break
                    
                # Filter by query
                filtered_libs = self._filter_results(libraries, query, key_field="name")
                
                # Add top results (limited to remaining slots)
                remaining = max_results - len(results)
                results.extend(filtered_libs[:remaining])
        
        return results
    
    def _search_error_solutions(self, query: str, technology: str,
                               max_results: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for error solutions.
        
        Args:
            query: The search query.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            
        Returns:
            A list of error solutions.
        """
        results = []
        
        # Check if we have mock data for the specified technology
        if technology and technology in self._MOCK_DATA.get("error", {}):
            errors = self._MOCK_DATA["error"][technology]
            
            # Filter by query
            filtered_errors = self._filter_results(errors, query, key_field="error")
            
            # Add top results
            results.extend(filtered_errors[:max_results])
        else:
            # If technology not specified or not found, return general results
            for tech, errors in self._MOCK_DATA.get("error", {}).items():
                if len(results) >= max_results:
                    break
                    
                # Filter by query
                filtered_errors = self._filter_results(errors, query, key_field="error")
                
                # Add top results (limited to remaining slots)
                remaining = max_results - len(results)
                results.extend(filtered_errors[:remaining])
        
        return results
    
    def _search_general(self, query: str, technology: str,
                       max_results: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform a general search across all types.
        
        Args:
            query: The search query.
            technology: Specific technology to search within.
            max_results: Maximum number of results to return.
            filter: Additional filters for the search.
            
        Returns:
            A list of mixed search results.
        """
        results = []
        
        # Allocate results per type
        docs_count = max(1, max_results // 3)
        code_count = max(1, max_results // 3)
        lib_count = max(1, max_results // 3)
        
        # Gather results from each type
        doc_results = self._search_documentation(query, technology, docs_count, filter)
        code_results = self._search_code_examples(query, technology, code_count, filter)
        lib_results = self._search_libraries(query, technology, lib_count, filter)
        
        # Add type to each result for clarity
        for result in doc_results:
            result["result_type"] = "documentation"
        for result in code_results:
            result["result_type"] = "code_example"
        for result in lib_results:
            result["result_type"] = "library"
        
        # Combine results
        results.extend(doc_results)
        results.extend(code_results)
        results.extend(lib_results)
        
        # If we still have room for more results, try error solutions
        if len(results) < max_results:
            remaining = max_results - len(results)
            error_results = self._search_error_solutions(query, technology, remaining, filter)
            for result in error_results:
                result["result_type"] = "error_solution"
            results.extend(error_results)
        
        # Ensure we don't exceed max_results
        return results[:max_results]
    
    def _filter_results(self, items: List[Dict[str, Any]], query: str, 
                       key_field: str = "title") -> List[Dict[str, Any]]:
        """
        Filter results based on query relevance.
        
        Args:
            items: List of items to filter.
            query: The search query.
            key_field: The field to primarily match against.
            
        Returns:
            Filtered and sorted results.
        """
        filtered = []
        query_terms = query.lower().split()
        
        for item in items:
            # Calculate relevance score
            score = 0
            
            # Check primary field
            if key_field in item:
                primary_text = str(item[key_field]).lower()
                # Exact match gets high score
                if query.lower() in primary_text:
                    score += 10
                # Term matches get medium score
                for term in query_terms:
                    if term in primary_text:
                        score += 5
            
            # Check description field if present
            if "description" in item:
                desc = item["description"].lower()
                # Description match gets lower score
                if query.lower() in desc:
                    score += 3
                # Term matches in description
                for term in query_terms:
                    if term in desc:
                        score += 2
            
            # Check all other fields (lower score)
            for field, value in item.items():
                if field not in [key_field, "description"] and isinstance(value, str):
                    text = value.lower()
                    if query.lower() in text:
                        score += 1
                    for term in query_terms:
                        if term in text:
                            score += 0.5
            
            # Add item with its score if relevant
            if score > 0:
                filtered.append({"item": item, "score": score})
        
        # Sort by relevance score (descending)
        filtered.sort(key=lambda x: x["score"], reverse=True)
        
        # Return only the items (without scores)
        return [item["item"] for item in filtered]
