from agents import function_tool
from typing import Optional, Dict
import requests
import json
from datetime import datetime
import os

DEFAULT_API_URL = os.getenv("DATABASE_API_URL", "http://localhost:8013/PD/mvc/getViewsHierarchyByITagVTag")


@function_tool
def fetch_database_info(api_url: str) -> Dict:
    """Fetch view items data from API"""
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return {"status": "success", "data": response.json(), "timestamp": datetime.now().isoformat()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": str(e), "timestamp": datetime.now().isoformat()}


@function_tool
def parse_database_info(raw_data: str) -> Dict:
    """Parse raw database data into structured view items"""
    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        if "data" in data:
            data = data["data"]
        
        parsed_views = []
        total_items = 0
        
        for view in data.get("views", []):
            view_items = []
            for item in view.get("items", []):
                question_id = item.get("question_id", "")
                parts = question_id.split("_")
                entity_id = parts[1] if len(parts) > 1 else "unknown"
                
                view_items.append({
                    "question_id": question_id,
                    "entity_id": entity_id,
                    "tab_order": item.get("tab_order", 0),
                    "dependencies": item.get("dependencies", []),
                    "view_name": view.get("view_name", "")
                })
                total_items += 1
            
            parsed_views.append({"view_name": view.get("view_name", ""), "items": view_items})
        
        return {
            "status": "success",
            "parsed_views": parsed_views,
            "total_items": total_items
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@function_tool
def analyze_view_items(parsed_data: str) -> Dict:
    """Identify tab order violations where dependencies appear after current items"""
    try:
        data = json.loads(parsed_data) if isinstance(parsed_data, str) else parsed_data
        violations = []
        item_lookup = {}
        
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                item_lookup[item["question_id"]] = item
        
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                current_qid = item["question_id"]
                current_tab = item["tab_order"]
                current_entity = item["entity_id"]
                view_name = item["view_name"]
                
                for dep_qid in item.get("dependencies", []):
                    base_dep_qid = dep_qid.split("_v")[0]
                    dep_item = item_lookup.get(dep_qid) or item_lookup.get(base_dep_qid)
                    
                    if not dep_item or current_entity != dep_item["entity_id"]:
                        continue
                    
                    dep_tab = dep_item["tab_order"]
                    
                    if dep_tab > current_tab:
                        violations.append({
                            "current_question_id": current_qid,
                            "current_tab": current_tab,
                            "dependency_question_id": dep_qid,
                            "dependency_tab": dep_tab,
                            "entity_id": current_entity,
                            "view_name": view_name,
                            "recommended_tab": dep_tab + 1
                        })
        
        return {
            "status": "success",
            "violations": violations,
            "total_violations": len(violations)
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@function_tool
def generate_report(analysis_data: str) -> Dict:
    """Generate validation report with violations and recommendations"""
    try:
        data = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
        violations = data.get("violations", [])
        
        violations_by_view = {}
        for v in violations:
            view = v["view_name"]
            if view not in violations_by_view:
                violations_by_view[view] = []
            violations_by_view[view].append(v)
        
        recommendations = []
        for view, view_violations in violations_by_view.items():
            for v in view_violations:
                recommendations.append(
                    f"Move {v['current_question_id']} from Tab {v['current_tab']} to Tab {v['recommended_tab']} or later"
                )
        
        summary = f"Found {len(violations)} tab order violation(s) across {len(violations_by_view)} view(s)"
        
        return {
            "status": "success",
            "summary": summary,
            "violations_by_view": violations_by_view,
            "recommendations": recommendations,
            "total_violations": len(violations),
            "report_generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@function_tool
def run_ordersense_validation(
    pt_id: Optional[str] = None,
    iTag: Optional[str] = None,
    vTag: Optional[str] = None
) -> Dict:
    """
    Validate tab orders for view items. Checks if questions appear before their dependencies.
    Requires pt_id and either iTag or vTag.
    """
    try:
        base_url = DEFAULT_API_URL
        
        if not pt_id:
            return {"status": "error", "error_message": "pt_id is required"}
        
        if not iTag and not vTag:
            return {"status": "error", "error_message": "Either iTag or vTag is required"}
        
        params = [f"pt_id={pt_id}"]
        if iTag:
            params.append(f"iTag={iTag}")
        if vTag:
            params.append(f"vTag={vTag}")
        
        api_url = f"{base_url}?{'&'.join(params)}"
        
        raw_data = fetch_database_info.invoke(api_url)
        if raw_data.get("status") == "error":
            return raw_data
        
        parsed_data = parse_database_info.invoke(json.dumps(raw_data))
        if parsed_data.get("status") == "error":
            return parsed_data
        
        analysis_data = analyze_view_items.invoke(json.dumps(parsed_data))
        if analysis_data.get("status") == "error":
            return analysis_data
        
        report = generate_report.invoke(json.dumps(analysis_data))
        if report.get("status") == "error":
            return report
        
        report["request_parameters"] = {
            "pt_id": pt_id,
            "iTag": iTag,
            "vTag": vTag
        }
        
        return report
        
    except Exception as e:
        return {"status": "error", "error_message": f"Validation failed: {str(e)}"}
