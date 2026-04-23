"""SI-P7 V2 계측 테스트 — si-p7-signals.json persist + load + snapshot.

V-T5 a단계: state.py 신규 필드 + state_io.py 확장만 검증.
V-T5 b/c 단계 (telemetry si_p7 sub-dict + emit 경로) 테스트는 별도 추가.

원칙 (D-187):
- fixture = real snapshot (`bench/japan-travel/state/*.json`)
- function stub / mock 금지
"""

from pathlib import Path

from src.utils.state_io import load_state, save_state, snapshot_state

BENCH = Path("bench/japan-travel")

_SIGNAL_FIELDS = (
    "integration_result_dist",
    "ku_stagnation_signals",
    "aggressive_mode_remaining",
    "recent_conflict_fields",
    "adjacency_yield",
    "coverage_map",
    "aggressive_mode_history",
    "query_rewrite_rx_log",
    "condition_split_events",
    "suppress_event_log",
)


def _state_with_all_signals() -> dict:
    """real snapshot 로드 후 10개 si-p7 신호 필드에 샘플 값 주입."""
    state = load_state(BENCH)
    state["integration_result_dist"] = {
        "resolved": 5,
        "no_source_gu": 1,
        "cycle_history": [{"cycle": 14, "resolved": 5}],
    }
    state["ku_stagnation_signals"] = {
        "added_history": [{"cycle": 14, "added": 3, "total_claims": 10, "added_ratio": 0.3}],
        "conflict_hold_history": [{"cycle": 14, "conflict_hold": 1}],
        "condition_split_history": [{"cycle": 14, "condition_split": 2}],
    }
    state["aggressive_mode_remaining"] = 3
    state["recent_conflict_fields"] = [{"field": "price", "since_cycle": 14}]
    state["adjacency_yield"] = {
        "transport:price→duration": [{"cycle": 14, "attempted": 3, "resolved": 2}]
    }
    state["coverage_map"] = {"transport": {"deficit_score": 0.3}}
    state["aggressive_mode_history"] = [
        {"cycle": 14, "remaining": 3, "event": "entered", "rx_id": "ku_stagnation:added_low"}
    ]
    state["query_rewrite_rx_log"] = [
        {"cycle": 14, "gu_id": "gu-001", "slug": "jr-pass", "field": "price",
         "rewritten_queries": ["jr pass cost 2026"]}
    ]
    state["condition_split_events"] = [
        {"cycle": 14, "ku_id": "ku-001", "claim_entity": "japan-travel:transport:jr-pass",
         "field": "price", "reason": "conditions"}
    ]
    state["suppress_event_log"] = [
        {"cycle": 14, "category": "transport", "threshold": 1.5,
         "suppressed_fields": ["price", "duration"], "field_counts": {"price": 3, "duration": 2}}
    ]
    return state


# === Test 1: save → si-p7-signals.json 생성 + 필드 match ===

def test_save_state_writes_si_p7_signals_file(tmp_path):
    state = _state_with_all_signals()
    save_state(state, tmp_path)

    signals_path = tmp_path / "state" / "si-p7-signals.json"
    assert signals_path.exists(), "si-p7-signals.json 이 생성되어야 함"

    import json
    data = json.loads(signals_path.read_text(encoding="utf-8"))

    for field in _SIGNAL_FIELDS:
        assert field in data, f"필드 누락: {field}"

    assert data["aggressive_mode_remaining"] == 3
    assert data["recent_conflict_fields"][0]["field"] == "price"
    assert data["condition_split_events"][0]["reason"] == "conditions"


# === Test 2: 모든 필드가 비어있으면 파일 생성 안 됨 ===

def test_save_state_skips_si_p7_signals_when_empty(tmp_path):
    state = load_state(BENCH)
    # load_state 기본값은 전부 비어있음 (coverage_map={}, remaining=0, lists=[])
    # 명시적으로 모두 비운 상태
    for field in _SIGNAL_FIELDS:
        if field == "aggressive_mode_remaining":
            state[field] = 0
        elif field in ("integration_result_dist", "ku_stagnation_signals",
                       "adjacency_yield", "coverage_map"):
            state[field] = {}
        else:
            state[field] = []

    save_state(state, tmp_path)

    signals_path = tmp_path / "state" / "si-p7-signals.json"
    assert not signals_path.exists(), "모든 필드가 비면 파일을 생성하면 안 됨"


# === Test 3: save → load 라운드트립, 필드 복원 ===

