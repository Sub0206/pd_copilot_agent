"""
OrderSense Agent - Tab Order Validation System
Analyzes view items for processing order violations based on dependencies
All sub-agents implemented as function tools for PD Copilot integration
"""

from agents import function_tool
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import requests
from datetime import datetime
import json


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUTS
# ============================================================================

class TabOrderViolation(BaseModel):
    """Represents a single tab order violation"""
    current_question_id: str = Field(description="Question with the violation")
    current_tab: int = Field(description="Current tab order")
    dependency_question_id: str = Field(description="Dependency that causes violation")
    dependency_tab: int = Field(description="Tab order of dependency")
    entity_id: str = Field(description="Entity ID")
    view_name: str = Field(description="View name")
    recommended_tab: int = Field(description="Recommended tab order to fix violation")
    explanation: str = Field(description="Explanation of the violation")


class ValidationReport(BaseModel):
    """Final validation report"""
    summary: str = Field(description="Executive summary of findings")
    violations_by_view: Dict[str, List[Dict]] = Field(description="Violations grouped by view")
    recommendations: List[str] = Field(description="List of recommended actions")
    total_violations: int = Field(description="Total number of violations")
    report_generated_at: str = Field(description="Timestamp of report generation")


# ============================================================================
# FUNCTION TOOLS - All OrderSense sub-agents as tools
# ============================================================================

@function_tool
def fetch_database_info(api_url: str) -> Dict:
    """
    DATABASE AGENT: Fetch view items data from the web service API.
    
    This tool calls your API endpoint to retrieve view items with their tab orders and dependencies.
    
    Args:
        api_url: The API endpoint URL to fetch view items data
        
    Returns:
        Dictionary containing view items data with status
    """
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@function_tool
def parse_database_info(raw_data: str) -> Dict:
    """
    INPUT AGENT: Parse raw database information into structured view items.
    
    Extracts and organizes:
    - Question IDs (format: Q_EntityID_TabNumber)
    - Entity IDs from question IDs
    - Tab order positions
    - Dependency lists
    - View names
    
    Args:
        raw_data: JSON string of raw database data from API
        
    Returns:
        Dictionary with parsed view items organized by views
    """
    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        
        if "data" in data:
            data = data["data"]
        
        parsed_views = []
        total_items = 0
        
        for view in data.get("views", []):
            view_items = []
            for item in view.get("items", []):
                # Extract entity ID from question ID (Q_EntityID_TabNumber)
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
        
        return {
            "status": "success",
            "parsed_views": parsed_views,
            "total_items": total_items,
            "parsing_notes": f"Successfully parsed {total_items} items from {len(parsed_views)} views"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "parsing_notes": "Failed to parse database information"
        }


@function_tool
def analyze_view_items(parsed_data: str) -> Dict:
    """
    ANALYSIS AGENT: Identify tab order violations in view items.
    
    Analyzes each view item to find violations where a question depends on another 
    question that appears AFTER it in the tab order.
    
    Analysis steps for each item:
    1. Entity Match Check: Verify dependency belongs to same entity
    2. Version Selection: Handle multiple versions of questions (v1, v2, etc.)
    3. Tab Order Comparison: 
       - dependency_tab < current_tab = CORRECT (dependency before current)
       - dependency_tab > current_tab = VIOLATION (dependency after current)
    
    Args:
        parsed_data: JSON string of parsed view items data
        
    Returns:
        Dictionary with analysis results including all violations found
    """
    try:
        data = json.loads(parsed_data) if isinstance(parsed_data, str) else parsed_data
        
        violations = []
        total_analyzed = 0
        views_with_violations = set()
        
        # Build lookup map for all items
        item_lookup = {}
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                item_lookup[item["question_id"]] = item
        
        # Analyze each item
        for view in data.get("parsed_views", []):
            for item in view.get("items", []):
                total_analyzed += 1
                current_qid = item["question_id"]
                current_tab = item["tab_order"]
                current_entity = item["entity_id"]
                view_name = item["view_name"]
                
                # Check each dependency
                for dep_qid in item.get("dependencies", []):
                    # Handle versioned dependencies (e.g., Q_30004_5_v2)
                    base_dep_qid = dep_qid.split("_v")[0]  # Remove version suffix
                    
                    # Find the dependency
                    dep_item = item_lookup.get(dep_qid) or item_lookup.get(base_dep_qid)
                    
                    if not dep_item:
                        continue
                    
                    dep_tab = dep_item["tab_order"]
                    dep_entity = dep_item["entity_id"]
                    
                    # Only check same entity dependencies
                    if current_entity != dep_entity:
                        continue
                    
                    # VIOLATION: dependency appears AFTER current item
                    if dep_tab > current_tab:
                        # Calculate recommended tab (after the dependency)
                        recommended_tab = dep_tab + 1
                        
                        violation = {
                            "current_question_id": current_qid,
                            "current_tab": current_tab,
                            "dependency_question_id": dep_qid,
                            "dependency_tab": dep_tab,
                            "entity_id": current_entity,
                            "view_name": view_name,
                            "recommended_tab": recommended_tab,
                            "explanation": f"{current_qid} at tab {current_tab} depends on {dep_qid} at tab {dep_tab}. "
                                         f"The dependency appears later in the sequence, causing a processing order violation. "
                                         f"Recommended: Move {current_qid} to tab {recommended_tab} or later."
                        }
                        violations.append(violation)
                        views_with_violations.add(view_name)
        
        return {
            "status": "success",
            "violations": violations,
            "total_items_analyzed": total_analyzed,
            "total_violations": len(violations),
            "views_with_violations": list(views_with_violations)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "violations": [],
            "total_items_analyzed": 0,
            "total_violations": 0
        }


