from pathlib import Path

BASE = Path("alembic/versions/2026_10_04_adastra_base.py").read_text()
BETA = Path("alembic/versions/2026_10_04_adastra_beta.py").read_text()

def test_beta_chain_is_explicit():
    assert 'down_revision = "2026_10_04_adastra_base"' in BETA
    assert '2026_10_04_adastra_beta' in BETA
    assert 'idx_beta_slots_status' in BETA
    assert 'for slot in range(1, 11)' in BETA

def test_api_does_not_create_schema_at_import():
    main = Path("app/main.py").read_text()
    assert "Base.metadata.create_all" not in main
