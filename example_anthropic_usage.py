"""
Example: Using Anthropic/Claude models with the navegador agent.

This example demonstrates how to:
1. Load the Anthropic API key securely
2. Initialize Claude models with LangChain
3. Use Claude instead of OpenAI in your agent workflows

Requirements:
    - ANTHROPIC_API_KEY must be set in Codespaces secrets
    - anthropic and langchain-anthropic must be installed (see requirements.txt)
"""

from langchain_anthropic import ChatAnthropic
from config import get_config


def initialize_claude_models():
    """
    Initialize Claude models for use in the agent.

    Returns:
        dict: Dictionary of model configurations
    """
    # Get API key from config
    config = get_config()
    api_key = config.get_anthropic_key()

    if not api_key:
        raise ValueError(
            "Anthropic API key not found. "
            "Make sure ANTHROPIC_API_KEY is set in your Codespaces secrets."
        )

    # Define Claude model tiers (similar to OpenAI tiers in agent.py)
    models = {
        # Haiku: Fast and cost-effective for simple tasks
        'claude_bajo': ChatAnthropic(
            model='claude-3-5-haiku-20241022',
            anthropic_api_key=api_key,
            temperature=0.7,
            max_tokens=2048
        ),

        # Sonnet: Balanced performance for most tasks
        'claude_med': ChatAnthropic(
            model='claude-3-5-sonnet-20241022',
            anthropic_api_key=api_key,
            temperature=0.7,
            max_tokens=4096
        ),

        # Opus: Most capable for complex reasoning
        'claude_alto': ChatAnthropic(
            model='claude-3-opus-20240229',
            anthropic_api_key=api_key,
            temperature=0.7,
            max_tokens=4096
        ),
    }

    return models


def test_claude_model():
    """Quick test to verify Claude models are working."""
    print("🧪 Testing Claude model initialization...")

    try:
        models = initialize_claude_models()
        print("✅ Models initialized successfully:")
        for name, model in models.items():
            print(f"   - {name}: {model.model}")

        # Test a simple invocation
        print("\n🔄 Testing claude_med with a simple query...")
        response = models['claude_med'].invoke("Say hello in one sentence")
        print(f"✅ Response: {response.content}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# Example: Using Claude in a LangGraph agent (similar to agent.py structure)
def create_claude_agent():
    """
    Example of creating a LangGraph agent using Claude models.

    This follows the same pattern as the existing agent.py but uses Claude.
    """
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import MemorySaver

    # Initialize Claude models
    models = initialize_claude_models()

    # Use the medium tier (Sonnet) for the agent
    llm = models['claude_med']

    # Create a simple agent with memory
    memory = MemorySaver()
    agent = create_react_agent(
        llm,
        tools=[],  # Add your tools here
        checkpointer=memory
    )

    print("✅ Claude-powered agent created successfully")
    return agent


if __name__ == '__main__':
    # Run the test when executed directly
    print("=" * 60)
    print("Anthropic/Claude Model Integration Test")
    print("=" * 60)
    print()

    success = test_claude_model()

    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed! You're ready to use Claude models.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Import models in your agent code:")
        print("   from example_anthropic_usage import initialize_claude_models")
        print()
        print("2. Replace OpenAI models with Claude models:")
        print("   models = initialize_claude_models()")
        print("   llm = models['claude_med']")
        print()
        print("3. Use in your LangGraph agents as shown in create_claude_agent()")
    else:
        print("\n" + "=" * 60)
        print("❌ Tests failed. Check your API key configuration.")
        print("=" * 60)