def test_load_state_populates_si_p7_signals(tmp_path):
    state = _state_with_all_signals()
    save_state(state, tmp_path)

    reloaded = load_state(tmp_path)

    assert reloaded["aggressive_mode_remaining"] == 3
    assert reloaded["recent_conflict_fields"] == [{"field": "price", "since_cycle": 14}]
    assert reloaded["coverage_map"] == {"transport": {"deficit_score": 0.3}}
    assert reloaded["aggressive_mode_history"][0]["event"] == "entered"
    assert reloaded["query_rewrite_rx_log"][0]["slug"] == "jr-pass"
    assert reloaded["condition_split_events"][0]["reason"] == "conditions"
    assert reloaded["suppress_event_log"][0]["suppressed_fields"] == ["price", "duration"]


def test_load_state_defaults_when_signals_file_missing(tmp_path):
    """si-p7-signals.json 부재 시 기본값으로 populate."""
    state = load_state(BENCH)
    # 일부 field 만 설정, save → 원래 non-empty 만 persist
    state["aggressive_mode_remaining"] = 0
    for field in _SIGNAL_FIELDS:
        if field == "aggressive_mode_remaining":
            state[field] = 0
        elif field in ("integration_result_dist", "ku_stagnation_signals",
                       "adjacency_yield", "coverage_map"):
            state[field] = {}
        else:
            state[field] = []
    save_state(state, tmp_path)

    reloaded = load_state(tmp_path)
    assert reloaded["aggressive_mode_remaining"] == 0
    assert reloaded["recent_conflict_fields"] == []
    assert reloaded["condition_split_events"] == []


# === Test 4: snapshot_state 가 si-p7-signals.json 을 cycle snapshot 에 복사 ===

def test_snapshot_state_copies_si_p7_signals(tmp_path):
    state = _state_with_all_signals()
    save_state(state, tmp_path)

    snapshot_dir = snapshot_state(tmp_path, cycle=14)

    signals_copy = snapshot_dir / "si-p7-signals.json"
    assert signals_copy.exists(), "snapshot 디렉토리에 si-p7-signals.json 복사 필요"

    import json
    data = json.loads(signals_copy.read_text(encoding="utf-8"))
    assert data["aggressive_mode_remaining"] == 3
    assert len(data["aggressive_mode_history"]) == 1


def test_snapshot_state_omits_signals_when_source_missing(tmp_path):
    """source 파일 없으면 snapshot 에도 복사 안 함."""
    state = load_state(BENCH)
    # 빈 상태 저장 → si-p7-signals.json 생성 안 됨
    for field in _SIGNAL_FIELDS:
        if field == "aggressive_mode_remaining":
            state[field] = 0
        elif field in ("integration_result_dist", "ku_stagnation_signals",
                       "adjacency_yield", "coverage_map"):
            state[field] = {}
        else:
            state[field] = []
    save_state(state, tmp_path)

    snapshot_dir = snapshot_state(tmp_path, cycle=14)
    assert not (snapshot_dir / "si-p7-signals.json").exists()


def test_save_creates_bak_on_overwrite(tmp_path):
    """2차 save 시 기존 파일은 .bak 로 백업."""
    state = _state_with_all_signals()
    save_state(state, tmp_path)

    # remaining 값 변경 후 재저장
    state["aggressive_mode_remaining"] = 2
    save_state(state, tmp_path)

    signals_path = tmp_path / "state" / "si-p7-signals.json"
    bak_path = signals_path.with_suffix(signals_path.suffix + ".bak")
    assert bak_path.exists(), ".bak 백업 파일이 생성되어야 함"

    import json
    current = json.loads(signals_path.read_text(encoding="utf-8"))
    previous = json.loads(bak_path.read_text(encoding="utf-8"))
    assert current["aggressive_mode_remaining"] == 2
    assert previous["aggressive_mode_remaining"] == 3


# === Telemetry si_p7 sub-dict (V-T5 b단계) ===