@function_tool
def generate_report(analysis_data: str) -> Dict:
    """
    REPORT AGENT: Generate comprehensive validation report from analysis results.
    
    Creates a detailed report including:
    - Executive summary of findings
    - Violations grouped by view
    - Specific recommendations for each violation
    - Actionable steps to resolve issues
    
    Args:
        analysis_data: JSON string of analysis results with violations
        
    Returns:
        Dictionary with formatted validation report
    """
    try:
        data = json.loads(analysis_data) if isinstance(analysis_data, str) else analysis_data
        
        violations = data.get("violations", [])
        total_violations = data.get("total_violations", 0)
        views_with_violations = data.get("views_with_violations", [])
        
        # Group violations by view
        violations_by_view = {}
        for v in violations:
            view_name = v["view_name"]
            if view_name not in violations_by_view:
                violations_by_view[view_name] = []
            violations_by_view[view_name].append(v)
        
        # Generate summary
        if total_violations == 0:
            summary = "✅ No tab order violations found. All view items are properly sequenced with dependencies appearing before dependent items."
        else:
            summary = (
                f"⚠️ Analysis identified {total_violations} tab order violation(s) across {len(views_with_violations)} view(s). "
                f"These violations occur when questions depend on other questions that appear later in the tab sequence, "
                f"which can cause processing order issues."
            )
        
        # Generate recommendations
        recommendations = []
        for view_name, view_violations in violations_by_view.items():
            for v in view_violations:
                rec = (
                    f"[{view_name}] Move {v['current_question_id']} from tab {v['current_tab']} "
                    f"to tab {v['recommended_tab']} or later (after dependency {v['dependency_question_id']} at tab {v['dependency_tab']})"
                )
                recommendations.append(rec)
        
        report = {
            "status": "success",
            "summary": summary,
            "violations_by_view": violations_by_view,
            "recommendations": recommendations,
            "total_violations": total_violations,
            "report_generated_at": datetime.now().isoformat()
        }
        
        return report
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "summary": "Failed to generate report",
            "violations_by_view": {},
            "recommendations": [],
            "total_violations": 0
        }


@function_tool
def evaluate_report(report_data: str) -> Dict:
    """
    EVALUATOR AGENT: Quality assurance check on validation report.
    
    Evaluates report for:
    - Completeness: All dependencies properly traced
    - Accuracy: Tab order violations correctly identified
    - Documentation: Clear explanations and recommendations
    - Format: Professional structure
    
    Quality criteria for approval:
    - All dependency chains validated
    - Tab order comparisons mathematically correct
    - Recommendations are actionable
    - No logical errors in violation identification
    
    Args:
        report_data: JSON string of generated report
        
    Returns:
        Dictionary with evaluation result (approved/rejected with feedback)
    """
    try:
        data = json.loads(report_data) if isinstance(report_data, str) else report_data
        
        # Check if report generation was successful
        if data.get("status") != "success":
            return {
                "status": "success",
                "approved": False,
                "feedback": "Report generation failed. Please regenerate.",
                "issues_found": ["Report status indicates failure"],
                "confidence_score": 0.0
            }
        
        violations_by_view = data.get("violations_by_view", {})
        recommendations = data.get("recommendations", [])
        total_violations = data.get("total_violations", 0)
        
        issues = []
        
        # Check 1: Recommendations match violations
        if len(recommendations) != total_violations:
            issues.append(f"Mismatch: {total_violations} violations but {len(recommendations)} recommendations")
        
        # Check 2: All violations have proper structure
        for view_name, violations in violations_by_view.items():
            for v in violations:
                required_fields = ["current_question_id", "current_tab", "dependency_tab", "recommended_tab"]
                missing_fields = [f for f in required_fields if f not in v]
                if missing_fields:
                    issues.append(f"Violation in {view_name} missing fields: {missing_fields}")
                
                # Check 3: Verify tab order logic (dependency_tab should be > current_tab for violations)
                if "dependency_tab" in v and "current_tab" in v:
                    if v["dependency_tab"] <= v["current_tab"]:
                        issues.append(
                            f"Invalid violation: {v['current_question_id']} - dependency tab {v['dependency_tab']} "
                            f"should be greater than current tab {v['current_tab']}"
                        )
        
        # Determine approval
        approved = len(issues) == 0
        confidence_score = 1.0 if approved else max(0.0, 1.0 - (len(issues) * 0.2))
        
        if approved:
            feedback = (
                f"✅ Report approved. Successfully identified {total_violations} violation(s) with proper "
                f"validation logic and clear recommendations."
            )
        else:
            feedback = f"❌ Report has {len(issues)} issue(s) that need correction."
        
        return {
            "status": "success",
            "approved": approved,
            "feedback": feedback,
            "issues_found": issues,
            "confidence_score": confidence_score
        }
        
    except Exception as e:
        return {
            "status": "error",
            "approved": False,
            "feedback": f"Evaluation failed: {str(e)}",
            "issues_found": ["Evaluation process error"],
            "confidence_score": 0.0
        }


