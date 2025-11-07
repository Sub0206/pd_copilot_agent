from agents import function_tool
from typing import Optional, Dict, List
import requests
import json
from datetime import datetime
import os

# Default base URL for APIs
DEFAULT_BASE_URL = os.getenv("DATABASE_API_URL", "http://localhost:8013/PD/mvc")


# ============================================================================
# API CLIENT FUNCTIONS
# ============================================================================

def fetch_views_dependency_by_vtag(api_url: str, pt_id: str, vtag: str) -> Dict:
    """Fetch view dependency data by vTag"""
    try:
        url = f"{api_url}/getViewsDependencyByVTag?pt_id={pt_id}&vTag={vtag}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "endpoint": "getViewsDependencyByVTag",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "endpoint": "getViewsDependencyByVTag",
            "timestamp": datetime.now().isoformat()
        }


def fetch_views_dependency_by_itag(api_url: str, pt_id: str, itag: str) -> Dict:
    """Fetch interface dependency data by iTag"""
    try:
        url = f"{api_url}/getViewsDependencyByITag?pt_id={pt_id}&iTag={itag}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "endpoint": "getViewsDependencyByITag",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "endpoint": "getViewsDependencyByITag",
            "timestamp": datetime.now().isoformat()
        }


def fetch_views_version_dependency_by_vtag(api_url: str, pt_id: str, vtag: str) -> Dict:
    """Fetch view version dependency data by vTag"""
    try:
        url = f"{api_url}/getViewsVersionDependencyByVTag?pt_id={pt_id}&vTag={vtag}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "endpoint": "getViewsVersionDependencyByVTag",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "endpoint": "getViewsVersionDependencyByVTag",
            "timestamp": datetime.now().isoformat()
        }


def fetch_views_version_dependency_by_itag(api_url: str, pt_id: str, itag: str) -> Dict:
    """Fetch interface version dependency data by iTag"""
    try:
        url = f"{api_url}/getViewsVersionDependencyByITag?pt_id={pt_id}&iTag={itag}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "endpoint": "getViewsVersionDependencyByITag",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "endpoint": "getViewsVersionDependencyByITag",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# DATA PARSING & PROCESSING
# ============================================================================

def parse_view_hierarchy(raw_data: Dict) -> Dict:
    """
    Parse view hierarchy data from API response
    
    Data format:
    {
        "views": [
            {
                "viewName": "polDT",
                "viewItems": {
                    "viewItem : Q_30004_163": [
                        {
                            "tabOrder": 168,
                            "primaryBTag": 30000,
                            "primarySeqNo": 563,
                            "primaryTabOrder": 0,
                            "qbtag": "30004",
                            "qseqNo": 163,
                            "presentationLiteral": "...",
                            "textualExpression": "...",
                            "vtag": "polDT",
                            "dtype": "V"
                        }
                    ]
                }
            }
        ]
    }
    """
    try:
        data = raw_data.get("data", raw_data)
        
        parsed_views = []
        total_items = 0
        total_dependencies = 0
        
        # Handle both direct views array and nested interfaces structure
        views_list = data.get("views", [])
        if not views_list:
            # Try interfaces structure
            interfaces = data.get("interfaces", [])
            for interface in interfaces:
                views_list.extend(interface.get("views", []))
        
        for view in views_list:
            view_name = view.get("viewName", view.get("view_name", "unknown"))
            view_items_dict = view.get("viewItems", {})
            
            parsed_items = []
            
            # viewItems is a dictionary where keys are "viewItem : Q_X_Y"
            # and values are arrays of dependency configurations
            for item_key, item_configs in view_items_dict.items():
                # Each item_configs is an array of configurations
                # (one per dependency/primary question combination)
                
                if not item_configs or len(item_configs) == 0:
                    continue
                
                # Get the base item info from first config
                first_config = item_configs[0]
                
                # Build question ID from qbtag and qseqNo
                qbtag = first_config.get("qbtag", "")
                qseq_no = first_config.get("qseqNo", 0)
                question_id = f"Q_{qbtag}_{qseq_no}"
                
                tab_order = first_config.get("tabOrder", 0)
                presentation_literal = first_config.get("presentationLiteral", "")
                
                # Collect all dependencies (one per configuration)
                dependencies = []
                for config in item_configs:
                    primary_btag = config.get("primaryBTag", 0)
                    primary_seq_no = config.get("primarySeqNo", 0)
                    primary_tab_order = config.get("primaryTabOrder", 0)
                    textual_expression = config.get("textualExpression", "")
                    dependency_action = config.get("dependencyAction", "")
                    dtype = config.get("dtype", "")
                    
                    # Skip if no primary question (primaryTabOrder = 0 usually means no dependency)
                    # BUT we should still include it for analysis
                    # Build primary question ID
                    primary_question_id = f"Q_{primary_btag}_{primary_seq_no}" if primary_btag and primary_seq_no else ""
                    
                    dependency = {
                        "primary_question_id": primary_question_id,
                        "primary_btag": str(primary_btag),
                        "primary_seq_no": str(primary_seq_no),
                        "primary_tab_order": primary_tab_order,
                        "textual_expression": textual_expression,
                        "dependency_action": dependency_action,
                        "dtype": dtype
                    }
                    
                    dependencies.append(dependency)
                    if primary_question_id:  # Count only real dependencies
                        total_dependencies += 1
                
                item = {
                    "question_id": question_id,
                    "qbtag": qbtag,
                    "qseq_no": qseq_no,
                    "tab_order": tab_order,
                    "presentation_literal": presentation_literal,
                    "view_name": view_name,
                    "dependencies": dependencies
                }
                
                parsed_items.append(item)
                total_items += 1
            
            parsed_views.append({
                "view_name": view_name,
                "items": parsed_items
            })
        
        return {
            "status": "success",
            "parsed_views": parsed_views,
            "total_items": total_items,
            "total_dependencies": total_dependencies,
            "total_views": len(parsed_views)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error_message": f"Parse error: {str(e)}",
            "traceback": traceback.format_exc()
        }