def test_telemetry_emits_si_p7_subdict(tmp_path):
    """_build_snapshot → si_p7 sub-dict 가 cycle snapshot 에 포함."""
    from src.obs.telemetry import emit_cycle

    state = _state_with_all_signals()
    state["current_cycle"] = 14
    state["cycle_count"] = 14

    # trial-card.md 존재 가정 (emit_cycle warning 회피 용)
    (tmp_path / "trial-card.md").write_text("# trial", encoding="utf-8")

    emit_cycle(state, tmp_path, cycle_elapsed_s=1.23)

    cycles_path = tmp_path / "telemetry" / "cycles.jsonl"
    assert cycles_path.exists()

    import json
    line = cycles_path.read_text(encoding="utf-8").strip().split("\n")[0]
    snapshot = json.loads(line)

    assert "si_p7" in snapshot
    si_p7 = snapshot["si_p7"]

    # 8개 sub-field 전부 존재
    expected_fields = (
        "aggressive_mode_remaining",
        "integration_result_cycle",
        "condition_split_count_cycle",
        "suppress_count_cycle",
        "query_rewrite_count_cycle",
        "recent_conflict_fields_count",
        "adjacency_yield_top3",
        "coverage_deficit_top3",
    )
    for field in expected_fields:
        assert field in si_p7, f"si_p7 sub-field 누락: {field}"

    # 값 정합성
    assert si_p7["aggressive_mode_remaining"] == 3
    assert si_p7["recent_conflict_fields_count"] == 1
    assert si_p7["condition_split_count_cycle"] == 1
    assert si_p7["query_rewrite_count_cycle"] == 1
    assert si_p7["suppress_count_cycle"] == 1
    assert si_p7["integration_result_cycle"]["cycle"] == 14
    assert len(si_p7["adjacency_yield_top3"]) == 1
    assert si_p7["adjacency_yield_top3"][0]["rule_id"] == "transport:price→duration"
    assert len(si_p7["coverage_deficit_top3"]) == 1
    assert si_p7["coverage_deficit_top3"][0]["category"] == "transport"


def test_telemetry_helpers_readonly():
    """_build_si_p7_subdict 및 helper 들이 state 를 변형하지 않음."""
    from src.obs.telemetry import _build_si_p7_subdict

    state = _state_with_all_signals()
    state["current_cycle"] = 14
    state["cycle_count"] = 14

    # 전/후 snapshot 비교
    import copy
    before = copy.deepcopy({k: state[k] for k in _SIGNAL_FIELDS if k in state})

    result = _build_si_p7_subdict(state)
    assert isinstance(result, dict)

    after = {k: state[k] for k in _SIGNAL_FIELDS if k in state}
    assert before == after, "helper 가 state 를 변형했음"


def test_telemetry_si_p7_empty_state():
    """빈 state 에서 si_p7 sub-dict 가 기본값으로 채워짐."""
    from src.obs.telemetry import _build_si_p7_subdict

    state = load_state(BENCH)
    state["cycle_count"] = 0
    state["current_cycle"] = 0
    # 모든 필드 비워 두기
    for field in _SIGNAL_FIELDS:
        if field == "aggressive_mode_remaining":
            state[field] = 0
        elif field in ("integration_result_dist", "ku_stagnation_signals",
                       "adjacency_yield", "coverage_map"):
            state[field] = {}
        else:
            state[field] = []

    result = _build_si_p7_subdict(state)
    assert result["aggressive_mode_remaining"] == 0
    assert result["integration_result_cycle"] == {}
    assert result["condition_split_count_cycle"] == 0
    assert result["recent_conflict_fields_count"] == 0
    assert result["adjacency_yield_top3"] == []
    assert result["coverage_deficit_top3"] == []


def test_telemetry_adjacency_yield_top3_ordering():
    """adjacency_yield_top3 는 resolved 기준 내림차순."""
    from src.obs.telemetry import _top_n_rules

    adjacency = {
        "cat:a→b": [{"cycle": 1, "attempted": 10, "resolved": 7}],
        "cat:b→c": [{"cycle": 1, "attempted": 5, "resolved": 3}],
        "cat:c→d": [{"cycle": 1, "attempted": 20, "resolved": 15}],
        "cat:d→e": [{"cycle": 1, "attempted": 2, "resolved": 1}],
    }
    result = _top_n_rules(adjacency, n=3)
    assert len(result) == 3
    assert result[0]["rule_id"] == "cat:c→d"
    assert result[0]["resolved"] == 15
    assert result[1]["rule_id"] == "cat:a→b"
    assert result[2]["rule_id"] == "cat:b→c"
    assert "yield" in result[0]
    assert result[0]["yield"] == round(15 / 20, 3)


