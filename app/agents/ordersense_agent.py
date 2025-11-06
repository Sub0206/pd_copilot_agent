from agents import function_tool
from typing import Optional, Dict
import requests
import json
from datetime import datetime
import os

# Base URL for API endpoints
BASE_API_URL = os.getenv("DATABASE_API_URL", "http://localhost:8013/PD/mvc")

# Available endpoints
ENDPOINTS = {
    "dependency_vtag": "/getViewsDependencyByVTag",
    "dependency_itag": "/getViewsDependencyByITag",
    "version_dependency_vtag": "/getViewsVersionDependencyByVTag",
    "version_dependency_itag": "/getViewsVersionDependencyByITag"
}


def determine_endpoint(iTag: Optional[str], vTag: Optional[str], check_version: bool = False) -> str:
    """
    Determine which endpoint to use based on provided parameters
    
    Args:
        iTag: Interface tag (optional)
        vTag: View tag (optional)
        check_version: If True, use version dependency endpoints
    
    Returns:
        Endpoint path
    """
    if check_version:
        # Version dependency endpoints
        if vTag:
            return ENDPOINTS["version_dependency_vtag"]
        elif iTag:
            return ENDPOINTS["version_dependency_itag"]
    else:
        # Regular dependency endpoints
        if vTag:
            return ENDPOINTS["dependency_vtag"]
        elif iTag:
            return ENDPOINTS["dependency_itag"]
    
    raise ValueError("Either iTag or vTag must be provided")


def build_api_url(pt_id: str, iTag: Optional[str] = None, vTag: Optional[str] = None, 
                  check_version: bool = False) -> str:
    """
    Build the complete API URL with parameters
    
    Args:
        pt_id: Product type ID (required)
        iTag: Interface tag (optional)
        vTag: View tag (optional)
        check_version: If True, use version dependency endpoints
    
    Returns:
        Complete API URL with query parameters
    """
    endpoint = determine_endpoint(iTag, vTag, check_version)
    base_url = f"{BASE_API_URL}{endpoint}"
    
    params = [f"pt_id={pt_id}"]
    
    if vTag:
        params.append(f"vTag={vTag}")
    elif iTag:
        params.append(f"iTag={iTag}")
    
    return f"{base_url}?{'&'.join(params)}"


def fetch_database_info(api_url: str) -> Dict:
    """Fetch view items data from API"""
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return {"status": "success", "data": response.json(), "timestamp": datetime.now().isoformat()}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error_message": str(e), "timestamp": datetime.now().isoformat()}


