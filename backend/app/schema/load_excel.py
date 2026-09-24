import os
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================================
# CONFIG
# ==========================================================

MYSQL_USER = "root"
MYSQL_PWD = "manager"
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "embedded_db"

EXCEL_FILE = os.getenv(
    "EXCEL_FILE",
    str(Path(__file__).resolve().parents[3] / "Pentesting_DataBase_Version_2.xlsx"),
)

# ==========================================================
# DB
# ==========================================================

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PWD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}",
    pool_pre_ping=True,
)

# ==========================================================
# HELPERS
# ==========================================================

def clean(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def get_or_create(conn, table, column, value):
    if value is None:
        return None

    row = conn.execute(
        text(
            f"""
            SELECT id
            FROM {table}
            WHERE {column} = :value
            LIMIT 1
            """
        ),
        {"value": value},
    ).fetchone()

    if row:
        return row[0]

    conn.execute(
        text(
            f"""
            INSERT INTO {table}
            ({column})
            VALUES (:value)
            """
        ),
        {"value": value},
    )

    row = conn.execute(
        text(
            f"""
            SELECT id
            FROM {table}
            WHERE {column} = :value
            LIMIT 1
            """
        ),
        {"value": value},
    ).fetchone()

    return row[0]


def split_values(value):
    if value is None:
        return []
    return [item.strip() for item in re.split(r"[,;|\n]+", value) if item.strip()]


def sync_links(conn, test_case_id, tool_used, reference):
    conn.execute(text("DELETE FROM test_case_tools WHERE test_case_id = :id"), {"id": test_case_id})
    conn.execute(text("DELETE FROM test_case_references WHERE test_case_id = :id"), {"id": test_case_id})

    for value in split_values(tool_used):
        tool_id = get_or_create(conn, "tools_master", "tool_name", value)
        conn.execute(
            text("INSERT IGNORE INTO test_case_tools (test_case_id, tool_id) VALUES (:test_case_id, :tool_id)"),
            {"test_case_id": test_case_id, "tool_id": tool_id},
        )

    for value in split_values(reference):
        reference_id = get_or_create(conn, "references_master", "ref_text", value)
        conn.execute(
            text("INSERT IGNORE INTO test_case_references (test_case_id, reference_id) VALUES (:test_case_id, :reference_id)"),
            {"test_case_id": test_case_id, "reference_id": reference_id},
        )


# ==========================================================
# LOAD EXCEL
# ==========================================================

print("Reading workbook...")

workbook = pd.ExcelFile(EXCEL_FILE)
if "Sheet2" in workbook.sheet_names:
    df = pd.read_excel(workbook, sheet_name="Sheet2", header=0)
else:
    df = pd.read_excel(
        workbook,
        sheet_name="ECU_PenTest_Master",
        header=1,
    )

print(f"Rows loaded from Excel: {len(df)}")
print()

# ==========================================================
# IMPORT
# ==========================================================

with engine.begin() as conn:

    for idx, row in df.iterrows():

        print(
            f"Processing {idx + 1}/{len(df)}",
            end="\r",
        )

        action_test_case = clean(row.get("Action / Test Case"))
        if action_test_case is None:
            continue

        category = clean(row["Category"])
        objective = clean(row["Objective"])
        test_case_name = clean(row.get("TC Name"))
        pre_condition = clean(row.get("Pre-Condition"))
        impact = clean(row.get("Impact"))
        test_type = clean(row["Test Type"])
        source_scope_status = clean(row.get("Source Scope Status"))
        attack_vector = clean(row["Attack Vector"])
        protocol = clean(row["Protocol"])
        description = clean(row["Description"])
        threat = clean(row["Threat"])
        attack_path = clean(row["Attack Path"])
        tool_used = clean(row["Tool Used"])
        test_steps = clean(row["Test Steps"])
        expected_output = clean(row["Expected Output"])
        reference = clean(row["Reference"])
        severity = clean(row["Severity"])
        attack_feasibility = clean(row["Attack Feasibility"])
        cia_impact = clean(row["CIA Impact"])
        safety_impact = clean(row["Safety Impact"])

        # ==================================================
        # MASTER TABLES
        # ==================================================

        category_id = get_or_create(
            conn,
            "categories",
            "name",
            category,
        )

        protocol_id = get_or_create(
            conn,
            "protocols",
            "name",
            protocol,
        )

        attack_vector_id = get_or_create(
            conn,
            "attack_vectors",
            "name",
            attack_vector,
        )

        test_type_id = get_or_create(
            conn,
            "test_types",
            "name",
            test_type,
        )

        threat_id = get_or_create(
            conn,
            "threats",
            "threat_text",
            threat,
        )

        severity_row = conn.execute(
            text(
                """
                SELECT id
                FROM severities
                WHERE name = :name
                """
            ),
            {"name": severity},
        ).fetchone()

        if not severity_row:
            severity_lower = (severity or "").lower()
            severity_rank = (
                4 if "critical" in severity_lower else
                3 if "high" in severity_lower else
                2 if "medium" in severity_lower else
                1
            )
            conn.execute(
                text(
                    """
                    INSERT INTO severities (name, severity_rank)
                    VALUES (:name, :severity_rank)
                    """
                ),
                {"name": severity, "severity_rank": severity_rank},
            )
            severity_row = conn.execute(
                text(
                    """
                    SELECT id
                    FROM severities
                    WHERE name = :name
                    """
                ),
                {"name": severity},
            ).fetchone()

        severity_id = severity_row[0]

        # ==================================================
        # OBJECTIVE
        # ==================================================

        objective_row = conn.execute(
            text(
                """
                SELECT id
                FROM objectives
                WHERE category_id = :category_id
                AND name = :name
                """
            ),
            {
                "category_id": category_id,
                "name": objective,
            },
        ).fetchone()

        if objective_row:
            objective_id = objective_row[0]
        else:
            conn.execute(
                text(
                    """
                    INSERT INTO objectives
                    (
                        category_id,
                        name
                    )
                    VALUES
                    (
                        :category_id,
                        :name
                    )
                    """
                ),
                {
                    "category_id": category_id,
                    "name": objective,
                },
            )

            objective_id = conn.execute(
                text(
                    """
                    SELECT id
                    FROM objectives
                    WHERE category_id=:category_id
                    AND name=:name
                    """
                ),
                {
                    "category_id": category_id,
                    "name": objective,
                },
            ).fetchone()[0]

        # ==================================================
        # DUPLICATE CHECK
        # ==================================================

        exists = conn.execute(
            text(
                """
                SELECT id
                FROM test_cases
                WHERE objective_id = :objective_id
                AND action_test_case = :action_test_case
                LIMIT 1
                """
            ),
            {
                "objective_id": objective_id,
                "action_test_case": action_test_case,
            },
        ).fetchone()

        if exists:
            conn.execute(
                text(
                    """
                    UPDATE test_cases
                    SET test_case_name = :test_case_name,
                        pre_condition = :pre_condition,
                        impact = :impact
                    WHERE id = :id
                    """
                ),
                {
                    "id": exists[0],
                    "test_case_name": test_case_name,
                    "pre_condition": pre_condition,
                    "impact": impact,
                },
            )
            sync_links(conn, exists[0], tool_used, reference)
            continue

        # ==================================================
        # INSERT TEST CASE
        # ==================================================

        conn.execute(
            text(
                """
                INSERT INTO test_cases
                (
                    category_id,
                    objective_id,
                    protocol_id,
                    attack_vector_id,
                    test_type_id,
                    severity_id,
                    threat_id,

                    test_case_name,
                    pre_condition,
                    impact,
                    action_test_case,
                    source_scope_status,

                    description,
                    attack_path,

                    test_steps,
                    expected_output,

                    attack_feasibility,
                    cia_impact,
                    safety_impact,
                )
                VALUES
                (
                    :category_id,
                    :objective_id,
                    :protocol_id,
                    :attack_vector_id,
                    :test_type_id,
                    :severity_id,
                    :threat_id,

                    :test_case_name,
                    :pre_condition,
                    :impact,
                    :action_test_case,
                    :source_scope_status,

                    :description,
                    :attack_path,

                    :test_steps,
                    :expected_output,

                    :attack_feasibility,
                    :cia_impact,
                    :safety_impact,
                )
                """
            ),
            {
                "category_id": category_id,
                "objective_id": objective_id,
                "protocol_id": protocol_id,
                "attack_vector_id": attack_vector_id,
                "test_type_id": test_type_id,
                "severity_id": severity_id,
                "threat_id": threat_id,

                "test_case_name": test_case_name,
                "pre_condition": pre_condition,
                "impact": impact,
                "action_test_case": action_test_case,
                "source_scope_status": source_scope_status,

                "description": description,
                "attack_path": attack_path,

                "test_steps": test_steps,
                "expected_output": expected_output,

                "attack_feasibility": attack_feasibility,
                "cia_impact": cia_impact,
                "safety_impact": safety_impact,
            },
        )

        test_case_id = conn.execute(
            text("SELECT id FROM test_cases WHERE objective_id = :objective_id AND action_test_case = :action_test_case ORDER BY id DESC LIMIT 1"),
            {"objective_id": objective_id, "action_test_case": action_test_case},
        ).fetchone()[0]
        sync_links(conn, test_case_id, tool_used, reference)

print()
print("===================================")
print("Import completed successfully")
print("===================================")
print(f"Rows processed : {len(df)}")