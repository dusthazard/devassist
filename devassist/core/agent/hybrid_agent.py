"""
Hybrid Agent module that combines single and multi-agent capabilities.

This agent can dynamically switch between single and multi-agent modes based on task complexity.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional

from devassist.core.agent.tool_agent import ToolAgent

class HybridAgent(ToolAgent):
    """
    A hybrid agent that can switch between single and multi-agent modes.
    
    This agent assesses task complexity and chooses the appropriate mode.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        max_iterations: int = 10,
        tools: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a HybridAgent instance.
        
        Args:
            name: Optional name for the agent.
            max_iterations: Maximum number of thought-action cycles to perform.
            tools: Optional list of tool names to load.
            **kwargs: Additional configuration options for the agent.
        """
        super().__init__(name=name, max_iterations=max_iterations, tools=tools, **kwargs)
        self.mode = kwargs.get("mode", "auto")
        self.complexity_threshold = kwargs.get("complexity_threshold", 7.0)
        
        # Specialized agents for multi-agent mode
        self.specialized_agents = {}
        
        logging.info(f"Hybrid agent '{self.name}' initialized in {self.mode} mode with complexity threshold {self.complexity_threshold}")
    
    def execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task using the appropriate mode based on complexity.
        
        Args:
            task: The task description to execute.
            **kwargs: Additional parameters for task execution.
            
        Returns:
            A dictionary containing the execution result and metadata.
        """
        # If mode is explicitly specified in kwargs, use that
        mode = kwargs.get("mode", self.mode)
        
        if mode == "auto":
            # Assess task complexity to determine mode
            complexity = self._assess_complexity(task)
            logging.info(f"Task complexity assessed as {complexity:.1f}/10.0 (threshold: {self.complexity_threshold})")
            
            if complexity < self.complexity_threshold:
                logging.info(f"Task complexity ({complexity:.1f}) below threshold ({self.complexity_threshold}). Using single-agent mode.")
                return super().execute(task, **kwargs)
            else:
                logging.info(f"Task complexity ({complexity:.1f}) above threshold ({self.complexity_threshold}). Using multi-agent mode.")
                return self._execute_multi_agent(task, **kwargs)
        elif mode == "multi":
            logging.info("Using multi-agent mode as explicitly specified.")
            return self._execute_multi_agent(task, **kwargs)
        else:  # single mode
            logging.info("Using single-agent mode as explicitly specified.")
            return super().execute(task, **kwargs)
    
    def _assess_complexity(self, task: str) -> float:
        """
        Assess the complexity of a task.
        
        Args:
            task: The task description.
            
        Returns:
            A complexity score between 0 and 10.
        """
        complexity = 0.0
        
        # Check for multiple operations
        operations = [
            (r'(calculate|compute|evaluate)', 1.0),  # Basic calculations
            (r'(search|find|look up)', 1.0),  # Search operations
            (r'(count|process|analyze|transform)\s+text', 1.0),  # Text operations
            (r'run\s+code|execute', 1.5),  # Code execution
            (r'compare|contrast|evaluate', 2.0),  # Analysis operations
            (r'optimize|improve|enhance', 2.5),  # Optimization tasks
            (r'and|then|after|before', 1.0),  # Task chaining
            (r'if|when|unless|otherwise', 1.5),  # Conditional operations
            (r'all|every|each', 1.0),  # Comprehensive operations
            (r'most|best|optimal', 1.5),  # Decision making
            (r'create\s+(api|endpoint|component|class|model)', 2.0),  # Creation tasks
            (r'generate\s+(api|endpoint|component|class|model)', 2.0),  # Generation tasks
            (r'design|architect', 3.0),  # Design tasks
            (r'debug|troubleshoot|fix', 2.5),  # Debugging tasks
            (r'full\s+stack|end-to-end|complete', 3.0),  # Full-stack tasks
            (r'database|storage|persistence', 2.0),  # Database tasks
            (r'authentication|security|encryption', 2.5),  # Security tasks
            (r'deploy|release|publish', 2.0),  # Deployment tasks
            (r'test|validate|verify', 1.5),  # Testing tasks
            (r'front-?end|back-?end|ui|ux', 1.5),  # Specific development areas
        ]
        
        # Add complexity for each operation found
        for pattern, score in operations:
            matches = re.findall(pattern, task.lower())
            complexity += score * len(matches)
        
        # Add complexity for length of task description
        words = task.split()
        complexity += len(words) * 0.1  # 0.1 points per word
        
        # Add complexity for special characters (potential complex expressions)
        special_chars = sum(1 for c in task if not c.isalnum() and not c.isspace())
        complexity += special_chars * 0.05
        
        # Add complexity for multiple tools needed
        tool_keywords = {
            'calculator': ['calculate', 'compute', 'evaluate', 'math'],
            'search': ['search', 'find', 'look up', 'query'],
            'text': ['text', 'string', 'characters', 'words'],
            'code': ['code', 'execute', 'run', 'python'],
            'react_component': ['react', 'component', 'ui', 'frontend'],
            'api_endpoint': ['api', 'endpoint', 'backend', 'rest'],
            'database_model': ['database', 'model', 'schema', 'orm']
        }
        
        tools_needed = 0
        task_lower = task.lower()
        for tool_name, keywords in tool_keywords.items():
            if any(kw in task_lower for kw in keywords):
                tools_needed += 1
            
        complexity += tools_needed * 1.5
        
        # Cap the complexity at 10
        return min(10.0, complexity)
    
    def _execute_multi_agent(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task using multiple specialized agents.
        
        Args:
            task: The task description to execute.
            **kwargs: Additional parameters for task execution.
            
        Returns:
            A dictionary containing the aggregated results.
        """
        logging.info("Task decomposed into subtasks for optimal multi-agent execution")
        
        # Ensure we have specialized agents
        self._ensure_specialized_agents()
        
        # For simple calculator tasks, use direct execution
        if task.lower().startswith("calculate"):
            # Use the ToolAgent's _decide_action method to determine the action
            action_name, action_input = self._decide_action({"task": task})
            
            # If it's a calculator action, execute it directly
            if action_name == "calculator" and "expression" in action_input:
                result = self._execute_action(action_name, action_input)
                if result.get("status") == "success" and "result" in result:
                    return {
                        "task": task,
                        "answer": f"The result of {action_input['expression']} is {result['result']}",
                        "direct_result": result,
                        "mode": "direct"
                    }
        
        # For complex tasks, use multi-agent approach
        results = {}
        final_result = None
        
        # Researcher analyzes the task and gathers information
        researcher_result = self.specialized_agents["researcher"].execute(
            f"Analyze and gather information for: {task}"
        )
        results["researcher"] = researcher_result
        logging.info("Researcher agent completed information gathering")
        
        # Planner creates a strategy based on research
        planner_result = self.specialized_agents["planner"].execute(
            f"Plan execution strategy for: {task}\nBased on research: {researcher_result['answer']}"
        )
        results["planner"] = planner_result
        logging.info("Planner agent completed strategy development")
        
        # Executor carries out the plan
        executor_result = self.specialized_agents["executor"].execute(
            f"Execute plan for: {task}\nFollowing strategy: {planner_result['answer']}"
        )
        results["executor"] = executor_result
        final_result = executor_result  # Use executor's result as the primary result
        logging.info("Executor agent completed plan execution")
        
        # Critic evaluates the results
        critic_result = self.specialized_agents["critic"].execute(
            f"Evaluate results for: {task}\nAnalyzing output: {executor_result['answer']}"
        )
        results["critic"] = critic_result
        logging.info("Critic agent completed result evaluation")
        
        logging.info("All specialized agents have completed their tasks. Aggregating results...")
        
        return {
            "task": task,
            "answer": final_result.get("answer", str(final_result)),
            "agent_results": results,
            "mode": "multi"
        }
    
    def _ensure_specialized_agents(self) -> None:
        """
        Create specialized agents if they don't already exist.
        """
        if not self.specialized_agents:
            logging.info("Creating specialized agents for multi-agent execution")
            
            required_roles = ["researcher", "planner", "executor", "critic"]
            
            for role in required_roles:
                if role not in self.specialized_agents:
                    # Copy tools from the primary agent
                    agent = ToolAgent(
                        name=f"{role}-agent",
                        max_iterations=self.max_iterations,
                        tools=list(self.tools.keys())  # Use the same tools as the primary agent
                    )
                    
                    self.specialized_agents[role] = agent
                    logging.info(f"Created specialized agent for role: {role}")
            
            logging.info(f"All specialized agents created: {', '.join(self.specialized_agents.keys())}")
    
    def add_specialized_agent(self, role: str, config: Dict[str, Any]) -> None:
        """
        Add a specialized agent for a specific role.
        
        Args:
            role: The role of the agent.
            config: Configuration for the agent.
        """
        # Create a new ToolAgent with the given configuration
        agent = ToolAgent(
            name=config.get("name", f"{role}-agent"),
            max_iterations=config.get("max_iterations", self.max_iterations),
            tools=config.get("tools", list(self.tools.keys()))
        )
        
        self.specialized_agents[role] = agent
        logging.info(f"Added specialized agent for role: {role}")
    
    def get_specialized_agent(self, role: str) -> Optional[ToolAgent]:
        """
        Get a specialized agent by role.
        
        Args:
            role: The role of the agent.
            
        Returns:
            The agent for the given role, or None if not found.
        """
        return self.specialized_agents.get(role)