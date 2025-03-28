# Tree-of-Thoughts Agent (ToTA)

A powerful agent-based system that explores a dynamic tree of potential solution steps using Large Language Models (LLMs) with function calling. ToTA breaks down complex problems into steps, generates and evaluates multiple possible paths, and produces a comprehensive, transparent reasoning trail.

## 📋 Features

- **Tree Exploration**: Dynamically builds and explores a tree of thoughts to solve complex problems
- **LLM-driven Decisions**: Uses LLMs to generate thoughts, evaluate paths, and decide next actions
- **Function Calling**: Leverages modern LLM function calling capabilities for structured output
- **Comprehensive Logging**: Creates detailed Markdown logs of the entire reasoning process
- **Flexible Configuration**: Easily configurable via YAML for various parameters and limits

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ installed
- Anthropic API key (for Claude models) or OpenAI API key (if configured for GPT models)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/meir23/tree-of-thoughts-agent.git
   cd tree-of-thoughts-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Running the Agent

Run the agent from the command line:

```bash
python main.py --task "Create a 3-step plan to learn Python" --config config.yaml
```

Or use the test script to verify functionality:

```bash
python test_tota_agent.py
```

## 🔧 Configuration

The agent is configured via a YAML file. Here's an example `config.yaml`:

```yaml
# LLM Configuration
llm_model_identifier: "claude-3-sonnet-20240229"  # Anthropic Claude 3 Sonnet
llm_api_base_url: "https://api.anthropic.com/v1"  # Anthropic API endpoint
llm_retry_attempts: 3

# Prompt Templates
generation_prompt_template: "prompts/generation_prompt.txt"
decision_hub_prompt_template: "prompts/decision_hub_prompt.txt"

# Tree Exploration Limits
max_depth: 10          # Maximum depth of tree exploration
max_breadth: 3         # Maximum number of thoughts per node
max_nodes: null        # Optional cap on total nodes (null = unlimited)
max_llm_calls: null    # Optional cap on total LLM API calls (null = unlimited)
max_time_limit_seconds: null  # Optional time limit in seconds (null = unlimited)

# Logging Configuration
log_file_path_template: "logs/tota_run_{timestamp}.md"

# Function Names
function_names:
  log_node: "log_node_details"
```

## 📂 Project Structure

```
tota_agent/
├── main.py                    # Entry point for CLI execution
├── config.yaml                # Configuration file
├── tota_core/                 # Core components
│   ├── __init__.py
│   ├── control_flow_manager.py  # Main orchestrator
│   ├── llm_interaction.py       # LLM API interactions
│   ├── tree_manager.py          # Manages tree state
│   ├── function_implementations.py  # Function call implementations
│   └── configuration.py         # Loads and validates config
├── prompts/                  # Prompt templates
│   ├── generation_prompt.txt   # For thought generation
│   └── decision_hub_prompt.txt # For decision making
├── logs/                     # Output logs directory
│   └── tota_run_*.md          # Generated Markdown logs
└── tests/                    # Test files
    └── ...
```

## 🔄 How It Works

1. **Initialization**: The agent loads configuration, initializes components, and creates a root node with the task.

2. **Tree Exploration**: For each node, the agent:
   - Generates multiple potential thoughts using the LLM
   - Calls the Decision Hub to evaluate thoughts and decide the next action
   - Logs the decision and reasoning via function calling
   - Takes action based on the LLM's decision (Select, Backtrack, Success)

3. **Function Calling**: The agent uses structured function calling to:
   - Format parameters for the LLM
   - Convert function definitions to the LLM API's format
   - Configure the tool_choice parameter
   - Parse the response to extract function call details
   - Execute the function with extracted arguments

4. **Logging**: Each node's exploration is logged in a structured Markdown file, creating a comprehensive thinking trace.

## 📝 Example Log Output

Each log file includes:
- Task description and configuration
- For each explored node:
  - Sub-problem description
  - Generated thoughts with rationales
  - Evaluation scores and justifications
  - Decision (Select, Backtrack, Success) with rationale
- Final metrics (termination reason, elapsed time, total nodes, etc.)

## 🧪 Testing

Run the standard test to verify functionality:

```bash
python test_tota_agent.py
```

To test function calling specifically:

```bash
python test_function_calling.py
```

## 🔍 Troubleshooting

### Common Issues

1. **API Authentication Errors**:
   - Verify your API key in the .env file
   - Check if the API key has the necessary permissions

2. **Function Calling Errors**:
   - Ensure the LLM model supports function calling (Claude 3+)
   - Check the format of function definitions matches the LLM API's requirements

3. **Missing Dependencies**:
   - Run `pip install -r requirements.txt` to install all required packages

### Debugging

- Set logging level to DEBUG in the scripts for more verbose output
- Check the generated log files for detailed thinking traces

## 📚 Further Development

- Add support for more LLM providers
- Implement parallel thought exploration
- Create a web interface for visualization
- Add more agent capabilities through additional function definitions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.