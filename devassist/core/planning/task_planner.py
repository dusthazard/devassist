"""
Task Planner module for LLM-based development task planning.

This module provides concrete implementation of the BasePlanner interface
using language models to create and manage development task plans.
"""

import uuid
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union

from devassist.core.planning.base_planner import BasePlanner
from devassist.models.base.base_model import BaseModel

class TaskPlanner(BasePlanner):
    """
    A planner that uses language models to create and manage development task plans.
    
    Implements task breakdown for software development, dependency tracking, 
    and adaptive replanning based on execution feedback.
    
    Features:
    - Intelligent breakdown of development tasks
    - Technology-specific planning
    - Dependency tracking between steps
    - Adaptive replanning based on execution results
    - Development-specific step categorization (frontend, backend, database, etc.)
    """
    
    def __init__(self, model: BaseModel, **kwargs):
        """
        Initialize a TaskPlanner instance.
        
        Args:
            model: The language model to use for planning.
            **kwargs: Additional configuration options for the planner.
        """
        super().__init__(**kwargs)
        self.model = model
        self.max_steps = kwargs.get("max_steps", 15)
        self.development_domains = kwargs.get("development_domains", [
            "frontend", "backend", "database", "testing", "deployment", 
            "infrastructure", "security", "documentation"
        ])
        
        # Technology-specific planning templates
        self.tech_templates = kwargs.get("tech_templates", {})
        
        # Default technology template
        self.default_template = """
        You are a development planning assistant. Break down development tasks into logical steps.
        When creating a plan, consider:
        1. Dependencies between steps
        2. Appropriate tools for each step
        3. Required knowledge or resources
        4. Testing and validation
        5. Clear, actionable descriptions
        
        Create a plan that would enable a developer to implement: {task}
        
        The plan should include:
        - A clear and logical sequence of steps
        - Tool suggestions for each step when applicable
        - Dependencies between steps
        - A brief rationale for your planning approach
        """
    
    def create_plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a plan for executing a development task using the language model.
        
        Args:
            task: The task description.
            context: Optional context for planning, including:
                    - project: Project name or identifier
                    - technology: Technology stack information
                    - constraints: Any constraints or requirements
                    - existing_code: Information about existing codebase
                    - user_level: Developer experience level
            
        Returns:
            A plan dictionary with steps and metadata.
        """
        context = context or {}
        
        # Choose the appropriate planning template based on context
        prompt = self._create_planning_prompt(task, context)
        
        # Extract JSON schema for the plan
        plan_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "domain": {"type": "string"},
                            "tool": {"type": "string"},
                            "tool_input": {"type": "object"},
                            "expected_output": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "estimated_time": {"type": "string"}
                        },
                        "required": ["description", "domain"]
                    }
                },
                "reasoning": {"type": "string"},
                "estimated_steps": {"type": "integer"}
            },
            "required": ["title", "steps", "reasoning"]
        }
        
        # Generate the plan using the model
        try:
            plan_data = self.model.extract_json(
                prompt=prompt,
                schema=plan_schema,
                system_message="You are a software development planning assistant. Break down development tasks into logical steps."
            )
            
            # Process the plan data
            return self._process_plan_data(task, plan_data, context)
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            # Return a minimal plan
            return {
                "id": str(uuid.uuid4()),
                "task": task,
                "title": f"Plan for: {task}",
                "status": "error",
                "error": str(e),
                "created_at": time.time(),
                "steps": [],
                "reasoning": "Error generating plan",
                "current_step_index": 0,
                "completed_steps": [],
                "metadata": {
                    "context": context,
                    "error_details": str(e)
                }
            }
    
    def replan(self, plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a plan based on execution feedback.
        
        Args:
            plan: The current plan.
            feedback: Feedback from execution, which may include:
                     - step_id: ID of the step that generated the feedback
                     - status: Success or failure status
                     - error: Error message if status is failure
                     - result: Result data if status is success
                     - new_requirements: Any new requirements discovered
            
        Returns:
            The updated plan.
        """
        # Extract current plan state
        task = plan.get("task", "")
        completed_steps = plan.get("completed_steps", [])
        remaining_steps = self._get_remaining_steps(plan)
        
        # Prepare the replanning prompt
        prompt = self._create_replanning_prompt(task, plan, feedback)
        
        # Extract JSON schema for the updated plan
        plan_schema = {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "domain": {"type": "string"},
                            "tool": {"type": "string"},
                            "tool_input": {"type": "object"},
                            "expected_output": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "estimated_time": {"type": "string"}
                        },
                        "required": ["description", "domain"]
                    }
                },
                "reasoning": {"type": "string"}
            },
            "required": ["steps", "reasoning"]
        }
        
        try:
            # Generate the updated plan
            updated_plan_data = self.model.extract_json(
                prompt=prompt,
                schema=plan_schema,
                system_message="You are a software development planning assistant. Revise development plans based on execution feedback."
            )
            
            # Merge the updated plan with the original plan
            updated_plan = plan.copy()
            
            # Keep the completed steps
            updated_plan["steps"] = completed_steps + updated_plan_data.get("steps", [])
            updated_plan["reasoning"] = updated_plan_data.get("reasoning", "Plan updated based on feedback")
            updated_plan["updated_at"] = time.time()
            updated_plan["status"] = "updated"
            
            # Keep the current step index
            if len(completed_steps) < len(updated_plan["steps"]):
                updated_plan["current_step_index"] = len(completed_steps)
            else:
                updated_plan["current_step_index"] = 0
            
            # Add feedback to metadata
            if "metadata" not in updated_plan:
                updated_plan["metadata"] = {}
            updated_plan["metadata"]["feedback_history"] = updated_plan["metadata"].get("feedback_history", [])
            updated_plan["metadata"]["feedback_history"].append(feedback)
            
            # Validate the updated plan
            errors = self.validate_plan(updated_plan)
            if errors:
                self.logger.warning(f"Validation errors in updated plan: {errors}")
                updated_plan["metadata"]["validation_errors"] = errors
            
            return updated_plan
            
        except Exception as e:
            self.logger.error(f"Error replanning: {e}")
            # Return the original plan with an error flag
            plan["status"] = "error"
            plan["error"] = str(e)
            if "metadata" not in plan:
                plan["metadata"] = {}
            plan["metadata"]["replan_error"] = str(e)
            return plan
    
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
        steps = plan.get("steps", [])
        current_index = plan.get("current_step_index", 0)
        
        # Check if we've completed all steps
        if current_index >= len(steps):
            return None
        
        # Get the next step
        next_step = steps[current_index]
        
        # Check dependencies
        if "dependencies" in next_step and next_step["dependencies"]:
            completed_step_ids = [step.get("id") for step in plan.get("completed_steps", [])]
            
            # Check if all dependencies are satisfied
            for dep_id in next_step["dependencies"]:
                if dep_id not in completed_step_ids:
                    # Dependency not satisfied, try to find an alternative step
                    alt_step = self._find_executable_step(plan)
                    if alt_step:
                        return alt_step
                    else:
                        # Can't proceed, need replanning
                        self.logger.warning(f"Can't execute step {next_step.get('id')}: unsatisfied dependencies")
                        return None
        
        return next_step
    
    def mark_step_complete(self, plan: Dict[str, Any], step_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark a step as complete in a plan.
        
        Args:
            plan: The current plan.
            step_id: The ID of the completed step.
            result: The result of the step execution, which may include:
                   - status: Success or failure status
                   - output: Output data (code, documentation, etc.)
                   - files_created: List of files created
                   - files_modified: List of files modified
                   - execution_time: Time taken to execute the step
            
        Returns:
            The updated plan.
        """
        updated_plan = plan.copy()
        steps = updated_plan.get("steps", [])
        current_index = updated_plan.get("current_step_index", 0)
        
        # Find the step
        step_index = -1
        for i, step in enumerate(steps):
            if step.get("id") == step_id:
                step_index = i
                break
        
        if step_index == -1:
            self.logger.warning(f"Step {step_id} not found in plan")
            return plan
        
        # Update the step with result
        completed_step = steps[step_index].copy()
        completed_step["result"] = result
        completed_step["completed_at"] = time.time()
        
        # Extract artifacts if any
        if "output" in result:
            artifacts = self._extract_artifacts(result["output"])
            if artifacts:
                completed_step["artifacts"] = artifacts
        
        # Add to completed steps
        if "completed_steps" not in updated_plan:
            updated_plan["completed_steps"] = []
        updated_plan["completed_steps"].append(completed_step)
        
        # Update current step index
        if step_index == current_index:
            updated_plan["current_step_index"] = current_index + 1
        
        # Check if plan is complete
        if updated_plan["current_step_index"] >= len(steps):
            updated_plan["status"] = "completed"
            updated_plan["completed_at"] = time.time()
        
        return updated_plan
    
    def _create_planning_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """
        Create a prompt for generating a development plan.
        
        Args:
            task: The task description.
            context: Context information.
            
        Returns:
            A prompt string.
        """
        # Extract relevant context information
        project = context.get("project", "Unknown Project")
        technology = context.get("technology", {})
        constraints = context.get("constraints", [])
        existing_code = context.get("existing_code", {})
        user_level = context.get("user_level", "intermediate")
        
        # Choose appropriate template based on technology
        tech_stack = technology.get("stack", "")
        template = self.default_template
        
        # If we have a technology-specific template, use it
        if tech_stack in self.tech_templates:
            template = self.tech_templates[tech_stack]
        
        # Format the template
        base_prompt = template.format(task=task)
        
        # Add context information
        prompt = f"""
{base_prompt}

Project: {project}

Technology Information:
{json.dumps(technology, indent=2)}

Constraints:
{json.dumps(constraints, indent=2) if constraints else "No specific constraints."}

Existing Code Structure:
{json.dumps(existing_code, indent=2) if existing_code else "No existing code structure provided."}

Developer Experience Level:
{user_level}

Please provide a structured plan with no more than {self.max_steps} steps.
Each step should include a domain category from: {', '.join(self.development_domains)}
"""
        return prompt
    
    def _create_replanning_prompt(self, task: str, plan: Dict[str, Any], feedback: Dict[str, Any]) -> str:
        """
        Create a prompt for replanning.
        
        Args:
            task: The task description.
            plan: The current plan.
            feedback: Feedback from execution.
            
        Returns:
            A prompt string.
        """
        # Extract completed steps
        completed_steps = plan.get("completed_steps", [])
        completed_steps_text = ""
        for i, step in enumerate(completed_steps):
            result = step.get("result", {})
            status = result.get("status", "unknown")
            summary = result.get("summary", "No summary provided")
            
            completed_steps_text += f"{i+1}. {step.get('description', 'Step')}: {status} - {summary}\n"
        
        # Extract remaining steps
        remaining_steps = self._get_remaining_steps(plan)
        remaining_steps_text = ""
        for i, step in enumerate(remaining_steps):
            remaining_steps_text += f"{i+1}. {step.get('description', 'Step')} (Domain: {step.get('domain', 'unknown')})\n"
        
        # Extract feedback details
        feedback_step_id = feedback.get("step_id", "unknown")
        feedback_status = feedback.get("status", "unknown")
        feedback_error = feedback.get("error", "No error")
        feedback_result = feedback.get("result", {})
        
        # Construct new requirements if any
        new_requirements = feedback.get("new_requirements", [])
        new_requirements_text = "\n".join([f"- {req}" for req in new_requirements]) if new_requirements else "None"
        
        prompt = f"""
Task: {task}

I need to revise my development plan based on execution feedback. 

Completed steps:
{completed_steps_text if completed_steps_text else "No steps completed yet."}

Current feedback:
- Step ID: {feedback_step_id}
- Status: {feedback_status}
{"- Error: " + feedback_error if feedback_status == "failure" else ""}
- Details: {json.dumps(feedback_result, indent=2)}

New requirements:
{new_requirements_text}

Current remaining steps:
{remaining_steps_text if remaining_steps_text else "No remaining steps."}

Please provide an updated plan for the remaining steps, considering the feedback and results from completed steps.
Ensure your updated plan addresses any errors and incorporates new requirements.

Each step should include a domain category from: {', '.join(self.development_domains)}
"""
        return prompt
    
    def _process_plan_data(self, task: str, plan_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw plan data into a structured plan.
        
        Args:
            task: The task description.
            plan_data: Raw plan data from the model.
            context: Context used for planning.
            
        Returns:
            A structured plan dictionary.
        """
        # Get the title if available, otherwise generate one
        title = plan_data.get("title", f"Plan for: {task[:50]}...")
        
        steps = plan_data.get("steps", [])
        
        # Ensure each step has an ID and required fields
        for i, step in enumerate(steps):
            if "id" not in step:
                step["id"] = f"step-{i+1}-{str(uuid.uuid4())[:8]}"
            
            if "tool_input" not in step and "tool" in step:
                step["tool_input"] = {}
            
            if "dependencies" not in step:
                step["dependencies"] = []
                
            # Ensure the domain is valid
            if "domain" in step and step["domain"] not in self.development_domains:
                # Find the closest domain or default to "other"
                closest = self._find_closest_domain(step["domain"])
                self.logger.warning(f"Invalid domain: {step['domain']}, using {closest}")
                step["domain"] = closest
        
        # Create the plan structure
        plan = {
            "id": str(uuid.uuid4()),
            "task": task,
            "title": title,
            "status": "created",
            "created_at": time.time(),
            "steps": steps,
            "reasoning": plan_data.get("reasoning", ""),
            "current_step_index": 0,
            "completed_steps": [],
            "metadata": {
                "context": context,
                "estimated_steps": plan_data.get("estimated_steps", len(steps))
            }
        }
        
        # Validate the plan
        errors = self.validate_plan(plan)
        if errors:
            self.logger.warning(f"Validation errors in created plan: {errors}")
            plan["metadata"]["validation_errors"] = errors
        
        return plan
    
    def _get_remaining_steps(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get the remaining steps from a plan.
        
        Args:
            plan: The current plan.
            
        Returns:
            A list of remaining steps.
        """
        steps = plan.get("steps", [])
        current_index = plan.get("current_step_index", 0)
        
        if current_index >= len(steps):
            return []
        
        return steps[current_index:]
    
    def _find_executable_step(self, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a step that can be executed (all dependencies satisfied).
        
        Args:
            plan: The current plan.
            
        Returns:
            An executable step, or None if none found.
        """
        steps = plan.get("steps", [])
        current_index = plan.get("current_step_index", 0)
        completed_step_ids = [step.get("id") for step in plan.get("completed_steps", [])]
        
        # Look for steps after the current index
        for i in range(current_index, len(steps)):
            step = steps[i]
            dependencies = step.get("dependencies", [])
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = True
            for dep_id in dependencies:
                if dep_id not in completed_step_ids:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                return step
        
        return None
    
    def _extract_artifacts(self, output: str) -> List[Dict[str, Any]]:
        """
        Extract artifacts from step output.
        
        Args:
            output: The step output text.
            
        Returns:
            A list of extracted artifacts.
        """
        artifacts = []
        
        # Look for file creation patterns
        file_patterns = [
            # Code files
            r'```(\w+)\s+(?:// File: ([\w\.\-\/]+))?\s*([\s\S]+?)```',
            # Markdown/text files with explicit file marker
            r'```\s+File: ([\w\.\-\/]+)\s+([\s\S]+?)```',
            # Named code blocks
            r'```(\w+):(\S+)\s*([\s\S]+?)```'
        ]
        
        for pattern in file_patterns:
            import re
            matches = re.finditer(pattern, output)
            
            for match in matches:
                if len(match.groups()) == 3:
                    # First pattern
                    language, filename, content = match.groups()
                    if not filename:
                        # Generate a filename based on language
                        ext = self._language_to_extension(language)
                        filename = f"generated_file_{len(artifacts) + 1}{ext}"
                elif len(match.groups()) == 2:
                    # Second pattern
                    filename, content = match.groups()
                    language = self._filename_to_language(filename)
                else:
                    # Third pattern
                    language, name, content = match.groups()
                    # Generate a filename based on language and name
                    ext = self._language_to_extension(language)
                    filename = f"{name}{ext}"
                
                artifacts.append({
                    "type": "file",
                    "filename": filename,
                    "language": language,
                    "content": content.strip()
                })
        
        return artifacts
    
    def _language_to_extension(self, language: str) -> str:
        """
        Convert a language name to a file extension.
        
        Args:
            language: The language name.
            
        Returns:
            The file extension.
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "php": ".php",
            "ruby": ".rb",
            "go": ".go",
            "rust": ".rs",
            "swift": ".swift",
            "kotlin": ".kt",
            "markdown": ".md",
            "json": ".json",
            "yaml": ".yml",
            "xml": ".xml",
            "sql": ".sql",
            "sh": ".sh",
            "bash": ".sh",
            "plaintext": ".txt",
            "text": ".txt"
        }
        
        return extensions.get(language.lower(), ".txt")
    
    def _filename_to_language(self, filename: str) -> str:
        """
        Guess the language from a filename.
        
        Args:
            filename: The filename.
            
        Returns:
            The language name.
        """
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".md": "markdown",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".xml": "xml",
            ".sql": "sql",
            ".sh": "bash",
            ".txt": "plaintext"
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return extensions.get(ext, "plaintext")
    
    def _find_closest_domain(self, domain: str) -> str:
        """
        Find the closest valid domain for an invalid domain name.
        
        Args:
            domain: The domain name to check.
            
        Returns:
            The closest valid domain name.
        """
        domain = domain.lower()
        
        # Direct mapping of invalid domains to valid ones
        domain_mapping = {
            "front-end": "frontend",
            "front": "frontend",
            "ui": "frontend",
            "interface": "frontend",
            "back-end": "backend",
            "back": "backend",
            "server": "backend",
            "db": "database",
            "data": "database",
            "test": "testing",
            "qa": "testing",
            "quality assurance": "testing",
            "deploy": "deployment",
            "infra": "infrastructure",
            "devops": "infrastructure",
            "secure": "security",
            "docs": "documentation",
            "doc": "documentation"
        }
        
        # Check direct mapping
        if domain in domain_mapping:
            return domain_mapping[domain]
        
        # Check if it's a valid domain
        if domain in [d.lower() for d in self.development_domains]:
            return domain
            
        # Find the closest match
        import difflib
        matches = difflib.get_close_matches(domain, self.development_domains, n=1, cutoff=0.6)
        if matches:
            return matches[0]
        
        # Default to "other" if available, or the first domain
        if "other" in self.development_domains:
            return "other"
        
        return self.development_domains[0]
