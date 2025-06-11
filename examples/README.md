# Autonomous Multi-LLM Agent Examples

This directory contains practical examples demonstrating the features and capabilities of the autonomous multi-LLM agent system.

## Sequential Thinking Examples

### sequential_thinking_example.py

Comprehensive examples demonstrating the sequential thinking capabilities integrated via the MCP (Model Context Protocol) server.

**Features Demonstrated:**
- Basic step-by-step problem solving
- Advanced thinking with revisions and branching
- Integration manager usage
- Thought process visualization

**Key Concepts:**
- **Sequential Thinking**: Structured approach to complex problem solving
- **Thought Revision**: Ability to reconsider and improve previous thoughts
- **Thought Branching**: Exploring alternative solution paths
- **Session Management**: Managing long-running thinking processes

**Usage:**
```bash
# Run the sequential thinking examples
python examples/sequential_thinking_example.py
```

**Example Output:**
```
Basic Sequential Thinking Example
=== Basic Sequential Thinking Example ===
Started thinking session: thinking-session-12345
Problem: How can we implement rate limiting in a distributed API gateway?
Thought 1: First, I need to understand the requirements: rate limiting scope, algorithms, and storage.
Thought 2: I should consider different rate limiting algorithms: token bucket, sliding window, fixed window.
...
✓ Basic thinking session completed
```

## What is Sequential Thinking?

Sequential thinking is a structured problem-solving approach that breaks down complex problems into manageable steps. The system provides:

1. **Step-by-Step Analysis**: Problems are decomposed into logical thinking steps
2. **Dynamic Adaptation**: The number of steps can be adjusted as understanding evolves
3. **Revision Capability**: Previous thoughts can be reconsidered and improved
4. **Branching**: Alternative solution paths can be explored
5. **Context Preservation**: The full thinking process is maintained for reference

## Integration with Autonomous Agents

The sequential thinking capability is integrated into the autonomous agent system through:

- **MCP Server**: A Node.js-based Model Context Protocol server that handles the thinking logic
- **Python Client**: A Python client that interfaces with the MCP server
- **Integration Manager**: Centralized management of sequential thinking sessions
- **Agent Factory**: All agents are equipped with sequential thinking capabilities

## Running the Examples

### Prerequisites

1. **Node.js and npm** (for the MCP server):
   ```bash
   # Install Node.js (if not already installed)
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Build the MCP Server**:
   ```bash
   # Run the setup script
   ./setup_mcp_servers.sh
   
   # Or manually:
   cd mcp-servers/sequential-thinking
   npm install
   npm run build
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running Examples

```bash
# Test the integration
python test_sequential_thinking_integration.py

# Run example scenarios
python examples/sequential_thinking_example.py
```

## Example Scenarios

### 1. API Rate Limiting Design
**Problem**: Implement rate limiting in a distributed API gateway
**Approach**: Step-by-step analysis of requirements, algorithms, and implementation

### 2. Real-time Collaborative Editing
**Problem**: Design a Google Docs-like collaborative document editor
**Approach**: Advanced thinking with revisions and exploring alternative architectures

### 3. Database Query Optimization
**Problem**: Optimize database queries in high-traffic e-commerce
**Approach**: Integration manager-based problem solving

## Configuration

Sequential thinking is configured in `config/config.yaml`:

```yaml
# Sequential Thinking Integration (MCP)
integrations:
  sequential_thinking:
    enabled: true
    priority: 9
    timeout: 60.0
    max_retries: 2
    config:
      server_path: null  # Will use default path
      max_concurrent_sessions: 5
      session_timeout_minutes: 30
      auto_cleanup_completed_sessions: true

# Feature flag
features:
  integrations:
    sequential_thinking: true
```

## API Reference

### SequentialThinkingClient

Main client for interacting with the sequential thinking MCP server.

```python
from src.integrations.sequential_thinking_client import SequentialThinkingClient

client = SequentialThinkingClient()

# Start a thinking session
session_id = await client.start_thinking_session("Your problem description")

# Add thought steps
await client.add_thought_step(
    session_id=session_id,
    thought="Your thinking step",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True
)

# Revise a thought
await client.revise_thought(
    session_id=session_id,
    original_thought_number=2,
    revised_thought="Improved thinking"
)

# Create a branch
await client.create_thought_branch(
    session_id=session_id,
    branch_from_thought_number=3,
    branch_thought="Alternative approach",
    branch_id="alternative_branch"
)

# Complete the session
await client.complete_thinking_session(session_id, "Final solution")
```

### Integration Manager

Use sequential thinking through the centralized integration manager:

```python
from src.integrations.manager import IntegrationManager

manager = IntegrationManager(config)
await manager.start()

# Solve problems step-by-step
result = await manager.solve_problem_step_by_step(
    problem_description="Your problem",
    initial_thought_estimate=5,
    max_thoughts=10
)
```

## Troubleshooting

### Common Issues

1. **MCP Server Not Built**:
   ```bash
   cd mcp-servers/sequential-thinking
   npm install && npm run build
   ```

2. **Node.js Not Found**:
   ```bash
   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. **Connection Timeout**:
   - Check if the MCP server builds correctly
   - Verify the server path in configuration
   - Increase timeout values in config

### Debugging

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or with loguru
from loguru import logger
logger.level("DEBUG")
```

## Performance Considerations

- **Session Limits**: Configure `max_concurrent_sessions` based on available resources
- **Timeouts**: Adjust `timeout` and `session_timeout_minutes` for your use case
- **Cleanup**: Enable `auto_cleanup_completed_sessions` to prevent memory leaks
- **Retry Logic**: Configure appropriate retry policies for network resilience

## Contributing

When adding new examples:

1. Follow the existing code structure
2. Include comprehensive documentation
3. Add error handling and logging
4. Test with different scenarios
5. Update this README with new examples

## Further Reading

- [Model Context Protocol (MCP) Documentation](https://modelcontextprotocol.io)
- [Sequential Thinking MCP Server](../mcp-servers/sequential-thinking/README.md)
- [Integration Manager Documentation](../docs/integration-guide.md)
- [Agent Factory Documentation](../docs/agent-guide.md)