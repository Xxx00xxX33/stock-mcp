#!/usr/bin/env python3
"""
Simple structure test that doesn't require full dependencies.
"""

import os
import sys


def test_required_files():
    """Test that all required files exist."""
    print("Testing required files...")
    
    required_files = [
        "smithery.yaml",
        "pyproject.toml",
        ".env.example",
        ".gitignore",
        "README_SMITHERY.md",
        "src/server/mcp/smithery_server.py",
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} NOT FOUND")
            all_exist = False
    
    return all_exist


def test_smithery_yaml():
    """Test smithery.yaml content."""
    print("\nTesting smithery.yaml...")
    
    try:
        with open("smithery.yaml", "r") as f:
            content = f.read().strip()
        
        if content == 'runtime: "python"':
            print("  ✓ smithery.yaml has correct content")
            return True
        else:
            print(f"  ✗ smithery.yaml content incorrect: {content}")
            return False
    except Exception as e:
        print(f"  ✗ Failed to read smithery.yaml: {e}")
        return False


def test_pyproject_toml():
    """Test pyproject.toml structure."""
    print("\nTesting pyproject.toml...")
    
    try:
        import tomllib
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        
        # Check required sections
        checks = [
            ("build-system" in data, "build-system section"),
            ("project" in data, "project section"),
            ("tool" in data and "smithery" in data["tool"], "tool.smithery section"),
        ]
        
        all_passed = True
        for passed, desc in checks:
            if passed:
                print(f"  ✓ {desc}")
            else:
                print(f"  ✗ {desc} missing")
                all_passed = False
        
        # Check server entry point
        if all_passed:
            server_entry = data["tool"]["smithery"].get("server")
            if server_entry == "src.server.mcp.smithery_server:create_server":
                print(f"  ✓ Server entry point: {server_entry}")
            else:
                print(f"  ✗ Server entry point incorrect: {server_entry}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Failed to parse pyproject.toml: {e}")
        return False


def test_server_file():
    """Test that server file has required structure."""
    print("\nTesting smithery_server.py structure...")
    
    try:
        with open("src/server/mcp/smithery_server.py", "r") as f:
            content = f.read()
        
        checks = [
            ("from smithery.decorators import smithery" in content, "@smithery decorator import"),
            ("from fastmcp import FastMCP" in content, "FastMCP import"),
            ("class ConfigSchema" in content, "ConfigSchema class"),
            ("@smithery.server" in content, "@smithery.server decorator"),
            ("def create_server()" in content, "create_server function"),
        ]
        
        all_passed = True
        for passed, desc in checks:
            if passed:
                print(f"  ✓ {desc}")
            else:
                print(f"  ✗ {desc} missing")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Failed to read smithery_server.py: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Stock MCP Server - Smithery Structure Test")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Required Files", test_required_files()))
    results.append(("smithery.yaml", test_smithery_yaml()))
    results.append(("pyproject.toml", test_pyproject_toml()))
    results.append(("smithery_server.py", test_server_file()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✅ All structure tests passed!")
        print("\nProject is ready for Smithery deployment:")
        print("1. Push code to GitHub")
        print("2. Connect GitHub to Smithery.ai")
        print("3. Click Deploy in Deployments tab")
        print("4. Wait for build to complete")
        print("5. Configure API keys in Smithery UI")
        print("6. Connect from Claude Desktop or Cursor")
        return 0
    else:
        print("\n❌ Some structure tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
