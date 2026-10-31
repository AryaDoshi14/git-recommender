"""Tests for core/embeddings.py."""

import numpy as np
from core.embeddings import cosine_similarity, is_valid_embedding


def test_is_valid_embedding():
    """Verify is_valid_embedding correctly identifies valid and invalid embeddings."""
    assert is_valid_embedding([0.1, 0.2, 0.3]) is True
    assert is_valid_embedding(np.array([1.0, 2.0])) is True

    # Invalid cases
    assert is_valid_embedding([]) is False
    assert is_valid_embedding(None) is False
    assert is_valid_embedding("invalid") is False
    assert is_valid_embedding([1.0, "text"]) is False
    assert is_valid_embedding([float("nan"), 1.0]) is False


def test_cosine_similarity_standard_cases():
    """Verify cosine similarity calculations for normal vectors."""
    # Identical vectors -> 1.0
    v1 = [1.0, 2.0, 3.0]
    assert np.isclose(cosine_similarity(v1, v1), 1.0)

    # Orthogonal vectors -> 0.0
    v_x = [1.0, 0.0]
    v_y = [0.0, 1.0]
    assert np.isclose(cosine_similarity(v_x, v_y), 0.0)

    # Opposite vectors -> -1.0
    v_neg = [-1.0, -2.0, -3.0]
    assert np.isclose(cosine_similarity(v1, v_neg), -1.0)


def test_cosine_similarity_edge_cases():
    """Verify edge cases: zero magnitude, dimension mismatch, and invalid input return 0.0."""
    valid_vec = [1.0, 2.0, 3.0]
    zero_vec = [0.0, 0.0, 0.0]

    # Zero magnitude
    assert cosine_similarity(zero_vec, valid_vec) == 0.0
    assert cosine_similarity(zero_vec, zero_vec) == 0.0

    # Dimension mismatch
    diff_dim_vec = [1.0, 2.0]
    assert cosine_similarity(valid_vec, diff_dim_vec) == 0.0

    # Invalid input
    assert cosine_similarity(None, valid_vec) == 0.0
    assert cosine_similarity([], valid_vec) == 0.0
    assert cosine_similarity("string", valid_vec) == 0.0
