#!/usr/bin/env python3
"""
Script pour lancer tous les tests
"""
import pytest
import sys

if __name__ == "__main__":
    print("🧪 Lancement des tests Proprexis CRM\n")
    print("=" * 60)

    # Options pytest
    args = [
        "tests/",
        "-v",  # Verbose
        "--tb=short",  # Traceback court
        "--color=yes",  # Couleurs
        "-s",  # Print output
    ]

    # Lancer pytest
    exit_code = pytest.main(args)

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ Tous les tests sont passés !")
    else:
        print(f"❌ Certains tests ont échoué (exit code: {exit_code})")

    sys.exit(exit_code)