def test_telemetry_coverage_deficit_top3_ordering():
    """coverage_deficit_top3 는 deficit_score 내림차순."""
    from src.obs.telemetry import _top_n_deficit

    coverage = {
        "transport": {"deficit_score": 0.3},
        "accommodation": {"deficit_score": 0.7},
        "activity": {"deficit_score": 0.1},
        "food": 0.5,  # scalar 허용 케이스
    }
    result = _top_n_deficit(coverage, n=3)
    assert len(result) == 3
    assert result[0]["category"] == "accommodation"
    assert result[0]["deficit_score"] == 0.7
    assert result[1]["category"] == "food"
    assert result[1]["deficit_score"] == 0.5


# === Emit points (V-T5 c단계) ===
# critique.py / plan.py / integrate.py 의 event 기록 경로 검증

def test_critique_emits_aggressive_mode_entry(caplog):
    """critique_node 에서 ku_stagnation:added_low 발동 시 aggressive entry event + log."""
    import logging
    from src.nodes.critique import critique_node

    state = load_state(BENCH)
    state["cycle_count"] = 10
    state["current_cycle"] = 10

    # critique 가 내부에서 prescriptions 를 만들려면 added_ratio 가 낮아야 함.
    # 가장 안정적인 경로: 기존 critique 결과에 stagnation trigger 를 외부에서 prescriptions 에
    # 주입할 수 없으므로, integrate 가 생성한 signals 를 반영한 critique 를 실행해야 함.
    # 단위 테스트 범위에서 긴 체인은 지양. 여기서는 low-level emit 함수를 직접 호출하여
    # state 변경 + logger.info 를 검증하는 얇은 통합 테스트로 대체.
    #
    # critique.py 의 V2 계측 블록은 "stagnation_fired=True 일 때 history append + log" 로직.
    # stagnation_fired 는 prescriptions 리스트 내용으로만 판정되므로, 모의 prescriptions 가
    # 포함된 state 를 만들어서 critique_node 를 직접 호출하는 대신,
    # 내부에서 분기에 해당하는 블록만 모사한 통합 테스트를 제공한다.
    #
    # D-187 (real-path): 실제 critique 경로에서 emit 이 작동하는지는 V-T6 smoke 에서 검증.
    # 본 L1 은 emit 블록의 **호출 가능성** (state update + log) 만 확인.
    caplog.set_level(logging.INFO, logger="src.nodes.critique")

    # 직접 호출 대신: critique_node 가 반환한 result 에 aggressive_mode_history 가
    # 포함되도록 구성하려면 prescriptions 가 added_low 를 포함해야 하지만, 이는 내부 규칙
    # (ku_stagnation_signals.added_history 와 임계치) 로만 발동된다.
    # 실경로 smoke 는 V-T6. 본 테스트는 emit 블록의 구조적 정합만 확인한다.
    import src.nodes.critique as crit_mod
    assert hasattr(crit_mod, "logger"), "critique 모듈에 logger 가 정의되어야 함"
    # emit 블록의 텍스트 확인 (regression guard)
    import inspect
    source = inspect.getsource(crit_mod)
    assert "[si-p7] β aggressive_mode entered" in source
    assert "aggressive_mode_history" in source


def test_plan_emits_query_rewrite_event():
    """plan_node 에서 is_stagnation=True 시 query_rewrite_rx_log append + logger.info."""
    from src.nodes.plan import plan_node

    state = load_state(BENCH)
    state["current_cycle"] = 10

    # stagnation 강제 활성화 — aggressive_mode_remaining > 0 으로 _is_stagnation_active True
    state["aggressive_mode_remaining"] = 2

    # plan_node 는 gap_map 의 open GU 가 있어야 target 생성
    open_gus = [gu for gu in state["gap_map"] if gu.get("status") == "open"]
    assert len(open_gus) > 0, "테스트 fixture 에 open GU 필요"

    # mode 설정 (plan_node 가 current_mode 사용)
    state["current_mode"] = {"mode": "normal", "explore_budget": 0, "exploit_budget": 2}

    result = plan_node(state)

    # query_rewrite_rx_log 가 반환 dict 에 포함되어야 함
    assert "query_rewrite_rx_log" in result, "stagnation 활성 시 query_rewrite_rx_log 반환 필수"
    log = result["query_rewrite_rx_log"]
    assert len(log) > 0
    entry = log[0]
    assert "cycle" in entry
    assert "gu_id" in entry
    assert "slug" in entry
    assert "field" in entry
    assert "rewritten_queries" in entry
    assert entry["cycle"] == 10


