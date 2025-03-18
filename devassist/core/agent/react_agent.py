"""
React Agent module that extends the base agent with reasoning capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import logging

from devassist.core.agent.base_agent import BaseAgent

class ReactAgent(BaseAgent):
    """
    A reasoning agent that follows the React paradigm (Reasoning and Acting).
    
    This agent implements a thought-action-observation loop for complex reasoning.
    """
    
    def __init__(self, name: Optional[str] = None, max_iterations: int = 10, **kwargs):
        """
        Initialize a ReactAgent instance.
        
        Args:
            name: Optional name for the agent.
            max_iterations: Maximum number of thought-action cycles to perform.
            **kwargs: Additional configuration options for the agent.
        """
        super().__init__(name=name, **kwargs)
        self.max_iterations = max_iterations
        self.current_iteration = 0
    
    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task using the React paradigm.
        
        Args:
            task: The task description to execute.
            **kwargs: Additional parameters for task execution.
            
        Returns:
            A dictionary containing the execution result and metadata.
        """
        self.update_state(status="executing", task=task)
        self.current_iteration = 0
        
        logging.info(f"Agent '{self.name}' executing task: {task}")
        
        # Initialize the context with the task
        context = {
            "task": task,
            "thoughts": [],
            "actions": [],
            "observations": []
        }
        
        # Main React loop
        while self.current_iteration < self.max_iterations:
            logging.debug(f"Agent '{self.name}' starting iteration {self.current_iteration+1}/{self.max_iterations}")
            
            # Generate thought
            thought = self._generate_thought(context)
            context["thoughts"].append(thought)
            logging.debug(f"Agent '{self.name}' thought: {thought}")
            
            # Decide on action
            action_name, action_input = self._decide_action(context)
            action = {"name": action_name, "input": action_input}
            context["actions"].append(action)
            logging.debug(f"Agent '{self.name}' action: {action_name}")
            
            # Execute action and get observation
            observation = self._execute_action(action_name, action_input)
            context["observations"].append(observation)
            logging.debug(f"Agent '{self.name}' observation: {str(observation)[:100]}...")
            
            # Log the iteration
            self.log_action("iteration", {
                "iteration": self.current_iteration,
                "thought": thought,
                "action": action,
                "observation": observation
            })
            
            # Check if we should terminate
            if self._should_terminate(context):
                logging.info(f"Agent '{self.name}' terminating after {self.current_iteration+1} iterations")
                break
                
            self.current_iteration += 1
        
        # Generate final answer
        final_answer = self._generate_final_answer(context)
        logging.info(f"Agent '{self.name}' completed task with answer: {final_answer[:100]}...")
        
        result = {
            "task": task,
            "answer": final_answer,
            "iterations": self.current_iteration + 1,
            "context": context
        }
        
        self.update_state(status="completed")
        return result
    
    def _generate_thought(self, context: Dict[str, Any]) -> str:
        """
        Generate a thought based on the current context.
        
        Args:
            context: The current execution context.
            
        Returns:
            The thought string.
        """
        # This should be implemented using a language model
        # Currently using a placeholder
        return f"Thinking about how to {context['task']} (iteration {self.current_iteration})"
    
    def _decide_action(self, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Decide on the next action to take.
        
        Args:
            context: The current execution context.
            
        Returns:
            A tuple of (action_name, action_input).
        """
        # This should be implemented using a language model
        # Currently using a placeholder
        return "dummy_action", {"query": f"Placeholder action for {context['task']}"}
    
    def _execute_action(self, action_name: str, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action and return the observation.
        
        Args:
            action_name: The name of the action to execute.
            action_input: The input parameters for the action.
            
        Returns:
            The observation from executing the action.
        """
        # This should be overridden by subclasses
        return {"status": "error", "error": f"Unknown action or tool: {action_name}"}
    
    def _should_terminate(self, context: Dict[str, Any]) -> bool:
        """
        Check if execution should terminate.
        
        Args:
            context: The current execution context.
            
        Returns:
            True if execution should terminate, False otherwise.
        """
        # This should check if we've found a satisfactory answer
        # Currently using a placeholder
        return self.current_iteration >= self.max_iterations - 1
    
    def _generate_final_answer(self, context: Dict[str, Any]) -> str:
        """
        Generate a final answer based on the context.
        
        Args:
            context: The current execution context.
            
        Returns:
            The final answer string.
        """
        # Default implementation checks for successful tool executions
        for observation in context.get("observations", []):
            if isinstance(observation, dict) and "result" in observation:
                result = observation["result"]
                if isinstance(result, dict) and "status" == "success":
                    return str(result.get("result", "Task completed successfully"))
                
        # Return a generic message if no specific result found
        return "Task execution completed. Please check the detailed results for more information."