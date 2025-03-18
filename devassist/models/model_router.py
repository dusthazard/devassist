"""
Model Router module for dynamic model selection and management.

This module provides functionality for selecting and managing different language
models based on task requirements, ensuring optimal model usage for different
development tasks.
"""

from typing import Dict, List, Any, Optional, Union, Type
import logging
import os
import json
import time

from devassist.models.base.base_model import BaseModel
from devassist.models.openai_model import OpenAIModel

class ModelRouter:
    """
    Router for dynamically selecting and managing language models.
    
    Provides functionality for:
    - Registering different model implementations
    - Selecting models based on task requirements
    - Fallback mechanisms for reliability
    - Cost optimization
    
    The router helps choose the most appropriate model for specific development
    tasks, balancing capability, cost, and performance.
    """
    
    def __init__(self, default_model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a ModelRouter instance.
        
        Args:
            default_model_config: Configuration for the default model.
                                  If None, uses OpenAI GPT-4 with default settings.
        """
        self.models: Dict[str, BaseModel] = {}
        self.model_classes: Dict[str, Type[BaseModel]] = {
            "openai": OpenAIModel
        }
        self.default_model_config = default_model_config or {
            "provider": "openai",
            "model_name": "gpt-4",
            "temperature": 0.0
        }
        self.default_model = None
        
        # Cache for models to avoid recreating them
        self._model_cache: Dict[str, BaseModel] = {}
        
        # Model usage statistics for optimization
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Development-specific model mappings
        self.task_model_mappings: Dict[str, Dict[str, Any]] = {
            "code_generation": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.2
            },
            "code_explanation": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.3
            },
            "debugging": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.0
            },
            "refactoring": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.1
            },
            "documentation": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.4
            },
            "planning": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.2
            }
        }
        
        self.logger = logging.getLogger("devassist.models.router")
    
    def register_model(self, name: str, model: BaseModel) -> None:
        """
        Register a model instance.
        
        Args:
            name: A unique name for the model.
            model: The model instance to register.
        """
        self.models[name] = model
        self.logger.info(f"Registered model: {name}")
    
    def register_model_class(self, provider: str, model_class: Type[BaseModel]) -> None:
        """
        Register a model class for a provider.
        
        Args:
            provider: The model provider name.
            model_class: The model class to register.
        """
        self.model_classes[provider] = model_class
        self.logger.info(f"Registered model class for provider: {provider}")
    
    def get_model(self, name_or_config: Union[str, Dict[str, Any]]) -> BaseModel:
        """
        Get a model instance by name or create one from config.
        
        Args:
            name_or_config: Either a model name or a model configuration dictionary.
            
        Returns:
            A model instance.
        """
        # Check if it's cached
        cache_key = name_or_config if isinstance(name_or_config, str) else json.dumps(name_or_config, sort_keys=True)
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]
        
        # If it's a string, look up by name
        if isinstance(name_or_config, str):
            # Check registered models
            if name_or_config in self.models:
                model = self.models[name_or_config]
                self._model_cache[cache_key] = model
                return model
            
            # Check task model mappings
            if name_or_config in self.task_model_mappings:
                model = self._create_model_from_config(self.task_model_mappings[name_or_config])
                self._model_cache[cache_key] = model
                return model
            
            # If not found, use default model
            self.logger.warning(f"Model '{name_or_config}' not found. Using default model.")
            return self.get_default_model()
        
        # If it's a config dict, create a new model
        elif isinstance(name_or_config, dict):
            model = self._create_model_from_config(name_or_config)
            self._model_cache[cache_key] = model
            return model
        
        # Invalid input
        else:
            self.logger.error(f"Invalid model specification: {name_or_config}")
            return self.get_default_model()
    
    def get_default_model(self) -> BaseModel:
        """
        Get the default model, creating it if necessary.
        
        Returns:
            The default model instance.
        """
        if self.default_model is None:
            self.default_model = self._create_model_from_config(self.default_model_config)
        
        return self.default_model
    
    def select_model_for_task(self, task: str, requirements: Optional[Dict[str, Any]] = None) -> BaseModel:
        """
        Select an appropriate model for a given development task.
        
        Args:
            task: The task description.
            requirements: Optional requirements for the model, which may include:
                          - complexity: Task complexity (0-1)
                          - domain: Development domain (frontend, backend, etc.)
                          - quality: Required output quality (0-1)
                          - latency: Maximum acceptable latency (seconds)
                          - cost: Maximum acceptable cost
            
        Returns:
            The selected model instance.
        """
        requirements = requirements or {}
        
        # Check if complexity is specified
        complexity = requirements.get("complexity")
        
        # Check if domain is specified
        domain = requirements.get("domain")
        
        # Detect task type
        task_type = self._detect_task_type(task)
        
        # Use task type to select a model if available
        if task_type in self.task_model_mappings:
            return self.get_model(task_type)
        
        # If domain-specific configs exist, use them
        if domain and f"{domain}_tasks" in self.task_model_mappings:
            return self.get_model(f"{domain}_tasks")
            
        # If complexity is high, use a more capable model
        if complexity is not None and complexity > 0.7:
            # Create a config for a high-complexity task
            config = self.default_model_config.copy()
            config["model_name"] = self._get_powerful_model_name(config["provider"])
            config["temperature"] = 0.1  # Lower temperature for complex tasks
            return self._create_model_from_config(config)
        
        # Default to the default model
        return self.get_default_model()
    
    def track_model_usage(self, model_name: str, task_type: str, tokens_used: int, latency: float) -> None:
        """
        Track model usage for optimization.
        
        Args:
            model_name: The name of the model used.
            task_type: The type of task performed.
            tokens_used: The number of tokens used.
            latency: The latency of the request in seconds.
        """
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = {
                "total_tokens": 0,
                "total_requests": 0,
                "total_latency": 0.0,
                "task_types": {}
            }
        
        # Update model stats
        self.usage_stats[model_name]["total_tokens"] += tokens_used
        self.usage_stats[model_name]["total_requests"] += 1
        self.usage_stats[model_name]["total_latency"] += latency
        
        # Update task type stats
        if task_type not in self.usage_stats[model_name]["task_types"]:
            self.usage_stats[model_name]["task_types"][task_type] = {
                "tokens": 0,
                "requests": 0,
                "latency": 0.0
            }
        
        self.usage_stats[model_name]["task_types"][task_type]["tokens"] += tokens_used
        self.usage_stats[model_name]["task_types"][task_type]["requests"] += 1
        self.usage_stats[model_name]["task_types"][task_type]["latency"] += latency
    
    def optimize_model_mappings(self) -> None:
        """
        Optimize model mappings based on usage statistics.
        
        This method analyzes usage patterns and adjusts task-model mappings
        to optimize for cost, performance, and quality.
        """
        if not self.usage_stats:
            self.logger.info("No usage statistics available for optimization.")
            return
        
        # Calculate average latency per token for each model
        model_efficiency: Dict[str, float] = {}
        for model_name, stats in self.usage_stats.items():
            if stats["total_tokens"] > 0:
                model_efficiency[model_name] = stats["total_latency"] / stats["total_tokens"]
        
        # Find the most efficient model for each task type
        for task_type in self.task_model_mappings:
            best_model = None
            best_efficiency = float('inf')
            
            for model_name, stats in self.usage_stats.items():
                if task_type in stats["task_types"]:
                    task_stats = stats["task_types"][task_type]
                    if task_stats["tokens"] > 0:
                        efficiency = task_stats["latency"] / task_stats["tokens"]
                        if efficiency < best_efficiency:
                            best_efficiency = efficiency
                            best_model = model_name
            
            # Update the mapping if a better model is found
            if best_model and best_model != self.task_model_mappings[task_type].get("model_name"):
                self.logger.info(f"Optimizing {task_type} tasks to use {best_model}")
                # Extract model details to update the mapping
                for name, model in self.models.items():
                    if name == best_model:
                        self.task_model_mappings[task_type] = {
                            "provider": model.__class__.__module__.split(".")[-1].replace("_model", ""),
                            "model_name": model.model_name,
                            "temperature": model.temperature
                        }
                        break
    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for model usage based on statistics.
        
        Returns:
            A dictionary of recommendations for model usage.
        """
        if not self.usage_stats:
            return {"message": "No usage statistics available for recommendations."}
        
        recommendations = {
            "most_used_model": None,
            "most_efficient_model": None,
            "task_recommendations": {}
        }
        
        # Find most used model
        most_used_model = None
        most_used_tokens = 0
        for model_name, stats in self.usage_stats.items():
            if stats["total_tokens"] > most_used_tokens:
                most_used_tokens = stats["total_tokens"]
                most_used_model = model_name
        
        recommendations["most_used_model"] = {
            "name": most_used_model,
            "tokens": most_used_tokens,
            "requests": self.usage_stats[most_used_model]["total_requests"] if most_used_model else 0
        }
        
        # Find most efficient model
        model_efficiency = {}
        for model_name, stats in self.usage_stats.items():
            if stats["total_tokens"] > 0:
                model_efficiency[model_name] = stats["total_latency"] / stats["total_tokens"]
        
        if model_efficiency:
            most_efficient_model = min(model_efficiency, key=model_efficiency.get)
            recommendations["most_efficient_model"] = {
                "name": most_efficient_model,
                "efficiency": model_efficiency[most_efficient_model]
            }
        
        # Generate task-specific recommendations
        task_types = set()
        for stats in self.usage_stats.values():
            task_types.update(stats["task_types"].keys())
        
        for task_type in task_types:
            # Find the most efficient model for this task
            task_efficiency = {}
            for model_name, stats in self.usage_stats.items():
                if task_type in stats["task_types"]:
                    task_stats = stats["task_types"][task_type]
                    if task_stats["tokens"] > 0:
                        task_efficiency[model_name] = task_stats["latency"] / task_stats["tokens"]
            
            if task_efficiency:
                best_model = min(task_efficiency, key=task_efficiency.get)
                recommendations["task_recommendations"][task_type] = {
                    "recommended_model": best_model,
                    "efficiency": task_efficiency[best_model]
                }
        
        return recommendations
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models.
        
        Returns:
            A list of model information dictionaries.
        """
        models_info = []
        
        # Add instantiated models
        for name, model in self.models.items():
            info = {
                "name": name,
                "type": type(model).__name__,
                "model_name": model.model_name,
                "provider": model.__class__.__module__.split(".")[-1].replace("_model", ""),
                "temperature": model.temperature,
                "details": model.get_model_details()
            }
            models_info.append(info)
        
        # Add available providers
        for provider in self.model_classes.keys():
            if provider not in [info.get("provider") for info in models_info]:
                models_info.append({
                    "name": f"{provider}",
                    "provider": provider,
                    "type": self.model_classes[provider].__name__,
                    "available": True
                })
        
        return models_info
    
    def get_task_model_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current task-model mappings.
        
        Returns:
            A dictionary mapping task types to model configurations.
        """
        return self.task_model_mappings
    
    def set_task_model_mapping(self, task_type: str, model_config: Dict[str, Any]) -> None:
        """
        Set a task-model mapping.
        
        Args:
            task_type: The type of task.
            model_config: The model configuration to use for this task type.
        """
        self.task_model_mappings[task_type] = model_config
        self.logger.info(f"Updated task-model mapping for {task_type}")
        
        # Clear the cache for this task type if it exists
        if task_type in self._model_cache:
            del self._model_cache[task_type]
    
    def _create_model_from_config(self, config: Dict[str, Any]) -> BaseModel:
        """
        Create a model instance from a configuration dictionary.
        
        Args:
            config: The model configuration.
            
        Returns:
            A model instance.
        """
        # Get the provider
        provider = config.get("provider", "openai").lower()
        
        # Check if we have a class for this provider
        if provider not in self.model_classes:
            self.logger.error(f"Unknown model provider: {provider}. Using OpenAI as fallback.")
            provider = "openai"
        
        try:
            # Get the model class
            model_class = self.model_classes[provider]
            
            # Extract kwargs for the model
            kwargs = config.copy()
            kwargs.pop("provider", None)
            
            # Create the model
            return model_class(**kwargs)
            
        except Exception as e:
            self.logger.error(f"Error creating model for provider {provider}: {e}")
            
            # Fallback to OpenAI with minimal config
            try:
                return OpenAIModel(model_name="gpt-4")
            except Exception as e2:
                self.logger.error(f"Fallback model creation also failed: {e2}")
                raise ValueError(f"Failed to create model: {e}")
    
    def _detect_task_type(self, task: str) -> Optional[str]:
        """
        Detect the type of development task from its description.
        
        Args:
            task: The task description.
            
        Returns:
            The detected task type, or None if uncertain.
        """
        task_lower = task.lower()
        
        # Check for code generation tasks
        if any(keyword in task_lower for keyword in ["create", "write", "implement", "build", "develop", "generate code"]):
            return "code_generation"
        
        # Check for code explanation tasks
        if any(keyword in task_lower for keyword in ["explain", "understand", "clarify", "what does", "how does"]):
            return "code_explanation"
        
        # Check for debugging tasks
        if any(keyword in task_lower for keyword in ["debug", "fix", "issue", "problem", "error", "doesn't work", "not working"]):
            return "debugging"
        
        # Check for refactoring tasks
        if any(keyword in task_lower for keyword in ["refactor", "improve", "optimize", "clean", "better"]):
            return "refactoring"
        
        # Check for documentation tasks
        if any(keyword in task_lower for keyword in ["document", "documentation", "comments", "explain code", "readme"]):
            return "documentation"
        
        # Check for planning tasks
        if any(keyword in task_lower for keyword in ["plan", "design", "architect", "structure", "organize"]):
            return "planning"
        
        # No clear task type detected
        return None
    
    def _get_powerful_model_name(self, provider: str) -> str:
        """
        Get the name of a more powerful model for a given provider.
        
        Args:
            provider: The provider name.
            
        Returns:
            The name of a powerful model from the provider.
        """
        provider_models = {
            "openai": "gpt-4",
            "anthropic": "claude-3-opus",
            "cohere": "command-r-plus",
            "mistral": "mixtral-8x7b"
        }
        
        return provider_models.get(provider, "gpt-4")