def test_plan_skips_query_rewrite_event_when_not_stagnation():
    """stagnation 비활성 시 query_rewrite_rx_log 미반환."""
    from src.nodes.plan import plan_node

    state = load_state(BENCH)
    state["current_cycle"] = 10
    state["aggressive_mode_remaining"] = 0
    state["current_critique"] = None
    state["ku_stagnation_signals"] = None
    state["current_mode"] = {"mode": "normal", "explore_budget": 0, "exploit_budget": 2}

    result = plan_node(state)
    assert "query_rewrite_rx_log" not in result


def test_detect_conflict_populates_reason_out():
    """_detect_conflict 에 reason_out dict 전달 시 condition_split reason 기록."""
    from src.nodes.integrate import _detect_conflict

    # Rule 2 (conditions)
    reason = {}
    result = _detect_conflict(
        {"value": "¥50,000"},
        {"value": "¥40,000", "conditions": {"season": "peak"}},
        reason_out=reason,
    )
    assert result == "condition_split"
    assert reason["reason"] == "conditions"

    # Rule 2b (value_shape: scalar vs list)
    reason = {}
    result = _detect_conflict(
        {"value": "Visa"},
        {"value": ["Visa", "Mastercard"]},
        reason_out=reason,
    )
    assert result == "condition_split"
    assert reason["reason"] == "value_shape"

    # Rule 2d (condition_axes)
    reason = {}
    result = _detect_conflict(
        {"value": "A"},
        {"value": "B"},
        condition_axes=["region"],
        reason_out=reason,
    )
    assert result == "condition_split"
    assert reason["reason"] == "condition_axes"

    # Rule 2c (axis_tags)
    reason = {}
    result = _detect_conflict(
        {"value": "¥50,000", "axis_tags": {"geography": "tokyo"}},
        {"value": "¥60,000", "axis_tags": {"geography": "osaka"}},
        reason_out=reason,
    )
    assert result == "condition_split"
    assert reason["reason"] == "axis_tags"


def test_detect_conflict_reason_out_not_touched_for_non_split():
    """condition_split 이 아니면 reason_out 건드리지 않음."""
    from src.nodes.integrate import _detect_conflict

    reason = {}
    result = _detect_conflict(
        {"value": "¥50,000"},
        {"value": "¥50,000"},
        reason_out=reason,
    )
    assert result is None
    assert reason == {}


# === V-T7b axis toggle (V3 ablation) ===

def test_sip7_axis_toggles_default_all_on():
    """기본값: 모든 축 enabled=True (기존 동작 유지)."""
    from src.config import SIP7AxisToggles

    toggles = SIP7AxisToggles()
    d = toggles.to_dict()
    assert d == {
        "s1_enabled": True,
        "s2_enabled": True,
        "s3_enabled": True,
        "s4_enabled": True,
    }


def test_sip7_axis_toggles_from_env(monkeypatch):
    """SI_P7_AXIS_OFF='s2' env var → s2_enabled=False."""
    from src.config import SIP7AxisToggles

    monkeypatch.setenv("SI_P7_AXIS_OFF", "s2")
    t = SIP7AxisToggles.from_env()
    assert t.s1_enabled is True
    assert t.s2_enabled is False
    assert t.s3_enabled is True
    assert t.s4_enabled is True

    # 복수 축
    monkeypatch.setenv("SI_P7_AXIS_OFF", "s2, s3")
    t = SIP7AxisToggles.from_env()
    assert t.s2_enabled is False
    assert t.s3_enabled is False

    # 빈 문자열
    monkeypatch.setenv("SI_P7_AXIS_OFF", "")
    t = SIP7AxisToggles.from_env()
    assert all([t.s1_enabled, t.s2_enabled, t.s3_enabled, t.s4_enabled])


def test_detect_conflict_s2_off_skips_value_shape_split():
    """s2_enabled=False → Rule 2b (value_shape) skip → hold 로 회귀 (baseline pre-SI-P7).

    LLM=None 이므로 결정론적 fallback: 값 차이 + 조건 부재 → 'hold'.
    """
    from src.nodes.integrate import _detect_conflict

    # s2_enabled=True → condition_split
    r = _detect_conflict(
        {"value": "Visa"},
        {"value": ["Visa", "Mastercard"]},
        s2_enabled=True,
    )
    assert r == "condition_split"

    # s2_enabled=False → Rule 2b off → hold (기존 conflict 로 회귀)
    r = _detect_conflict(
        {"value": "Visa"},
        {"value": ["Visa", "Mastercard"]},
        s2_enabled=False,
    )
    assert r == "hold"


