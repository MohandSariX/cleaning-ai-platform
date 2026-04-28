"""
Tests pour Claude Memory — Mémoire persistante
"""
import pytest
from app.agents.claude_memory import (
    store, retrieve, search, delete,
    log_decision, update_decision_outcome, get_recent_decisions,
    store_message, get_conversation_history,
    initialize_default_memories
)


def test_store_and_retrieve():
    """Test stockage et récupération mémoire."""
    key = "test_memory_key"
    value = "test_value"
    context = "test"

    # Stocker
    success = store(key, value, context, {"meta": "data"})
    assert success, "Store should succeed"

    # Récupérer
    result = retrieve(key)
    assert result is not None, "Retrieve should return data"
    assert result["value"] == value, "Value should match"
    assert result["context"] == context, "Context should match"

    # Nettoyer
    delete(key)


def test_search_by_context():
    """Test recherche par contexte."""
    # Stocker plusieurs entrées
    store("test_search_1", "value1", "search_test")
    store("test_search_2", "value2", "search_test")
    store("test_search_3", "value3", "other_context")

    # Rechercher
    results = search(context="search_test")
    assert len(results) >= 2, "Should find at least 2 entries"

    # Nettoyer
    delete("test_search_1")
    delete("test_search_2")
    delete("test_search_3")


def test_log_decision():
    """Test logging décisions."""
    decision_id = log_decision(
        decision_type="test_decision",
        decision_data={"test": "data"},
        reasoning="Test reasoning",
        escalated=False
    )

    assert decision_id > 0, "Decision ID should be positive"

    # Récupérer
    decisions = get_recent_decisions(decision_type="test_decision", limit=1)
    assert len(decisions) > 0, "Should find decision"
    assert decisions[0]["type"] == "test_decision"


def test_update_decision_outcome():
    """Test mise à jour résultat décision."""
    decision_id = log_decision(
        decision_type="test_update",
        decision_data={},
        reasoning="Test"
    )

    success = update_decision_outcome(decision_id, "success", "Test feedback")
    assert success, "Update should succeed"


def test_conversation_history():
    """Test historique conversations."""
    # Stocker messages
    store_message("mohand", "Test message from Mohand")
    store_message("claude", "Test response from Claude")

    # Récupérer
    history = get_conversation_history(limit=10)
    assert len(history) >= 2, "Should find at least 2 messages"


def test_initialize_default_memories():
    """Test initialisation mémoires par défaut."""
    initialize_default_memories()

    # Vérifier que les mémoires par défaut existent
    role = retrieve("role")
    assert role is not None, "Role should be initialized"
    assert "Proprexis" in role["value"], "Should mention Proprexis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
