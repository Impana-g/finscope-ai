# Tests for teammate's code
# Run with: pytest tests/test_teammate.py -v

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# ══════════════════════════════════════════════════════
# BASIC API TESTS
# ══════════════════════════════════════════════════════

def test_home_endpoint():
    """Home endpoint should return 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "FinScope AI"
    assert response.json()["status"] == "running"
    print("✅ Home endpoint working")


def test_health_endpoint():
    """Health check should return ok"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ Health endpoint working")


# ══════════════════════════════════════════════════════
# SESSION API TESTS
# ══════════════════════════════════════════════════════

def test_get_session_not_found():
    """Fake session ID should return 404"""
    response = client.get("/sessions/fake-session-id-99999")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "not_found"
    print("✅ Session not found returns 404")


def test_approve_session_not_found():
    """Approving fake session should return 404"""
    response = client.patch("/sessions/fake-session-id/approve")
    assert response.status_code == 404
    print("✅ Approve not found returns 404")


def test_get_report_not_found():
    """Report for fake session should return 404"""
    response = client.get("/sessions/fake-id/report")
    assert response.status_code == 404
    print("✅ Report not found returns 404")


def test_delete_session_not_found():
    """Deleting fake session should return 404"""
    response = client.delete("/sessions/fake-session-id")
    assert response.status_code == 404
    print("✅ Delete not found returns 404")


# ══════════════════════════════════════════════════════
# REPORT API TESTS
# ══════════════════════════════════════════════════════

def test_get_report_by_id_not_found():
    """Fake report ID should return 404"""
    response = client.get("/reports/fake-report-id")
    assert response.status_code == 404
    print("✅ Report by ID not found returns 404")


def test_export_invalid_format():
    """Invalid export format should return 400"""
    response = client.get("/reports/some-id/export?format=excel")
    assert response.status_code in [400, 404]
    print("✅ Invalid export format returns error")


# ══════════════════════════════════════════════════════
# CALCULATOR TESTS
# ══════════════════════════════════════════════════════

def test_growth_going_up():
    from src.tools.calculator import calculate_growth
    result = calculate_growth(100, 120)
    assert result["success"] == True
    assert result["growth_pct"] == 20.0
    assert result["direction"] == "up"
    print("✅ Growth up works")


def test_growth_going_down():
    from src.tools.calculator import calculate_growth
    result = calculate_growth(100, 80)
    assert result["success"] == True
    assert result["growth_pct"] == -20.0
    assert result["direction"] == "down"
    print("✅ Growth down works")


def test_growth_zero_old_value():
    from src.tools.calculator import calculate_growth
    result = calculate_growth(0, 100)
    assert result["success"] == False
    print("✅ Zero division handled")


def test_margin_excellent():
    from src.tools.calculator import calculate_margin
    result = calculate_margin(25, 100)
    assert result["margin_pct"] == 25.0
    assert result["rating"] == "excellent"
    print("✅ Excellent margin works")


def test_margin_zero_revenue():
    from src.tools.calculator import calculate_margin
    result = calculate_margin(20, 0)
    assert result["success"] == False
    print("✅ Zero revenue handled")


def test_pe_overvalued():
    from src.tools.calculator import compare_pe_ratio
    result = compare_pe_ratio(30, 20)
    assert result["verdict"] == "overvalued"
    print("✅ Overvalued PE works")


def test_pe_undervalued():
    from src.tools.calculator import compare_pe_ratio
    result = compare_pe_ratio(10, 20)
    assert result["verdict"] == "undervalued"
    print("✅ Undervalued PE works")


def test_pe_fairly_valued():
    from src.tools.calculator import compare_pe_ratio
    result = compare_pe_ratio(21, 20)
    assert result["verdict"] == "fairly valued"
    print("✅ Fairly valued PE works")


def test_cagr_calculation():
    from src.tools.calculator import calculate_cagr
    result = calculate_cagr(100, 200, 5)
    assert result["success"] == True
    assert result["cagr_pct"] == 14.87
    print("✅ CAGR calculation works")


def test_cagr_zero_start():
    from src.tools.calculator import calculate_cagr
    result = calculate_cagr(0, 200, 5)
    assert result["success"] == False
    print("✅ Zero start value handled")


# ══════════════════════════════════════════════════════
# FINANCIAL DATA TESTS
# ══════════════════════════════════════════════════════

def test_ticker_infosys():
    from src.tools.financial_data import get_company_ticker
    assert get_company_ticker("Infosys") == "INFY"
    print("✅ Infosys ticker works")


def test_ticker_sun_pharma():
    from src.tools.financial_data import get_company_ticker
    assert get_company_ticker("Sun Pharma") == "SUNPHARMA"
    print("✅ Sun Pharma ticker works")


def test_ticker_unknown():
    from src.tools.financial_data import get_company_ticker
    result = get_company_ticker("RANDOMXYZ")
    assert result == "RANDOMXYZ"
    print("✅ Unknown ticker returned as-is")


def test_format_billions():
    from src.tools.financial_data import format_number
    result = format_number(82_000_000_000)
    assert "B" in result
    print("✅ Billion format works")


def test_format_trillions():
    from src.tools.financial_data import format_number
    result = format_number(2_000_000_000_000)
    assert "T" in result
    print("✅ Trillion format works")


def test_format_none():
    from src.tools.financial_data import format_number
    result = format_number(None)
    assert result == "N/A"
    print("✅ None value handled")


# ══════════════════════════════════════════════════════
# SCHEMA TESTS
# ══════════════════════════════════════════════════════

def test_valid_query_schema():
    from src.api.schemas import QueryRequest
    req = QueryRequest(
        query="Analyze Infosys financial performance 2025",
        user_id="user123",
        depth="standard"
    )
    assert req.depth == "standard"
    print("✅ Valid query schema works")


def test_short_query_rejected():
    from src.api.schemas import QueryRequest
    try:
        QueryRequest(query="Hi", user_id="u1")
        assert False, "Should have raised error"
    except Exception:
        print("✅ Short query correctly rejected")


def test_empty_user_id_rejected():
    from src.api.schemas import QueryRequest
    try:
        QueryRequest(
            query="Analyze Infosys financial results 2025",
            user_id="   "
        )
        assert False, "Should have raised error"
    except Exception:
        print("✅ Empty user_id correctly rejected")
