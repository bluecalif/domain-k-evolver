"""Task 2.3 테스트: Config 환경 설정."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from src.config import (
    EvolverConfig,
    LLMConfig,
    OrchestratorConfig,
    SearchConfig,
    write_config_snapshot,
)


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4.1-mini"
        assert cfg.temperature == 0.2
        assert cfg.max_tokens == 4096

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        monkeypatch.setenv("EVOLVER_LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("EVOLVER_LLM_TEMPERATURE", "0.5")
        cfg = LLMConfig.from_env()
        assert cfg.api_key == "sk-test-123"
        assert cfg.model == "gpt-4o"
        assert cfg.temperature == 0.5

    def test_frozen(self):
        cfg = LLMConfig()
        with pytest.raises(AttributeError):
            cfg.model = "other"


class TestSearchConfig:
    def test_defaults(self):
        cfg = SearchConfig()
        assert cfg.provider == "tavily"
        assert cfg.max_results == 5

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-456")
        monkeypatch.setenv("EVOLVER_SEARCH_MAX_RESULTS", "10")
        cfg = SearchConfig.from_env()
        assert cfg.api_key == "tvly-test-456"
        assert cfg.max_results == 10


class TestOrchestratorConfig:
    def test_defaults(self):
        cfg = OrchestratorConfig()
        assert cfg.max_cycles == 10
        assert cfg.snapshot_every == 1
        assert cfg.invariant_check is True
        assert cfg.stop_on_convergence is True

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("EVOLVER_MAX_CYCLES", "20")
        monkeypatch.setenv("EVOLVER_STOP_ON_CONVERGENCE", "false")
        cfg = OrchestratorConfig.from_env()
        assert cfg.max_cycles == 20
        assert cfg.stop_on_convergence is False


class TestEvolverConfig:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
        cfg = EvolverConfig.from_env()
        assert cfg.llm.api_key == "sk-test"
        assert cfg.search.api_key == "tvly-test"
        assert cfg.orchestrator.max_cycles == 10


class TestWriteConfigSnapshot:
    """P0-A6: config.snapshot.json 자동 작성."""

    def _make_config(self) -> EvolverConfig:
        return EvolverConfig(
            llm=LLMConfig(api_key="sk-secret"),
            search=SearchConfig(api_key="tvly-secret"),
            orchestrator=OrchestratorConfig(
                max_cycles=5,
                bench_root="bench/silver/japan-travel/test-trial",
            ),
        )

    def _write_skeleton(self, trial_dir: Path) -> Path:
        state_dir = trial_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        skeleton = state_dir / "domain-skeleton.json"
        skeleton.write_text(
            json.dumps({"categories": [{"name": "transport"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        return skeleton

    def test_snapshot_file_created_with_required_fields(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        target = write_config_snapshot(cfg, tmp_path)

        assert target.exists()
        assert target.name == "config.snapshot.json"

        data = json.loads(target.read_text(encoding="utf-8"))
        for key in (
            "schema_version",
            "timestamp",
            "git_head",
            "llm",
            "search",
            "orchestrator",
            "providers",
            "skeleton_path",
            "skeleton_sha256",
        ):
            assert key in data, f"missing key: {key}"

    def test_snapshot_redacts_api_keys(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        assert data["llm"]["api_key"] == "<redacted>"
        assert data["search"]["api_key"] == "<redacted>"
        # Secret literal must never appear in the serialized snapshot
        raw = target.read_text(encoding="utf-8")
        assert "sk-secret" not in raw
        assert "tvly-secret" not in raw

    def test_snapshot_skeleton_sha256_matches(self, tmp_path):
        cfg = self._make_config()
        skeleton = self._write_skeleton(tmp_path)
        expected = hashlib.sha256(skeleton.read_bytes()).hexdigest()

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        assert data["skeleton_sha256"] == expected

    def test_snapshot_skeleton_missing_falls_back(self, tmp_path):
        cfg = self._make_config()
        # skeleton 없음

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        assert data["skeleton_sha256"] == "missing"

    def test_snapshot_provider_list_default_and_override(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        # default → search provider
        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["providers"] == [cfg.search.provider]

        # override
        trial2 = tmp_path / "trial2"
        self._write_skeleton(trial2)
        target2 = write_config_snapshot(
            cfg, trial2, provider_list=["tavily", "ddg", "curated"]
        )
        data2 = json.loads(target2.read_text(encoding="utf-8"))
        assert data2["providers"] == ["tavily", "ddg", "curated"]

    def test_snapshot_orchestrator_fields_preserved(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        assert data["orchestrator"]["max_cycles"] == 5
        assert (
            data["orchestrator"]["bench_root"]
            == "bench/silver/japan-travel/test-trial"
        )

    def test_snapshot_git_head_is_string(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        git_head = data["git_head"]
        assert isinstance(git_head, str)
        # Either real 40-char hash or "unknown" fallback
        assert git_head == "unknown" or len(git_head) >= 7

    def test_snapshot_trial_dir_created_if_missing(self, tmp_path):
        cfg = self._make_config()
        new_trial = tmp_path / "new-trial"
        assert not new_trial.exists()

        target = write_config_snapshot(cfg, new_trial)

        assert new_trial.exists()
        assert target.exists()

    def test_snapshot_roundtrip_stable(self, tmp_path):
        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))

        # Re-serialize → same keys
        again = json.loads(json.dumps(data))
        assert again == data

    def test_snapshot_git_head_unknown_when_not_a_repo(self, tmp_path, monkeypatch):
        """subprocess 실패 → git_head == 'unknown'."""
        import subprocess as sp

        cfg = self._make_config()
        self._write_skeleton(tmp_path)

        def _raise(*args, **kwargs):
            raise sp.CalledProcessError(128, args[0])

        monkeypatch.setattr(sp, "check_output", _raise)

        target = write_config_snapshot(cfg, tmp_path)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["git_head"] == "unknown"
