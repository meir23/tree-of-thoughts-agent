"""
Function Implementations module for the ToTA agent.

This module is responsible for implementing functions that can be called by the LLM.
Currently, this includes the log_node_details function for logging node information.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional


class FunctionImplementations:
    """
    Implementation of functions callable by the LLM.
    
    This class contains the actual Python logic for functions that the LLM can call,
    particularly the logging function that records node details in a Markdown file.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the FunctionImplementations object.
        
        Args:
            config: Dictionary containing configuration parameters.
        """
        self.config = config
        self.log_file_path = self._generate_log_file_path()
    
    def _generate_log_file_path(self) -> str:
        """
        Generate a log file path using the template from config.
        
        Returns:
            Full path to the log file.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        template = self.config.get("log_file_path_template", "logs/tota_run_{timestamp}.md")
        log_path = template.replace("{timestamp}", timestamp)
        
        # Ensure the directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        return log_path
    
    def initialize_log_file(self, task_description: str, config_dict: Dict[str, Any]) -> None:
        """
        Initialize the log file with header information.
        
        Args:
            task_description: Description of the overall task.
            config_dict: Dictionary containing configuration parameters.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the config dict for the log (removing sensitive info)
        if hasattr(config_dict, 'get_all'):
            # It's a Configuration object
            safe_config = config_dict.get_all()
        elif hasattr(config_dict, 'copy'):
            # It's a standard dictionary
            safe_config = config_dict.copy()
        else:
            # Fallback: create a new dict
            safe_config = {k: v for k, v in config_dict.items()} if hasattr(config_dict, 'items') else {}
        
        # Remove sensitive information
        if 'llm_api_key' in safe_config:
            safe_config['llm_api_key'] = "***REDACTED***"
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # Write header information
        with open(self.log_file_path, 'w') as f:
            f.write(f"# Tree-of-Thoughts Agent Run\n\n")
            f.write(f"**Timestamp:** {timestamp}\n\n")
            f.write(f"**Task:** {task_description}\n\n")
            f.write(f"**Configuration:**\n")
            for key, value in sorted(safe_config.items()):
                f.write(f"- **{key}**: {value}\n")
            f.write("\n## Thought Process\n\n")
        
            # Ensure data is written to disk
            f.flush()
            os.fsync(f.fileno())
    
    def log_node_details(
        self,
        node_id: str,
        node_sub_problem: str,
        generated_thoughts: List[Dict[str, Any]],
        llm_decision: Dict[str, Any]
    ) -> None:
        """
        Log node details to the Markdown log file.
        
        Args:
            node_id: ID of the node being logged.
            node_sub_problem: Description of the sub-problem at this node.
            generated_thoughts: List of thoughts with their evaluations.
            llm_decision: Decision made by the LLM.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_type = llm_decision.get("action_type", "Unknown")
        selected_thought_id = llm_decision.get("selected_thought_id")
        decision_rationale = llm_decision.get("decision_rationale", "")
        
        # Start building the markdown content
        content = f"""
### Node: {node_id} ({timestamp})

#### Sub-Problem
> {node_sub_problem}

#### Generated Thoughts

"""
        
        # Add each thought with its evaluation
        for thought in generated_thoughts:
            thought_id = thought.get("thought_id", "unknown-id")
            description = thought.get("description", "")
            generation_rationale = thought.get("generation_rationale", "")
            evaluation_score = thought.get("evaluation_score", 0.0)
            evaluation_justification = thought.get("evaluation_justification", "")
            
            content += f"""**Thought {thought_id}:** {description}
- **Generation Rationale:** {generation_rationale}
- **Evaluation Score:** {evaluation_score:.2f}
- **Evaluation Justification:** {evaluation_justification}

"""
        
        # Add the decision
        content += f"""#### Decision
- **Action:** {action_type}
"""
        
        if selected_thought_id:
            content += f"- **Selected Thought:** {selected_thought_id}\n"
        
        content += f"""- **Rationale:** {decision_rationale}

---

"""
        
        # Append to the log file
        with open(self.log_file_path, 'a') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the JSON Schema definition of the log_node_details function.
        
        Returns:
            List containing the function definition in JSON Schema format.
        """
        log_function_name = self.config.get("function_names", {}).get("log_node", "log_node_details")
        
        return [{
            "name": log_function_name,
            "description": "Log details about a node in the thought tree, including its sub-problem, generated thoughts, and the LLM's decision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Unique identifier of the node."
                    },
                    "node_sub_problem": {
                        "type": "string",
                        "description": "Description of the sub-problem at this node."
                    },
                    "generated_thoughts": {
                        "type": "array",
                        "description": "List of generated thoughts with their evaluations.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "thought_id": {
                                    "type": "string",
                                    "description": "Unique identifier of the thought."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the thought."
                                },
                                "generation_rationale": {
                                    "type": "string",
                                    "description": "Rationale for generating this thought."
                                },
                                "evaluation_score": {
                                    "type": "number",
                                    "description": "Evaluation score between 0.0 and 1.0."
                                },
                                "evaluation_justification": {
                                    "type": "string",
                                    "description": "Justification for the evaluation score."
                                }
                            },
                            "required": ["thought_id", "description", "evaluation_score"]
                        }
                    },
                    "llm_decision": {
                        "type": "object",
                        "description": "Decision made by the LLM.",
                        "properties": {
                            "action_type": {
                                "type": "string",
                                "description": "Type of action to take next (Select, Backtrack, or Success).",
                                "enum": ["Select", "Backtrack", "Success"]
                            },
                            "selected_thought_id": {
                                "type": ["string", "null"],
                                "description": "ID of the selected thought (if action_type is Select, otherwise null)."
                            },
                            "decision_rationale": {
                                "type": "string",
                                "description": "Rationale for the decision."
                            }
                        },
                        "required": ["action_type", "decision_rationale"]
                    }
                },
                "required": ["node_id", "node_sub_problem", "generated_thoughts", "llm_decision"]
            }
        }]