def analyze_dependencies(parsed_data: Dict) -> Dict:
    """
    Analyze dependencies and identify tab order violations
    
    CRITICAL LOGIC:
    - For each question with dependencies (primary questions)
    - Check if primaryTabOrder > current question's tabOrder
    - IF primaryTabOrder > tabOrder → VIOLATION (dependency comes after the question)
    - IF primaryTabOrder < tabOrder → CORRECT (dependency comes before)
    - IF primaryTabOrder = 0 → Usually means cross-entity or no ordering constraint
    
    Example VIOLATION:
    - Q_30004_396 (tab 4) depends on Q_30004_395 (primaryTabOrder 8)
    - 8 > 4 → VIOLATION! The dependency should come BEFORE
    """
    try:
        violations = []
        
        # Build lookup for all items by question_id
        item_lookup = {}
        for view in parsed_data.get("parsed_views", []):
            for item in view.get("items", []):
                item_lookup[item["question_id"]] = item
        
        # Analyze each item's dependencies
        for view in parsed_data.get("parsed_views", []):
            for item in view.get("items", []):
                current_qid = item["question_id"]
                current_tab = item["tab_order"]
                current_qbtag = item["qbtag"]
                view_name = item["view_name"]
                presentation_literal = item["presentation_literal"]
                
                # Process each dependency
                for dep in item.get("dependencies", []):
                    primary_qid = dep.get("primary_question_id", "")
                    primary_tab_order = dep.get("primary_tab_order", 0)
                    primary_btag = dep.get("primary_btag", "")
                    primary_seq_no = dep.get("primary_seq_no", "")
                    textual_expression = dep.get("textual_expression", "")
                    dtype = dep.get("dtype", "")
                    
                    # Skip if no primary question
                    if not primary_qid or primary_tab_order == 0:
                        continue
                    
                    # Check if same entity (qbtag should match primaryBTag)
                    # Only validate within same entity
                    if current_qbtag != primary_btag:
                        continue
                    
                    # THE CRITICAL CHECK: Is primary tab order AFTER current tab?
                    # This is the violation: dependency should come BEFORE, not AFTER
                    if primary_tab_order > current_tab:
                        # VIOLATION DETECTED!
                        violation = {
                            "view_name": view_name,
                            "current_question_id": current_qid,
                            "current_tab_order": current_tab,
                            "current_presentation": presentation_literal,
                            "primary_question_id": primary_qid,
                            "primary_tab_order": primary_tab_order,
                            "primary_btag": primary_btag,
                            "primary_seq_no": primary_seq_no,
                            "textual_expression": textual_expression,
                            "dependency_type": dtype,
                            "recommended_tab_order": primary_tab_order + 1,
                            "violation_reason": f"Primary question at tab {primary_tab_order} appears AFTER dependent question at tab {current_tab}"
                        }
                        violations.append(violation)
        
        return {
            "status": "success",
            "violations": violations,
            "total_violations": len(violations),
            "analysis_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error_message": f"Analysis error: {str(e)}",
            "traceback": traceback.format_exc()
        }


