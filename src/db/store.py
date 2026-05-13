from typing import Dict, Any

sessions_store: Dict[str, Dict[str, Any]] = {}
steps_store: Dict[str, list] = {}
reports_store: Dict[str, Dict[str, Any]] = {}
session_to_report: Dict[str, str] = {}