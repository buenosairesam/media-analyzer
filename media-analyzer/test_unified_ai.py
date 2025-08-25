#!/usr/bin/env python3
"""
Test script for unified AI architecture
Tests execution strategies without requiring full Django setup
"""

import os
import sys
from PIL import Image
import numpy as np

# Add backend to path
sys.path.append('backend')

def create_test_image():
    """Create a simple test image"""
    # Create a 100x100 RGB image with some content
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return Image.fromarray(img_array)

def test_execution_strategies():
    """Test each execution strategy independently"""
    
    print("Testing Execution Strategies")
    print("=" * 50)
    
    # Test Local Execution Strategy
    print("\n1. Testing Local Execution Strategy...")
    try:
        from ai_processing.execution_strategies.local_execution import LocalExecutionStrategy
        
        local_strategy = LocalExecutionStrategy()
        print(f"   Available: {local_strategy.is_available()}")
        print(f"   Info: {local_strategy.get_info()}")
        print("   ✅ Local strategy initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Local strategy failed: {e}")
    
    # Test Remote LAN Execution Strategy
    print("\n2. Testing Remote LAN Execution Strategy...")
    try:
        from ai_processing.execution_strategies.remote_lan_execution import RemoteLANExecutionStrategy
        
        # Use dummy host for testing
        remote_strategy = RemoteLANExecutionStrategy(worker_host="dummy-host:8001")
        print(f"   Available: {remote_strategy.is_available()}")
        print(f"   Info: {remote_strategy.get_info()}")
        print("   ✅ Remote LAN strategy initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Remote LAN strategy failed: {e}")
    
    # Test Cloud Execution Strategy
    print("\n3. Testing Cloud Execution Strategy...")
    try:
        from ai_processing.execution_strategies.cloud_execution import CloudExecutionStrategy
        
        cloud_strategy = CloudExecutionStrategy()
        print(f"   Available: {cloud_strategy.is_available()}")
        print(f"   Info: {cloud_strategy.get_info()}")
        print("   ✅ Cloud strategy initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Cloud strategy failed: {e}")

def test_execution_strategy_factory():
    """Test the execution strategy factory"""
    
    print("\n\nTesting Execution Strategy Factory")
    print("=" * 50)
    
    try:
        from ai_processing.execution_strategies.base import ExecutionStrategyFactory
        
        # Test local strategy creation
        print("\n1. Creating local strategy...")
        local_strategy = ExecutionStrategyFactory.create('local')
        print(f"   Created: {type(local_strategy).__name__}")
        print("   ✅ Local strategy creation successful")
        
        # Test remote LAN strategy creation
        print("\n2. Creating remote LAN strategy...")
        remote_strategy = ExecutionStrategyFactory.create('remote_lan', worker_host="test-host:8001")
        print(f"   Created: {type(remote_strategy).__name__}")
        print("   ✅ Remote LAN strategy creation successful")
        
        # Test cloud strategy creation
        print("\n3. Creating cloud strategy...")
        cloud_strategy = ExecutionStrategyFactory.create('cloud')
        print(f"   Created: {type(cloud_strategy).__name__}")
        print("   ✅ Cloud strategy creation successful")
        
    except Exception as e:
        print(f"   ❌ Factory test failed: {e}")

def test_analysis_engine_initialization():
    """Test AnalysisEngine initialization with different strategies"""
    
    print("\n\nTesting Analysis Engine Initialization")
    print("=" * 50)
    
    # Test with local strategy
    print("\n1. Testing with local strategy...")
    try:
        os.environ['AI_PROCESSING_MODE'] = 'local'
        from ai_processing.analysis_engine import AnalysisEngine
        
        engine = AnalysisEngine()
        health = engine.health_check()
        print(f"   Health check: {health}")
        print("   ✅ Local analysis engine initialization successful")
        
    except Exception as e:
        print(f"   ❌ Local analysis engine failed: {e}")
    
    # Test with remote LAN strategy
    print("\n2. Testing with remote LAN strategy...")
    try:
        os.environ['AI_PROCESSING_MODE'] = 'remote_lan'
        os.environ['AI_WORKER_HOST'] = 'test-host:8001'
        
        # Need to reload the module to pick up new env vars
        import importlib
        import ai_processing.analysis_engine
        importlib.reload(ai_processing.analysis_engine)
        
        engine = ai_processing.analysis_engine.AnalysisEngine()
        health = engine.health_check()
        print(f"   Health check: {health}")
        print("   ✅ Remote LAN analysis engine initialization successful")
        
    except Exception as e:
        print(f"   ❌ Remote LAN analysis engine failed: {e}")
    
    # Test with cloud strategy
    print("\n3. Testing with cloud strategy...")
    try:
        os.environ['AI_PROCESSING_MODE'] = 'cloud'
        
        # Reload again for cloud strategy
        importlib.reload(ai_processing.analysis_engine)
        
        engine = ai_processing.analysis_engine.AnalysisEngine()
        health = engine.health_check()
        print(f"   Health check: {health}")
        print("   ✅ Cloud analysis engine initialization successful")
        
    except Exception as e:
        print(f"   ❌ Cloud analysis engine failed: {e}")

def test_mock_adapter_execution():
    """Test execution strategies with a mock adapter"""
    
    print("\n\nTesting Mock Adapter Execution")
    print("=" * 50)
    
    class MockAdapter:
        """Mock adapter for testing"""
        def detect(self, image, confidence_threshold=0.5):
            return [
                {
                    'class': 'test_object',
                    'confidence': 0.95,
                    'bbox': [10, 10, 50, 50]
                }
            ]
    
    test_image = create_test_image()
    mock_adapter = MockAdapter()
    
    # Test local execution
    print("\n1. Testing local execution with mock adapter...")
    try:
        from ai_processing.execution_strategies.local_execution import LocalExecutionStrategy
        
        local_strategy = LocalExecutionStrategy()
        result = local_strategy.execute_detection(mock_adapter, test_image, 0.5)
        print(f"   Result: {result}")
        print("   ✅ Local execution with mock adapter successful")
        
    except Exception as e:
        print(f"   ❌ Local execution with mock adapter failed: {e}")

if __name__ == "__main__":
    print("Unified AI Architecture Test")
    print("=" * 50)
    
    test_execution_strategies()
    test_execution_strategy_factory() 
    test_analysis_engine_initialization()
    test_mock_adapter_execution()
    
    print("\n\nTest Summary")
    print("=" * 50)
    print("✅ All tests completed - check output above for specific results")