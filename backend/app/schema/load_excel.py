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

EXCEL_FILE = "test.xlsx"

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


# ==========================================================
# LOAD EXCEL
# ==========================================================

print("Reading workbook...")

df = pd.read_excel(
    EXCEL_FILE,
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

        category = clean(row["Category"])
        objective = clean(row["Objective"])
        action_test_case = clean(row["Action / Test Case"])
        test_type = clean(row["Test Type"])
        source_scope_status = clean(row["Source Scope Status"])
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
        asset = clean(row["Asset"])
        attack_feasibility = clean(row["Attack Feasibility"])
        cia_impact = clean(row["CIA Impact"])
        safety_impact = clean(row["Safety Impact"])
        automation_possible = clean(row["Automation Possible"])

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

        asset_id = get_or_create(
            conn,
            "assets",
            "asset_name",
            asset,
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
            raise Exception(
                f"Severity not found: {severity}"
            )

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
                    asset_id,

                    action_test_case,
                    source_scope_status,

                    description,
                    attack_path,

                    test_steps,
                    expected_output,

                    attack_feasibility,
                    cia_impact,
                    safety_impact,
                    automation_possible
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
                    :asset_id,

                    :action_test_case,
                    :source_scope_status,

                    :description,
                    :attack_path,

                    :test_steps,
                    :expected_output,

                    :attack_feasibility,
                    :cia_impact,
                    :safety_impact,
                    :automation_possible
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
                "asset_id": asset_id,

                "action_test_case": action_test_case,
                "source_scope_status": source_scope_status,

                "description": description,
                "attack_path": attack_path,

                "test_steps": test_steps,
                "expected_output": expected_output,

                "attack_feasibility": attack_feasibility,
                "cia_impact": cia_impact,
                "safety_impact": safety_impact,
                "automation_possible": automation_possible,
            },
        )

print()
print("===================================")
print("Import completed successfully")
print("===================================")
print(f"Rows processed : {len(df)}")