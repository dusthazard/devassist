"""
Command-line interface for the DevAssist framework.
"""

import os
import sys
import time
import json
import logging
import cmd
import shutil
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from devassist.core.orchestrator import AgentOrchestrator

class CLI(cmd.Cmd):
    """
    Command-line interface for interacting with the DevAssist framework.
    
    Provides commands for:
    - Executing tasks
    - Managing agents
    - Viewing task history
    - Configuration
    """
    
    intro = "Welcome to the DevAssist framework. Type help or ? to list commands."
    prompt = "devassist> "
    
    def __init__(self, verbose: bool = False, config_path: str = "config.yaml"):
        """
        Initialize a CLI instance.
        
        Args:
            verbose: Whether to enable verbose output.
            config_path: Path to the configuration file.
        """
        super().__init__()
        self.verbose = verbose
        self.config_path = config_path
        self.orchestrator = None
        self.current_result = None
        self.history = []
        
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def display_welcome(self) -> None:
        """
        Display a welcome message.
        """
        term_width = shutil.get_terminal_size().columns
        
        print("=" * term_width)
        print("DevAssist - Development Assistant".center(term_width))
        print("=" * term_width)
        print("Your AI-powered development companion".center(term_width))
        print("=" * term_width)
        print("Type 'help' or '?' to list available commands.".center(term_width))
        print("=" * term_width)
        print()
    
    def start_interactive_mode(self, orchestrator: Optional[AgentOrchestrator] = None) -> None:
        """
        Start the interactive command-line interface.
        
        Args:
            orchestrator: Optional orchestrator instance. If not provided, one will be created.
        """
        if orchestrator:
            self.orchestrator = orchestrator
        else:
            self.orchestrator = AgentOrchestrator(config_path=self.config_path)
        
        # Display welcome message if not in stdin mode
        if sys.stdin.isatty():
            self.display_welcome()
        
        # Start the command loop
        self.cmdloop()
    
    def display_result(self, result: Dict[str, Any]) -> None:
        """
        Display the result of a task execution.
        
        Args:
            result: The task execution result.
        """
        self.current_result = result
        
        term_width = shutil.get_terminal_size().columns
        
        print("\n" + "=" * term_width)
        print("TASK RESULT".center(term_width))
        print("=" * term_width)
        
        # Display the task
        task = result.get("task", "Unknown task")
        print(f"Task: {task}")
        
        # Display the answer
        answer = result.get("answer", "No answer provided")
        print("\nAnswer:")
        print(f"{answer}")
        
        # Display additional information if verbose
        if self.verbose:
            print("\nExecution Details:")
            
            # Mode
            mode = result.get("mode", "single")
            print(f"Mode: {mode}")
            
            # Steps or iterations
            if "iterations" in result:
                iterations = result.get("iterations", 0)
                print(f"Iterations: {iterations}")
            elif "steps" in result:
                steps = len(result.get("steps", []))
                completed_steps = len(result.get("completed_steps", []))
                print(f"Steps: {completed_steps}/{steps} completed")
            
            # Display context or not based on verbosity
            if self.verbose and "context" in result:
                print("\nExecution Context:")
                self._pretty_print(result["context"])
        
        print("=" * term_width)
    
    def do_task(self, arg: str) -> None:
        """
        Execute a task.
        
        Usage: task [mode] <task description>
        
        Args:
            arg: Task description and optional mode.
        """
        # Make sure orchestrator is initialized
        if not self.orchestrator:
            self.orchestrator = AgentOrchestrator(config_path=self.config_path)
        
        # Parse arguments
        parts = arg.strip().split(maxsplit=1)
        
        if len(parts) == 0 or not arg.strip():
            print("Error: Please provide a task description.")
            print("DevAssist needs a task to work on.")
            return
        
        # Check if mode is specified
        mode = None
        task = arg.strip()
        
        if len(parts) > 1 and parts[0] in ["single", "multi", "auto"]:
            mode = parts[0]
            task = parts[1]
        
        # Execute the task
        print(f"Executing task: {task}")
        if mode:
            print(f"Mode: {mode}")
        
        if mode == "multi":
            print("Multiple agents engaged for collaborative execution...")
        
        try:
            result = self.orchestrator.execute_task(task, mode=mode)
            self.display_result(result)
            
            # Add to history
            self.history.append({
                "timestamp": time.time(),
                "task": task,
                "mode": mode,
                "result": result
            })
            
        except Exception as e:
            print(f"Error executing task: {e}")
            print("Please try again with a different task.")
    
    def do_agents(self, arg: str) -> None:
        """
        List available agents.
        
        Usage: agents
        """
        # Make sure orchestrator is initialized
        if not self.orchestrator:
            self.orchestrator = AgentOrchestrator(config_path=self.config_path)
        
        agents = self.orchestrator.list_agents()
        
        if not agents:
            print("No agents available.")
            print("Please initialize agents first.")
            return
        
        print("Available Agents:")
        print("-" * 40)
        
        for agent in agents:
            primary = agent.get("primary", False)
            prefix = "* " if primary else "  "
            print(f"{prefix}{agent.get('name', 'Unknown')} ({agent.get('type', 'Unknown')})")
            
            if self.verbose:
                print(f"   ID: {agent.get('id', 'Unknown')}")
            
            print()
            
        print(f"Total agents: {len(agents)}")
    
    def do_history(self, arg: str) -> None:
        """
        Show task execution history.
        
        Usage: history [limit]
        
        Args:
            arg: Optional limit on the number of history items to display.
        """
        # Parse arguments
        limit = 5
        if arg and arg.strip().isdigit():
            limit = int(arg.strip())
        
        # Get history from orchestrator if available
        if self.orchestrator:
            history = self.orchestrator.get_task_history(limit=limit)
        else:
            history = self.history[-limit:] if self.history else []
        
        if not history:
            print("No task history available.")
            print("Execute some tasks first to build history.")
            return
        
        print("Task History:")
        print("-" * 60)
        
        for i, entry in enumerate(reversed(history)):
            timestamp = entry.get("start_time", entry.get("timestamp", 0))
            dt = datetime.fromtimestamp(timestamp)
            task = entry.get("task", "Unknown task")
            mode = entry.get("mode", "single")
            status = entry.get("status", "completed")
            
            print(f"{i+1}. [{dt.strftime('%Y-%m-%d %H:%M:%S')}] ({mode}) {status}")
            print(f"   Task: {task}")
            
            # Show result summary if available
            if "result" in entry and "answer" in entry["result"]:
                answer = entry["result"]["answer"]
                summary = answer[:100] + "..." if len(answer) > 100 else answer
                print(f"   Answer: {summary}")
            
            print()
        
        print(f"Showing {min(len(history), limit)} of {len(history)} total entries.")
    
    def do_config(self, arg: str) -> None:
        """
        Show current configuration.
        
        Usage: config
        """
        # Make sure orchestrator is initialized
        if not self.orchestrator:
            self.orchestrator = AgentOrchestrator(config_path=self.config_path)
        
        print(f"Configuration file: {self.config_path}")
        print("-" * 60)
        
        self._pretty_print(self.orchestrator.config)
        print("\nA well-configured system performs better.")
    
    def do_exit(self, arg: str) -> bool:
        """
        Exit the application.
        
        Usage: exit
        """
        print("Exiting DevAssist. Thank you for using our service.")
        return True
    
    def do_quit(self, arg: str) -> bool:
        """
        Exit the application.
        
        Usage: quit
        """
        return self.do_exit(arg)
    
    def do_EOF(self, arg: str) -> bool:
        """
        Handle EOF (Ctrl+D).
        """
        print()  # Add a newline
        return self.do_exit(arg)
    
    def emptyline(self) -> None:
        """
        Handle empty lines in the CLI.
        """
        # Do nothing on empty line
        pass
    
    def _pretty_print(self, data: Any) -> None:
        """
        Pretty print data.
        
        Args:
            data: Data to print.
        """
        if isinstance(data, (dict, list)):
            try:
                print(json.dumps(data, indent=2))
            except Exception:
                print(data)
        else:
            print(data)