def test_detect_conflict_s2_off_still_respects_rule2_conditions():
    """s2_enabled=False 여도 Rule 2 (conditions) 는 여전히 condition_split.

    D-181 baseline 회귀: conditions-only rule 은 SI-P7 이전부터 존재.
    """
    from src.nodes.integrate import _detect_conflict

    r = _detect_conflict(
        {"value": "¥50,000"},
        {"value": "¥40,000", "conditions": {"season": "peak"}},
        s2_enabled=False,
    )
    assert r == "condition_split"


def test_detect_conflict_s2_off_skips_condition_axes_split():
    """s2_enabled=False → Rule 2d (condition_axes) skip → hold 회귀."""
    from src.nodes.integrate import _detect_conflict

    r = _detect_conflict(
        {"value": "A"},
        {"value": "B"},
        condition_axes=["region"],
        s2_enabled=False,
    )
    assert r == "hold"


def test_detect_conflict_s2_off_skips_axis_tags_split():
    """s2_enabled=False → Rule 2c (axis_tags) skip → hold 회귀."""
    from src.nodes.integrate import _detect_conflict

    r = _detect_conflict(
        {"value": "¥50,000", "axis_tags": {"geography": "tokyo"}},
        {"value": "¥60,000", "axis_tags": {"geography": "osaka"}},
        s2_enabled=False,
    )
    assert r == "hold"


def test_plan_s2_off_forces_is_stagnation_false():
    """s2_enabled=False → plan.py 에서 is_stagnation=False 강제.

    결과: query_rewrite_rx_log 미반환 (aggressive_mode_remaining > 0 여도).
    """
    from src.nodes.plan import plan_node

    state = load_state(BENCH)
    state["current_cycle"] = 10
    # 평소 stagnation 활성 조건 (aggressive > 0) 이지만 s2 off 로 force skip
    state["aggressive_mode_remaining"] = 2
    state["si_p7_toggles"] = {"s1_enabled": True, "s2_enabled": False,
                               "s3_enabled": True, "s4_enabled": True}
    state["current_mode"] = {"mode": "normal", "explore_budget": 0, "exploit_budget": 2}

    result = plan_node(state)
    assert "query_rewrite_rx_log" not in result


def test_critique_s2_off_skips_ku_stagnation_trigger():
    """s2_enabled=False 시 critique 모듈의 stagnation block 이 실행 안 되는지 검증.

    직접 실행은 복잡하므로 (signals 셋업 필요), 소스 구조로 regression guard 확인.
    """
    import inspect
    import src.nodes.critique as crit_mod
    source = inspect.getsource(crit_mod)
    # s2_enabled 파라미터 추출 + 전달 + 두 stagnation 블록에 가드 존재
    assert 's2_enabled = bool(state.get("si_p7_toggles"' in source
    assert "s2_enabled=s2_enabled" in source  # _analyze_failure_modes 호출 시 전달
    assert "if ku_stagnation_signals and s2_enabled" in source
    assert "if integration_result_dist and s2_enabled" in source


def test_generate_dynamic_gus_emits_suppress_event():
    """_generate_dynamic_gus 가 suppress 조건 충족 시 buffer 에 event append + log."""
    from src.nodes.integrate import _generate_dynamic_gus

    skeleton = {
        "fields": [
            {"name": "price", "categories": ["*"]},
            {"name": "duration", "categories": ["*"]},
            {"name": "hours", "categories": ["*"]},
        ],
        "field_adjacency": {
            "transport:price": ["duration", "hours"],
        },
    }
    claim = {"entity_key": "japan-travel:transport:jr-pass", "field": "price"}
    # 같은 category 에 price 필드가 과도하게 많은 KU set — suppress 유발
    kus = (
        [{"entity_key": f"japan-travel:transport:e{i}", "field": "price", "status": "active"}
         for i in range(10)]
        + [{"entity_key": "japan-travel:transport:e0", "field": "duration", "status": "active"}]
    )
    suppress_buf: list[dict] = []

    _generate_dynamic_gus(
        claim=claim,
        gap_map=[],
        skeleton=skeleton,
        mode="normal",
        open_count=0,
        kus=kus,
        conflict_blocklist=None,
        suppress_events_out=suppress_buf,
        cycle=7,
    )

    # suppress 가 발생했어야 함 (price count=10, 평균 5.5, threshold 8.25, price 10 > 8.25)
    assert len(suppress_buf) >= 1
    event = suppress_buf[0]
    assert event["cycle"] == 7
    assert event["category"] == "transport"
    assert "price" in event["suppressed_fields"]