def generate_validation_report(analysis_data: Dict, request_params: Dict, parsed_data: Dict) -> Dict:
    """
    Generate comprehensive validation report
    Includes both main dependencies and version dependencies in same report
    """
    try:
        violations = analysis_data.get("violations", [])
        
        # Group violations by view
        violations_by_view = {}
        for v in violations:
            view = v["view_name"]
            if view not in violations_by_view:
                violations_by_view[view] = []
            violations_by_view[view].append(v)
        
        # Generate detailed recommendations
        recommendations = []
        for view_name, view_violations in violations_by_view.items():
            for v in view_violations:
                rec = {
                    "view": view_name,
                    "violation_type": "TAB_ORDER_VIOLATION",
                    "current_question_id": v["current_question_id"],
                    "current_tab_order": v["current_tab_order"],
                    "current_presentation": v["current_presentation"],
                    "primary_question_id": v["primary_question_id"],
                    "primary_tab_order": v["primary_tab_order"],
                    "primary_btag": v["primary_btag"],
                    "primary_seq_no": v["primary_seq_no"],
                    "dependency_type": v["dependency_type"],
                    "textual_expression": v["textual_expression"],
                    "recommended_action": f"Move {v['current_question_id']} from Tab {v['current_tab_order']} to Tab {v['recommended_tab_order']} or later",
                    "reason": v["violation_reason"],
                    "severity": "HIGH" if (v["primary_tab_order"] - v["current_tab_order"]) > 100 else "MEDIUM"
                }
                recommendations.append(rec)
        
        # Generate summary
        if violations:
            summary = f"⚠️ Found {len(violations)} tab order violation(s) across {len(violations_by_view)} view(s)"
            status = "violations_found"
        else:
            summary = "✅ No tab order violations found. All primary questions appear before their dependent questions."
            status = "valid"
        
        # Statistics
        stats = {
            "total_items_analyzed": parsed_data.get("total_items", 0),
            "total_dependencies_checked": parsed_data.get("total_dependencies", 0),
            "total_violations": len(violations),
            "affected_views": len(violations_by_view),
            "high_severity_violations": sum(1 for r in recommendations if r.get("severity") == "HIGH"),
            "medium_severity_violations": sum(1 for r in recommendations if r.get("severity") == "MEDIUM")
        }
        
        report = {
            "status": status,
            "summary": summary,
            "statistics": stats,
            "violations_by_view": violations_by_view,
            "recommendations": recommendations,
            "request_parameters": request_params,
            "report_generated_at": datetime.now().isoformat()
        }
        
        return report
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error_message": f"Report generation error: {str(e)}",
            "traceback": traceback.format_exc()
        }


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