def parse_database_info(raw_data: str, endpoint_type: str) -> Dict:
    """
    Parse raw database data into structured view items
    
    Args:
        raw_data: Raw JSON response from API
        endpoint_type: Type of endpoint used ('vtag' or 'itag')
    
    Returns:
        Parsed data structure
    """
    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        if "data" in data:
            data = data["data"]
        
        parsed_views = []
        total_items = 0
        
        # Handle ViewHierarchyVO (vTag endpoints)
        if endpoint_type == "vtag":
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
                
                parsed_views.append({
                    "view_name": view.get("view_name", ""),
                    "items": view_items
                })
        
        # Handle InterfacesHierarchyVO (iTag endpoints)
        elif endpoint_type == "itag":
            for interface in data.get("interfaces", []):
                for view in interface.get("views", []):
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
                            "view_name": view.get("view_name", ""),
                            "interface_name": interface.get("interface_name", "")
                        })
                        total_items += 1
                    
                    parsed_views.append({
                        "view_name": view.get("view_name", ""),
                        "interface_name": interface.get("interface_name", ""),
                        "items": view_items
                    })
        
        return {
            "status": "success",
            "parsed_views": parsed_views,
            "total_items": total_items,
            "endpoint_type": endpoint_type
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def analyze_view_items(parsed_data: str) -> Dict:
    """Identify tab order violations where dependencies appear after current items"""
    try:
        data = json.loads(parsed_data) if isinstance(parsed_data, str) else parsed_data
        violations = []
        item_lookup = {}
        
        # Build lookup table for all items
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                item_lookup[item["question_id"]] = item
        
        # Analyze each item for violations
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                current_qid = item["question_id"]
                current_tab = item["tab_order"]
                current_entity = item["entity_id"]
                view_name = item["view_name"]
                
                # Check each dependency
                for dep_qid in item.get("dependencies", []):
                    # Handle versioned dependencies (e.g., question_id_v1)
                    base_dep_qid = dep_qid.split("_v")[0]
                    dep_item = item_lookup.get(dep_qid) or item_lookup.get(base_dep_qid)
                    
                    if not dep_item:
                        # Dependency not found in current view
                        continue
                    
                    # Only check dependencies within same entity
                    if current_entity != dep_item["entity_id"]:
                        continue
                    
                    dep_tab = dep_item["tab_order"]
                    
                    # Violation: dependency appears after current item
                    if dep_tab > current_tab:
                        violation = {
                            "current_question_id": current_qid,
                            "current_tab": current_tab,
                            "dependency_question_id": dep_qid,
                            "dependency_tab": dep_tab,
                            "entity_id": current_entity,
                            "view_name": view_name,
                            "recommended_tab": dep_tab + 1
                        }
                        
                        # Add interface name if available (from iTag endpoints)
                        if "interface_name" in item:
                            violation["interface_name"] = item["interface_name"]
                        
                        violations.append(violation)
        
        return {
            "status": "success",
            "violations": violations,
            "total_violations": len(violations)
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def generate_report(analysis_data: str) -> Dict:
    """Generate validation report with violations and recommendations"""
    try:
        data = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
        violations = data.get("violations", [])
        
        # Group violations by view (and interface if available)
        violations_by_view = {}
        violations_by_interface = {}
        
        for v in violations:
            view = v["view_name"]
            if view not in violations_by_view:
                violations_by_view[view] = []
            violations_by_view[view].append(v)
            
            # Group by interface if available
            if "interface_name" in v:
                interface = v["interface_name"]
                if interface not in violations_by_interface:
                    violations_by_interface[interface] = []
                violations_by_interface[interface].append(v)
        
        # Generate recommendations
        recommendations = []
        for v in violations:
            rec = f"Move {v['current_question_id']} from Tab {v['current_tab']} to Tab {v['recommended_tab']} or later"
            if "interface_name" in v:
                rec += f" (Interface: {v['interface_name']})"
            recommendations.append(rec)
        
        # Create summary
        if violations_by_interface:
            summary = (f"Found {len(violations)} tab order violation(s) across "
                      f"{len(violations_by_view)} view(s) in {len(violations_by_interface)} interface(s)")
        else:
            summary = f"Found {len(violations)} tab order violation(s) across {len(violations_by_view)} view(s)"
        
        report = {
            "status": "success",
            "summary": summary,
            "violations_by_view": violations_by_view,
            "recommendations": recommendations,
            "total_violations": len(violations),
            "report_generated_at": datetime.now().isoformat()
        }
        
        # Add interface grouping if available
        if violations_by_interface:
            report["violations_by_interface"] = violations_by_interface
        
        return report
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@function_tool
def run_ordersense_validation(
    pt_id: Optional[str] = None,
    iTag: Optional[str] = None,
    vTag: Optional[str] = None,
    check_version: bool = False
) -> Dict:
    """
    Validate tab orders for view items. Checks if questions appear before their dependencies.
    
    Args:
        pt_id: Product type ID (required)
        iTag: Interface tag (optional, mutually exclusive with vTag)
        vTag: View tag (optional, mutually exclusive with iTag)
        check_version: If True, uses version dependency endpoints (default: False)
    
    Returns:
        Validation report with violations and recommendations
    
    Endpoints used:
        - If vTag provided: /getViewsDependencyByVTag or /getViewsVersionDependencyByVTag
        - If iTag provided: /getViewsDependencyByITag or /getViewsVersionDependencyByITag
    """
    try:
        # Validate required parameters
        if not pt_id:
            return {"status": "error", "error_message": "pt_id is required"}
        
        if not iTag and not vTag:
            return {"status": "error", "error_message": "Either iTag or vTag is required"}
        
        if iTag and vTag:
            return {"status": "error", "error_message": "Provide either iTag or vTag, not both"}
        
        # Determine endpoint type
        endpoint_type = "vtag" if vTag else "itag"
        
        # Build API URL
        api_url = build_api_url(pt_id, iTag, vTag, check_version)
        
        # Fetch data from API
        raw_data = fetch_database_info(api_url)
        if raw_data.get("status") == "error":
            return raw_data
        
        # Parse the response
        parsed_data = parse_database_info(json.dumps(raw_data), endpoint_type)
        if parsed_data.get("status") == "error":
            return parsed_data
        
        # Analyze for violations
        analysis_data = analyze_view_items(json.dumps(parsed_data))
        if analysis_data.get("status") == "error":
            return analysis_data
        
        # Generate report
        report = generate_report(json.dumps(analysis_data))
        if report.get("status") == "error":
            return report
        
        # Add request metadata
        report["request_parameters"] = {
            "pt_id": pt_id,
            "iTag": iTag,
            "vTag": vTag,
            "check_version": check_version,
            "endpoint_used": endpoint_type,
            "api_url": api_url
        }
        
        return report
        
    except Exception as e:
        return {"status": "error", "error_message": f"Validation failed: {str(e)}"}