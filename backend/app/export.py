from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
import datetime

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))

def group_flags_by_severity(flags: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups a list of flags by their severity level."""
    grouped = {
        "High": [],
        "Medium": [],
        "Low": [],
        "Info": []
    }
    for flag in flags:
        severity = flag.get("severity", "Info")
        if severity in grouped:
            grouped[severity].append(flag)
    return grouped

def generate_report_html(doc: Dict[str, Any], flags: List[Dict[str, Any]], contract_type: str) -> str:
    """
    Generates a professional HTML report from the analysis results.
    """
    template = env.get_template("report.html")
    
    # Group flags for the Red-Flag Board
    grouped_flags = group_flags_by_severity(flags)
    
    # Create a map of clause_id to its flag for easy lookup
    clause_flag_map = {f["clause_id"]: f for f in flags}

    # Prepare data for the template
    template_data = {
        "contract_type": contract_type,
        "generation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clauses": doc.get("clauses", []),
        "grouped_flags": grouped_flags,
        "clause_flag_map": clause_flag_map
    }
    
    return template.render(template_data)