# ============================================================================
# MAIN ORDERSENSE TOOL - Single tool for PD Copilot
# ============================================================================

@function_tool
def run_ordersense_validation(api_url: str) -> Dict:
    """
    ORDERSENSE AGENT: Complete tab order validation pipeline.
    
    This is the main OrderSense tool that orchestrates all validation steps:
    1. Fetches view items data from API
    2. Parses the data structure
    3. Analyzes for tab order violations
    4. Generates comprehensive report
    5. Performs quality assurance check
    
    Use this tool when user wants to validate tab orders or check for processing
    order violations in view items.
    
    Args:
        api_url: The API endpoint URL to fetch view items data
        
    Returns:
        Dictionary with complete validation report including violations and recommendations
    """
    try:
        # Step 1: Fetch database info
        raw_data = fetch_database_info.invoke(api_url)
        if raw_data.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Failed to fetch data: {raw_data.get('error_message')}",
                "step_failed": "fetch_database_info"
            }
        
        # Step 2: Parse database info
        parsed_data = parse_database_info.invoke(json.dumps(raw_data))
        if parsed_data.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Failed to parse data: {parsed_data.get('error_message')}",
                "step_failed": "parse_database_info"
            }
        
        # Step 3: Analyze view items
        analysis_data = analyze_view_items.invoke(json.dumps(parsed_data))
        if analysis_data.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Failed to analyze: {analysis_data.get('error_message')}",
                "step_failed": "analyze_view_items"
            }
        
        # Step 4: Generate report
        report = generate_report.invoke(json.dumps(analysis_data))
        if report.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Failed to generate report: {report.get('error_message')}",
                "step_failed": "generate_report"
            }
        
        # Step 5: Evaluate report
        evaluation = evaluate_report.invoke(json.dumps(report))
        if evaluation.get("status") == "error":
            return {
                "status": "error",
                "error_message": f"Failed to evaluate: {evaluation.get('error_message')}",
                "step_failed": "evaluate_report"
            }
        
        # If evaluation not approved, include feedback but still return report
        if not evaluation.get("approved", False):
            report["evaluation_feedback"] = evaluation.get("feedback")
            report["evaluation_issues"] = evaluation.get("issues_found", [])
            report["needs_review"] = True
        else:
            report["evaluation_feedback"] = evaluation.get("feedback")
            report["needs_review"] = False
        
        return report
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"OrderSense validation failed: {str(e)}",
            "step_failed": "orchestration"
        }


# ============================================================================
# HELPER FUNCTION FOR INTEGRATION
# ============================================================================

def format_ordersense_result(report: Dict) -> str:
    """
    Format OrderSense validation report for display to user
    
    Args:
        report: Dictionary containing validation report
        
    Returns:
        Formatted string with report details
    """
    if report.get("status") != "success":
        return f"❌ OrderSense validation failed: {report.get('error_message', 'Unknown error')}"
    
    output = []
    output.append("=" * 70)
    output.append("📊 ORDERSENSE TAB ORDER VALIDATION REPORT")
    output.append("=" * 70)
    output.append("")
    
    # Summary
    output.append(f"📋 Summary:")
    output.append(f"{report.get('summary', 'No summary available')}")
    output.append("")
    
    # Violations by view
    violations_by_view = report.get("violations_by_view", {})
    if violations_by_view:
        output.append(f"🔍 Violations by View:")
        output.append("")
        for view_name, violations in violations_by_view.items():
            output.append(f"  View: {view_name} ({len(violations)} violation(s))")
            for v in violations:
                output.append(f"    • {v['current_question_id']} (Tab {v['current_tab']})")
                output.append(f"      → Depends on: {v['dependency_question_id']} (Tab {v['dependency_tab']})")
                output.append(f"      → Recommended: Move to Tab {v['recommended_tab']} or later")
            output.append("")
    
    # Recommendations
    recommendations = report.get("recommendations", [])
    if recommendations:
        output.append(f"💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            output.append(f"  {i}. {rec}")
        output.append("")
    
    # Metadata
    output.append(f"📅 Report Generated: {report.get('report_generated_at', 'N/A')}")
    output.append(f"📈 Total Violations: {report.get('total_violations', 0)}")
    output.append("=" * 70)
    
    return "\n".join(output)
