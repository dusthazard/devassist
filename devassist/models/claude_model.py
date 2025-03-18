"""
Claude/Anthropic Model implementation for the DevAssist framework.
"""

from typing import Dict, List, Any, Optional, Union
import json
import logging
import os

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from devassist.models.base.base_model import BaseModel

class ClaudeModel(BaseModel):
    """
    Anthropic Claude language model implementation.
    
    Provides integration with Anthropic's Claude models for text generation and tool usage.
    """
    
    def __init__(
        self, 
        model_name: str = "claude-3-opus-20240229", 
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a ClaudeModel instance.
        
        Args:
            model_name: The name of the Claude model to use. 
                       (e.g., 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307')
            temperature: Controls randomness in outputs. Lower values are more deterministic.
            max_tokens: Maximum number of tokens to generate.
            api_key: Anthropic API key. If None, it will be read from the ANTHROPIC_API_KEY environment variable.
            **kwargs: Additional model-specific parameters.
        """
        super().__init__(model_name, temperature, max_tokens, **kwargs)
        
        if not ANTHROPIC_AVAILABLE:
            logging.error("Anthropic package not installed. Please install it with 'pip install anthropic'.")
            raise ImportError("Anthropic package not installed")
        
        # Use provided API key or read from environment
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logging.error("Anthropic API key not provided and not found in environment.")
            raise ValueError("Anthropic API key required")
        
        # Initialize client
        self.client = Anthropic(api_key=self.api_key)
        
        # Set default embedding model - Claude doesn't have a native embedding model yet
        # For embeddings, users should use OpenAI or other embedding providers
        self.embedding_model = None
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text based on a prompt using Claude.
        
        Args:
            prompt: The text prompt for generation.
            system_message: Optional system message for the model.
            temperature: Controls randomness in outputs. Overrides instance value if provided.
            max_tokens: Maximum number of tokens to generate. Overrides instance value if provided.
            **kwargs: Additional Claude-specific parameters.
            
        Returns:
            The generated text response.
        """
        # Set parameters
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens or 4096
        
        try:
            # Make the API call
            message = self.client.messages.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                system=system_message,
                temperature=temp,
                max_tokens=tokens,
                **kwargs
            )
            
            # Extract and return the response text
            return message.content[0].text
        
        except Exception as e:
            logging.error(f"Error generating with Claude: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_tools(
        self, 
        prompt: str, 
        tools: List[Dict[str, Any]],
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text with tool calling capabilities.
        
        Args:
            prompt: The text prompt for generation.
            tools: List of tool schemas available for use.
            system_message: Optional system message for the model.
            temperature: Controls randomness in outputs. Overrides instance value if provided.
            max_tokens: Maximum number of tokens to generate. Overrides instance value if provided.
            **kwargs: Additional Claude-specific parameters.
            
        Returns:
            A dictionary with the response and any tool calls.
        """
        # Set parameters
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens or 4096
        
        # Convert tools to Claude's tool format
        claude_tools = []
        for tool in tools:
            claude_tool = {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {})
            }
            claude_tools.append(claude_tool)
        
        try:
            # Make the API call with tools
            message = self.client.messages.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                system=system_message,
                temperature=temp,
                max_tokens=tokens,
                tools=claude_tools,
                tool_choice="auto",
                **kwargs
            )
            
            # Extract response content and tool calls
            content = message.content[0].text if message.content and message.content[0].type == 'text' else ""
            
            # Process tool calls if any
            tool_calls = []
            for content_block in message.content:
                if content_block.type == "tool_use":
                    tool_call = {
                        "id": content_block.id,
                        "name": content_block.name,
                        "arguments": content_block.input
                    }
                    tool_calls.append(tool_call)
            
            return {
                "content": content,
                "tool_calls": tool_calls
            }
        
        except Exception as e:
            logging.error(f"Error generating with tools using Claude: {e}")
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": []
            }
    
    def extract_json(
        self, 
        prompt: str, 
        schema: Dict[str, Any],
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract structured JSON data based on a prompt.
        
        Args:
            prompt: The text prompt for extraction.
            schema: JSON schema describing the expected structure.
            system_message: Optional system message for the model.
            temperature: Controls randomness in outputs. Overrides instance value if provided.
            max_tokens: Maximum number of tokens to generate. Overrides instance value if provided.
            **kwargs: Additional Claude-specific parameters.
            
        Returns:
            The extracted JSON data.
        """
        # Set default system message for JSON extraction if not provided
        if not system_message:
            system_message = """
            Extract the requested information and respond ONLY with a valid JSON object according to the specified schema.
            Do not include any other text, explanation, or markdown formatting.
            The JSON should be valid and match the provided schema exactly.
            """
        
        # Set parameters
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens or 4096
        
        # Prepare prompt with schema
        extraction_prompt = f"""
        JSON Schema:
        ```json
        {json.dumps(schema, indent=2)}
        ```

        Based on this schema, extract the information from the following prompt:

        {prompt}

        Respond with ONLY the JSON object, nothing else.
        """
        
        try:
            # Make the API call
            message = self.client.messages.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                system=system_message,
                temperature=temp,
                max_tokens=tokens,
                **kwargs
            )
            
            # Extract and parse the response
            content = message.content[0].text if message.content else ""
            
            # Try to parse JSON from the response
            # First, clean any potential markdown formatting
            json_str = content
            if "```json" in json_str and "```" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON from response: {content}")
                return {"error": "Failed to parse JSON response"}
        
        except Exception as e:
            logging.error(f"Error extracting JSON with Claude: {e}")
            return {"error": str(e)}
    
    def get_embedding(self, text: str, **kwargs) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Note: Claude does not yet have a native embedding model. This is a placeholder
        that logs an error and returns an empty list. For embeddings, use an alternative
        provider like OpenAI.
        
        Args:
            text: The text to embed.
            **kwargs: Additional parameters.
            
        Returns:
            The embedding vector as a list of floats.
        """
        logging.error("Claude does not provide an embedding API. Please use OpenAI or another embedding provider.")
        return []
