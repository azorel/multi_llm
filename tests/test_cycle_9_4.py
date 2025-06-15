
import pytest

def test_add_numbers():
    """Test basic addition"""
    # This test should fail initially (Red phase)
    from math_utils import add_numbers
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_multiply_numbers():
    """Test basic multiplication"""
    from math_utils import multiply_numbers  
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-1, 5) == -5
    assert multiply_numbers(0, 10) == 0
