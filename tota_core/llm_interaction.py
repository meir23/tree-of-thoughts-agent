"""LLM Interaction Module.

This module handles all interactions with the LLM API, including:
- Formatting prompts
- Making API calls
- Handling function calling
- Parsing responses
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional

# Import Anthropic client
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Import OpenAI client (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMInteraction:
    """Handles interactions with the LLM API."""
    
    def __init__(self, config):
        """
        Initialize the LLM interaction module.
        
        Args:
            config: Configuration dictionary or object
        """
        self.logger = logging.getLogger('tota_core.llm_interaction')
        
        # Extract configuration parameters
        self.model = config.get('llm_model_identifier', 'claude-3-sonnet-20240229')
        self.api_base_url = config.get('llm_api_base_url', 'https://api.anthropic.com/v1')
        self.retry_attempts = config.get('llm_retry_attempts', 3)
        
        # Get API key from environment variables or config (prefer env vars)
        self.api_key = os.environ.get('ANTHROPIC_API_KEY') or config.get('llm_api_key', '')
        
        # Initialize Anthropic client
        if ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.logger.warning("Anthropic client not available. Install with: pip install anthropic")
            self.client = None
        
        # Template paths
        self.generation_prompt_template = config.get('generation_prompt_template')
        self.decision_hub_prompt_template = config.get('decision_hub_prompt_template')
    
    def _format_prompt(self, template_content: str, **kwargs) -> str:
        """
        Format a prompt template with the provided variables.
        
        Args:
            template_content: Template content to format
            **kwargs: Variables to format the template with
            
        Returns:
            Formatted prompt
        """
        return template_content.format(**kwargs)
    
    def call_llm(
        self,
        prompt_template_content: str,
        system_prompt: str = "",
        expect_function_call: bool = False,
        function_definitions: Optional[List[Dict[str, Any]]] = None,
        force_function_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call the LLM API with the provided prompt.
        
        Args:
            prompt_template_content: Template content for the prompt
            system_prompt: System prompt (optional)
            expect_function_call: Whether to expect a function call in the response
            function_definitions: List of function definitions for the LLM
            force_function_name: Force the LLM to use this function
            **kwargs: Variables to format the prompt template with
            
        Returns:
            Response from the LLM as a dictionary
        """
        # Format the prompt
        prompt = self._format_prompt(prompt_template_content, **kwargs)
        
        # Prepare messages
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Prepare API call parameters
        params = {
            "model": self.model,
            "max_tokens": 4000,
            "messages": messages
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt
        
        # Add function calling parameters if applicable
        if expect_function_call and function_definitions:
            # Convert function definitions to Anthropic's expected format with 'custom' type
            tools = []
            for func_def in function_definitions:
                tools.append({
                    "type": "custom",
                    "name": func_def["name"],
                    "description": func_def.get("description", ""),
                    "input_schema": func_def.get("parameters", {})
                })
            params["tools"] = tools
            
            # Force tool choice if specified
            if force_function_name:
                # Use the format from Anthropic API documentation: {"type": "tool", "name": "tool_name"}
                params["tool_choice"] = {
                    "type": "tool", 
                    "name": force_function_name
                }
        
        # Retry logic for transient errors
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.info(f"Calling LLM API (attempt {attempt}/{self.retry_attempts})")
                
                # Log the request for debugging
                self.logger.debug(f"Request to Anthropic API: {json.dumps(params, indent=2)}")
                
                # Make the API call using the client
                response = self.client.messages.create(**params)
                
                # Log the raw response for debugging
                self.logger.debug(f"Raw response from Anthropic API: {response}")
                
                # Parse the response
                if expect_function_call:
                    # Check for tool calls in response
                    tool_use_found = False
                    
                    for content_item in response.content:
                        if hasattr(content_item, 'type') and content_item.type == 'tool_use':
                            # Extract function call details
                            function_name = content_item.name
                            
                            # Parse arguments from JSON
                            try:
                                function_args = content_item.input if isinstance(content_item.input, dict) else json.loads(content_item.input)
                            except json.JSONDecodeError:
                                self.logger.error(f"Invalid JSON in function arguments: {content_item.input}")
                                raise ValueError("Invalid JSON in function arguments")
                            
                            function_call = {
                                "type": "function_call",
                                "name": function_name,
                                "arguments": function_args
                            }
                            tool_use_found = True
                            return function_call
                    
                    # If no tool use was found in the response
                    if not tool_use_found:
                        # Generate fallback function call for debug purposes
                        fallback_text = "No function call found in response. Full response content: "
                        for item in response.content:
                            if hasattr(item, 'type') and item.type == 'text':
                                fallback_text += item.text
                        
                        self.logger.warning(fallback_text)
                        
                        # If a specific function was forced, create a fallback function call
                        if force_function_name:
                            self.logger.warning(f"Creating fallback function call for {force_function_name}")
                            
                            # Extract basic information from the text response
                            text_response = ""
                            for item in response.content:
                                if hasattr(item, 'type') and item.type == 'text':
                                    text_response += item.text
                            
                            # Create a minimal fallback function call
                            return {
                                "type": "function_call",
                                "name": force_function_name,
                                "arguments": {
                                    "node_id": kwargs.get("node_id", "unknown"),
                                    "node_sub_problem": kwargs.get("current_sub_problem", "unknown"),
                                    "generated_thoughts": kwargs.get("thoughts", []),
                                    "llm_decision": {
                                        "action_type": "Backtrack",
                                        "decision_rationale": "Function calling failed, fallback to backtracking."
                                    }
                                }
                            }
                        else:
                            raise ValueError("Expected function call in response, but none was found")
                        
                # Process text response
                text_content = ""
                for content_item in response.content:
                    if hasattr(content_item, 'type') and content_item.type == 'text':
                        text_content += content_item.text
                
                return {"type": "text", "content": text_content}
                
            except (requests.exceptions.RequestException, TimeoutError) as e:
                # Handle transient errors (network issues, timeouts, rate limits)
                self.logger.warning(f"Transient error during LLM API call (attempt {attempt}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts:
                    # Exponential backoff: 2^attempt seconds (2, 4, 8, ...)
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed, raise the error
                    self.logger.error(f"All retry attempts failed: {e}")
                    raise Exception(f"API error: {e}")
            except Exception as e:
                # Handle other errors (authentication, invalid requests, etc.)
                self.logger.error(f"Error during LLM API call: {e}")
                raise Exception(f"API error: {e}")
        
        # This point should not be reached due to the raise in the loop
        return {"type": "error", "content": "Unexpected error in LLM call"}
    
    def load_prompt_template(self, template_path: str) -> str:
        """
        Load a prompt template from a file.
        
        Args:
            template_path: Path to the prompt template file.
            
        Returns:
            Content of the prompt template file as a string.
            
        Raises:
            FileNotFoundError: If the template file doesn't exist.
        """
        try:
            with open(template_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            self.logger.error(f"Prompt template file not found: {template_path}")
            raise FileNotFoundError(f"Prompt template file not found: {template_path}")
    
    def load_prompts_from_config(self) -> Dict[str, str]:
        """
        Load prompt templates specified in the configuration.
        
        Returns:
            Dictionary mapping prompt names to template content.
            
        Raises:
            FileNotFoundError: If any template file doesn't exist.
        """
        prompts = {}
        
        # Load generation prompt template
        generation_path = self.generation_prompt_template
        if generation_path:
            prompts['generation'] = self.load_prompt_template(generation_path)
        
        # Load decision hub prompt template
        decision_hub_path = self.decision_hub_prompt_template
        if decision_hub_path:
            prompts['decision_hub'] = self.load_prompt_template(decision_hub_path)
        
        return prompts
