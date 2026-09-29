"""Primavera P6 & Microsoft Project Bi-Directional Round-Trip Schedule Bridge.
Generates Oracle Primavera P6 XML and Microsoft Project XML update files from verified actuals.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List
from src.database.db_manager import DatabaseManager


class P6ScheduleBridge:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def generate_primavera_xml(self, project_name: str = "Oil India Limited - Duliajan GGS Expansion") -> str:
        """Generates standard Oracle Primavera P6 XML format with updated actuals."""
        activities = self.db.get_all_activities()
        root = ET.Element("PrimaveraXML", {"xmlns": "http://xmlns.oracle.com/Primavera/P6/V20.12/API/BusinessObjects"})

        proj = ET.SubElement(root, "Project")
        ET.SubElement(proj, "Id").text = "OIL-GGS-2026"
        ET.SubElement(proj, "Name").text = project_name
        ET.SubElement(proj, "ExportDate").text = datetime.now().isoformat()
        ET.SubElement(proj, "Status").text = "Active"

        acts_elem = ET.SubElement(proj, "Activities")
        for act in activities:
            a_elem = ET.SubElement(acts_elem, "Activity")
            ET.SubElement(a_elem, "ObjectId").text = act["activity_id"]
            ET.SubElement(a_elem, "Id").text = act["activity_id"]
            ET.SubElement(a_elem, "Name").text = act["name"]
            ET.SubElement(a_elem, "WBSCode").text = act.get("wbs_code", "1.0")
            ET.SubElement(a_elem, "Discipline").text = act["discipline"]
            ET.SubElement(a_elem, "PlannedStartDate").text = act["planned_start"]
            ET.SubElement(a_elem, "PlannedFinishDate").text = act["planned_end"]
            
            if act.get("actual_start"):
                ET.SubElement(a_elem, "ActualStartDate").text = act["actual_start"]
            if act.get("actual_end"):
                ET.SubElement(a_elem, "ActualFinishDate").text = act["actual_end"]

            ET.SubElement(a_elem, "Status").text = act.get("status", "NOT_STARTED")
            ET.SubElement(a_elem, "PercentComplete").text = str(act.get("percent_complete", 0.0))
            ET.SubElement(a_elem, "PhysicalQuantityDone").text = str(act.get("actual_quantity", 0.0))

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    def generate_msproject_xml(self, project_name: str = "Oil India Limited - Duliajan GGS Expansion") -> str:
        """Generates Microsoft Project XML schema compatible file."""
        activities = self.db.get_all_activities()
        root = ET.Element("Project", {"xmlns": "http://schemas.microsoft.com/project"})
        ET.SubElement(root, "Title").text = project_name
        ET.SubElement(root, "CreationDate").text = datetime.now().isoformat()

        tasks = ET.SubElement(root, "Tasks")
        for idx, act in enumerate(activities, 1):
            t = ET.SubElement(tasks, "Task")
            ET.SubElement(t, "UID").text = str(idx)
            ET.SubElement(t, "ID").text = act["activity_id"]
            ET.SubElement(t, "Name").text = act["name"]
            ET.SubElement(t, "OutlineNumber").text = act.get("wbs_code", f"1.{idx}")
            ET.SubElement(t, "Start").text = f"{act['planned_start']}T08:00:00"
            ET.SubElement(t, "Finish").text = f"{act['planned_end']}T17:00:00"

            if act.get("actual_start"):
                ET.SubElement(t, "ActualStart").text = f"{act['actual_start']}T08:00:00"
            if act.get("actual_end"):
                ET.SubElement(t, "ActualFinish").text = f"{act['actual_end']}T17:00:00"

            ET.SubElement(t, "PercentComplete").text = str(int(round(act.get("percent_complete", 0.0))))

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
