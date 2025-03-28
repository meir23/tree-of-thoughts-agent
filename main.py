#!/usr/bin/env python

"""
Tree-of-Thoughts Agent (ToTA) - Main Script

This script provides the entry point for running the ToTA agent from the command line.
It parses command-line arguments, initializes components, and runs the agent.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from tota_core.configuration import load_config
from tota_core.control_flow_manager import ControlFlowManager
from tota_core.llm_interaction import LLMInteraction
from tota_core.tree_manager import TreeManager
from tota_core.function_implementations import FunctionImplementations


# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('tota_agent')


def run_tota_agent(task_description, config_path='config.yaml'):
    """
    Run the ToTA agent with the given task and configuration.
    
    Args:
        task_description: Description of the task to solve
        config_path: Path to the configuration file
        
    Returns:
        Tuple of (status, solution_path, log_file_path)
    """
    # Load environment variables (.env file)
    load_dotenv()
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize components
    function_implementations = FunctionImplementations(config)
    llm_interaction = LLMInteraction(config)
    tree_manager = TreeManager()
    
    # Initialize Control Flow Manager
    cfm = ControlFlowManager(
        config=config,
        llm_interaction=llm_interaction,
        tree_manager=tree_manager,
        function_implementations=function_implementations
    )
    
    # Run the agent
    try:
        status, solution_path, log_file = cfm.run_agent(task_description)
        logger.info(f"Agent completed with status: {status}")
        logger.info(f"Log file: {log_file}")
        return status, solution_path, log_file
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return "Error", None, None


def main():
    """
    Main entry point for command-line execution.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Tree-of-Thoughts Agent (ToTA)')
    parser.add_argument('--task', type=str, required=True, help='Task description')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    # Check for API key
    if 'ANTHROPIC_API_KEY' not in os.environ and 'OPENAI_API_KEY' not in os.environ:
        logger.error("No API key found in environment variables.")
        logger.error("Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file.")
        sys.exit(1)
    
    # Run the agent
    status, solution_path, log_file = run_tota_agent(args.task, args.config)
    
    # Print output
    print("\nAgent completed")
    print(f"Status: {status}")
    print(f"Log file: {log_file}")
    if solution_path:
        print(f"\nSolution path:\n{solution_path}")


if __name__ == "__main__":
    main()
