CREATE DATABASE IF NOT EXISTS embedded_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE embedded_db;

CREATE TABLE categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE objectives (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE KEY uk_obj(category_id, name(255)),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE protocols (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE attack_vectors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE test_types (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE severities (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    severity_rank INT NOT NULL
);

CREATE TABLE threats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    threat_text TEXT NOT NULL,
    UNIQUE KEY uk_threat(threat_text(255))
);

CREATE TABLE assets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_name VARCHAR(500) NOT NULL UNIQUE
);

CREATE TABLE tools_master (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tool_name VARCHAR(1000) NOT NULL,
    UNIQUE KEY uk_tool(tool_name(255))
);

CREATE TABLE references_master (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ref_text TEXT NOT NULL,
    UNIQUE KEY uk_ref(ref_text(255))
);

CREATE TABLE test_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    category_id BIGINT NOT NULL,
    objective_id BIGINT NOT NULL,
    protocol_id BIGINT,
    attack_vector_id BIGINT,
    test_type_id BIGINT,
    severity_id BIGINT,
    threat_id BIGINT,
    asset_id BIGINT,

    action_test_case LONGTEXT NOT NULL,
    source_scope_status VARCHAR(100),

    description LONGTEXT,
    attack_path LONGTEXT,

    test_steps LONGTEXT,
    expected_output LONGTEXT,

    attack_feasibility TEXT,
    cia_impact TEXT,
    safety_impact TEXT,
    automation_possible VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (objective_id) REFERENCES objectives(id),
    FOREIGN KEY (protocol_id) REFERENCES protocols(id),
    FOREIGN KEY (attack_vector_id) REFERENCES attack_vectors(id),
    FOREIGN KEY (test_type_id) REFERENCES test_types(id),
    FOREIGN KEY (severity_id) REFERENCES severities(id),
    FOREIGN KEY (threat_id) REFERENCES threats(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE test_case_tools (
    test_case_id BIGINT NOT NULL,
    tool_id BIGINT NOT NULL,
    PRIMARY KEY(test_case_id, tool_id),
    FOREIGN KEY(test_case_id) REFERENCES test_cases(id),
    FOREIGN KEY(tool_id) REFERENCES tools_master(id)
);

CREATE TABLE test_case_references (
    test_case_id BIGINT NOT NULL,
    reference_id BIGINT NOT NULL,
    PRIMARY KEY(test_case_id, reference_id),
    FOREIGN KEY(test_case_id) REFERENCES test_cases(id),
    FOREIGN KEY(reference_id) REFERENCES references_master(id)
);

INSERT INTO severities(name,severity_rank)
VALUES
('Informational',1),
('Low',2),
('Medium',3),
('High',4),
('Critical',5);