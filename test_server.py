#!/usr/bin/env python3
"""
Simple test script to verify the Smithery server can be created.
"""

import sys
import asyncio


def test_import():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from src.server.mcp.smithery_server import create_server, ConfigSchema
        print("✓ Imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config_schema():
    """Test that ConfigSchema is valid."""
    print("\nTesting ConfigSchema...")
    try:
        from src.server.mcp.smithery_server import ConfigSchema
        
        # Test with empty config
        config = ConfigSchema()
        print(f"✓ ConfigSchema created: {config}")
        
        # Test with values
        config = ConfigSchema(
            tushare_token="test_token",
            finnhub_api_key="test_key"
        )
        print(f"✓ ConfigSchema with values: {config}")
        return True
    except Exception as e:
        print(f"✗ ConfigSchema test failed: {e}")
        return False


def test_server_creation():
    """Test that server can be created."""
    print("\nTesting server creation...")
    try:
        from src.server.mcp.smithery_server import create_server
        
        # Create server
        mcp = create_server()
        print(f"✓ Server created: {mcp.name} v{mcp.version}")
        
        # Check that server has tools
        # Note: FastMCP doesn't expose tools list directly in all versions
        # so we just verify the server object exists
        print(f"✓ Server type: {type(mcp)}")
        
        return True
    except Exception as e:
        print(f"✗ Server creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Stock MCP Server - Smithery Compatibility Test")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_import()))
    results.append(("ConfigSchema Test", test_config_schema()))
    results.append(("Server Creation Test", test_server_creation()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✅ All tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Configure .env file with API keys")
        print("3. Test locally: uv run dev")
        print("4. Deploy to Smithery: Push to GitHub and click Deploy")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