@function_tool
def run_ordersense_validation(
    pt_id: Optional[str] = None,
    iTag: Optional[str] = None,
    vTag: Optional[str] = None,
    include_version_check: bool = False
) -> Dict:
    """
    Validate tab orders for view items with primary question dependency checking.
    
    VALIDATION LOGIC:
    - Checks if primary questions (dependencies) appear BEFORE dependent questions
    - VIOLATION: primaryTabOrder > current tabOrder (dependency comes after)
    - CORRECT: primaryTabOrder < current tabOrder (dependency comes before)
    
    Supports 4 API endpoints:
    1. getViewsDependencyByVTag (vTag required)
    2. getViewsDependencyByITag (iTag required)
    3. getViewsVersionDependencyByVTag (vTag + include_version_check=True)
    4. getViewsVersionDependencyByITag (iTag + include_version_check=True)
    
    Parameters:
    - pt_id: Product Type ID (required)
    - iTag: Interface Tag (required if vTag not provided)
    - vTag: View Tag (required if iTag not provided)
    - include_version_check: If True, uses version-aware endpoints
    
    Returns:
    - Validation report with violations and recommendations
    """
    try:
        base_url = DEFAULT_BASE_URL
        
        # Validate required parameters
        if not pt_id:
            return {
                "status": "error",
                "error_message": "pt_id is required"
            }
        
        if not iTag and not vTag:
            return {
                "status": "error",
                "error_message": "Either iTag or vTag is required"
            }
        
        # Build request parameters
        request_params = {
            "pt_id": pt_id,
            "iTag": iTag,
            "vTag": vTag,
            "include_version_check": include_version_check
        }
        
        # Step 1: Fetch data from appropriate API
        print(f"\n[OrderSense] Fetching data for pt_id={pt_id}, vTag={vTag}, iTag={iTag}, version_check={include_version_check}")
        
        if vTag:
            if include_version_check:
                raw_data = fetch_views_version_dependency_by_vtag(base_url, pt_id, vTag)
            else:
                raw_data = fetch_views_dependency_by_vtag(base_url, pt_id, vTag)
        else:  # iTag
            if include_version_check:
                raw_data = fetch_views_version_dependency_by_itag(base_url, pt_id, iTag)
            else:
                raw_data = fetch_views_dependency_by_itag(base_url, pt_id, iTag)
        
        if raw_data.get("status") == "error":
            return raw_data
        
        request_params["endpoint_used"] = raw_data.get("endpoint")
        
        # Step 2: Parse hierarchy data
        print(f"[OrderSense] Parsing view hierarchy...")
        parsed_data = parse_view_hierarchy(raw_data)
        
        if parsed_data.get("status") == "error":
            return parsed_data
        
        print(f"[OrderSense] Parsed {parsed_data['total_items']} items with {parsed_data['total_dependencies']} dependencies from {parsed_data['total_views']} views")
        
        # Step 3: Analyze dependencies
        print(f"[OrderSense] Analyzing primary question dependencies...")
        analysis_data = analyze_dependencies(parsed_data)
        
        if analysis_data.get("status") == "error":
            return analysis_data
        
        print(f"[OrderSense] Found {analysis_data['total_violations']} violations")
        
        # Step 4: Generate report
        print(f"[OrderSense] Generating validation report...")
        report = generate_validation_report(analysis_data, request_params, parsed_data)
        
        print(f"[OrderSense] Validation complete: {report['summary']}")
        
        return report
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error_message": f"Validation failed: {str(e)}",
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# HELPER FUNCTIONS FOR TESTING
# ============================================================================

def validate_by_vtag(pt_id: str, vtag: str, include_version: bool = False) -> Dict:
    """Convenience function for vTag validation"""
    return run_ordersense_validation(
        pt_id=pt_id,
        vTag=vtag,
        include_version_check=include_version
    )


def validate_by_itag(pt_id: str, itag: str, include_version: bool = False) -> Dict:
    """Convenience function for iTag validation"""
    return run_ordersense_validation(
        pt_id=pt_id,
        iTag=itag,
        include_version_check=include_version
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Test with sample data
    print("\n" + "="*80)
    print("OrderSense Validation - Testing with Sample Data")
    print("="*80)
    
    # Sample data showing violation: Q_30004_396 (tab 4) depends on Q_30004_395 (tab 8)
    sample_data = {
        "views": [{
            "viewName": "polDT",
            "viewItems": {
                "viewItem : Q_30004_395": [{
                    "ptId": 1368,
                    "tabOrder": 8,
                    "qbtag": "30004",
                    "qseqNo": 395,
                    "primaryBTag": 30004,
                    "primarySeqNo": 0,
                    "primaryTabOrder": 0,
                    "presentationLiteral": "Policy Status",
                    "vtag": "polDT"
                }],
                "viewItem : Q_30004_396": [{
                    "ptId": 1368,
                    "tabOrder": 4,
                    "qbtag": "30004",
                    "qseqNo": 396,
                    "primaryBTag": 30004,
                    "primarySeqNo": 395,
                    "primaryTabOrder": 8,
                    "presentationLiteral": "Cancel Reason",
                    "textualExpression": "(Policy.Policy Status=C, CP)",
                    "vtag": "polDT",
                    "dtype": "V"
                }]
            }
        }]
    }
    
    # Test parsing
    parsed = parse_view_hierarchy(sample_data)
    print(f"\n✅ Parsed: {parsed['total_items']} items, {parsed['total_dependencies']} dependencies")
    
    # Test analysis
    analysis = analyze_dependencies(parsed)
    print(f"✅ Analysis: {analysis['total_violations']} violations found")
    
    if analysis['total_violations'] > 0:
        for v in analysis['violations']:
            print(f"\n⚠️  VIOLATION DETECTED:")
            print(f"   Current: {v['current_question_id']} (Tab {v['current_tab_order']})")
            print(f"   Primary: {v['primary_question_id']} (Tab {v['primary_tab_order']})")
            print(f"   Issue: {v['violation_reason']}")
            print(f"   Fix: Move to Tab {v['recommended_tab_order']} or later")
    
    print("\n" + "="*80)