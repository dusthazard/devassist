"""
Base Planner module that defines the common interface for task planning.

This module provides the foundation for all planners in the DevAssist framework,
ensuring consistent task planning capabilities across different planning strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

class BasePlanner(ABC):
    """
    Abstract base class for planners in the DevAssist framework.
    
    Provides the core functionality for breaking down development tasks into steps.
    
    The planner is responsible for:
    - Creating initial development plans
    - Adapting plans based on execution feedback
    - Tracking dependencies between steps
    - Providing the next step to execute
    - Marking steps as complete
    """
    
    def __init__(self, **kwargs):
        """
        Initialize a BasePlanner instance.
        
        Args:
            **kwargs: Additional configuration options for the planner.
        """
        self.config = kwargs
        self.logger = logging.getLogger("devassist.planning")
    
    @abstractmethod
    def create_plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a plan for executing a development task.
        
        Args:
            task: The task description.
            context: Optional context for planning including project information, 
                    technologies, constraints, etc.
            
        Returns:
            A plan dictionary with steps and metadata.
        """
        pass
    
    @abstractmethod
    def replan(self, plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a plan based on execution feedback.
        
        Args:
            plan: The current plan.
            feedback: Feedback from execution, which may include error messages,
                     new requirements, or other information that necessitates replanning.
            
        Returns:
            The updated plan.
        """
        pass
    
    @abstractmethod
    def get_next_step(self, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next step to execute from a plan.
        
        This method considers dependencies between steps and returns the next
        step that has all dependencies satisfied.
        
        Args:
            plan: The current plan.
            
        Returns:
            The next step to execute, or None if the plan is complete.
        """
        pass
    
    @abstractmethod
    def mark_step_complete(self, plan: Dict[str, Any], step_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark a step as complete in a plan.
        
        Args:
            plan: The current plan.
            step_id: The ID of the completed step.
            result: The result of the step execution, which may include code snippets,
                   files created, or other output.
            
        Returns:
            The updated plan.
        """
        pass
    
    def format_plan(self, plan: Dict[str, Any]) -> str:
        """
        Format a plan as a human-readable string.
        
        Args:
            plan: The plan to format.
            
        Returns:
            A string representation of the plan.
        """
        # Basic implementation, can be overridden by subclasses
        if not plan:
            return "No plan available."
        
        output = []
        
        # Plan title and ID
        title = plan.get("title", "Untitled Plan")
        plan_id = plan.get("id", "unknown")
        output.append(f"Plan: {title} (ID: {plan_id})")
        output.append("=" * len(output[0]))
        output.append("")
        
        # Status summary
        total_steps = len(plan.get("steps", []))
        completed_steps = len(plan.get("completed_steps", []))
        remaining_steps = total_steps - completed_steps
        progress_pct = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        output.append(f"Progress: {completed_steps}/{total_steps} steps completed ({progress_pct:.1f}%)")
        output.append("")
        
        # Steps
        output.append("Steps:")
        steps = plan.get("steps", [])
        completed_step_ids = [step.get("id") for step in plan.get("completed_steps", [])]
        
        for i, step in enumerate(steps):
            step_id = step.get("id", f"step-{i+1}")
            description = step.get("description", "No description")
            
            # Determine status
            status = "✓" if step_id in completed_step_ids else " "
            
            output.append(f"  [{status}] {i+1}. {description}")
            
            # Add tool information if available
            tool = step.get("tool")
            if tool:
                output.append(f"      Tool: {tool}")
            
            # Add dependencies if available
            dependencies = step.get("dependencies", [])
            if dependencies:
                deps_str = ", ".join([f"Step {d}" for d in dependencies])
                output.append(f"      Dependencies: {deps_str}")
        
        # Add reasoning if available
        reasoning = plan.get("reasoning")
        if reasoning:
            output.append("")
            output.append("Planning Rationale:")
            output.append(f"  {reasoning}")
        
        return "\n".join(output)
    
    def validate_plan(self, plan: Dict[str, Any]) -> List[str]:
        """
        Validate a plan for common issues.
        
        Args:
            plan: The plan to validate.
            
        Returns:
            A list of validation errors, or an empty list if the plan is valid.
        """
        errors = []
        
        # Check required fields
        required_fields = ["id", "task", "steps"]
        for field in required_fields:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        # Check step structure
        steps = plan.get("steps", [])
        if not isinstance(steps, list):
            errors.append("Steps must be a list")
        else:
            # Check each step
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"Step {i+1} must be a dictionary")
                    continue
                
                # Check step required fields
                step_required = ["id", "description"]
                for field in step_required:
                    if field not in step:
                        errors.append(f"Step {i+1} missing required field: {field}")
                
                # Check dependencies
                dependencies = step.get("dependencies", [])
                if not isinstance(dependencies, list):
                    errors.append(f"Step {i+1} dependencies must be a list")
                else:
                    # Check if dependencies refer to existing steps
                    for dep in dependencies:
                        if not any(s.get("id") == dep for s in steps):
                            errors.append(f"Step {i+1} has dependency on non-existent step: {dep}")
                
                # Check for circular dependencies
                if self._has_circular_dependency(steps, step, []):
                    errors.append(f"Step {i+1} has circular dependency")
        
        return errors
    
    def _has_circular_dependency(self, steps: List[Dict[str, Any]], current_step: Dict[str, Any], visited: List[str]) -> bool:
        """
        Check if a step has circular dependencies.
        
        Args:
            steps: All steps in the plan.
            current_step: The current step to check.
            visited: List of already visited step IDs.
            
        Returns:
            True if there is a circular dependency, False otherwise.
        """
        step_id = current_step.get("id")
        
        # If we've already visited this step, we have a circular dependency
        if step_id in visited:
            return True
        
        # Add this step to visited
        visited = visited + [step_id]
        
        # Check each dependency
        dependencies = current_step.get("dependencies", [])
        for dep_id in dependencies:
            # Find the dependency step
            dep_step = next((s for s in steps if s.get("id") == dep_id), None)
            if dep_step:
                # Recursively check for circular dependencies
                if self._has_circular_dependency(steps, dep_step, visited):
                    return True
        
        return False
