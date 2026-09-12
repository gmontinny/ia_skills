from src.services.knowledge_loader import parse_knowledge

VALID_KNOWLEDGE_YAML = """
knowledge_object:
  id: test/bundle
  name: Test Bundle
  version: "1.0"
  description: Bundle de teste

trust_signals:
  status: stable
  stale_after: "2030-01-01T00:00:00-04:00"
  autonomous_use: allowed
  maturity: mvp
"""

PROHIBITED_KNOWLEDGE_YAML = """
knowledge_object:
  id: test/restricted
  name: Restricted Bundle

trust_signals:
  status: draft
  autonomous_use: prohibited_before_end_to_end_test
"""


def test_parse_knowledge_valid():
    bundle = parse_knowledge(VALID_KNOWLEDGE_YAML)
    assert bundle is not None
    assert bundle.name == "Test Bundle"
    assert bundle.trust_signals.status == "stable"
    assert bundle.is_autonomous_use_prohibited is False


def test_parse_knowledge_prohibited():
    bundle = parse_knowledge(PROHIBITED_KNOWLEDGE_YAML)
    assert bundle.is_autonomous_use_prohibited is True


def test_parse_knowledge_invalid_yaml():
    bundle = parse_knowledge("{ invalid: yaml: content: [}")
    assert bundle is None
