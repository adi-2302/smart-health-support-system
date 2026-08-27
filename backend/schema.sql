-- ============================================================
-- Database Schema: Smart Mental Health Support System
-- 5 entities: Users, Daily_Responses, Predictions, Weekly_Reports, Exam_Schedule
-- Written in standard SQL (SQLite-compatible now, ports to PostgreSQL later)
-- ============================================================

CREATE TABLE Users (
    user_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    email               TEXT NOT NULL UNIQUE,
    password_hash       TEXT NOT NULL,
    age                 INTEGER,
    gender              TEXT,
    course              TEXT,
    year                INTEGER,
    living_conditions   TEXT,
    mental_health_history INTEGER,   -- 0/1, matches dataset's mental_health_history feature
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Exam_Schedule (
    exam_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    exam_date           DATE NOT NULL,
    exam_label          TEXT,               -- e.g. "End Semester Exams"
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
    -- One user can have one ACTIVE exam entry at a time; history kept via updated_at.
);

CREATE TABLE Daily_Responses (
    response_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                        INTEGER NOT NULL,
    response_date                  DATE NOT NULL,
    anxiety_level                  INTEGER,
    self_esteem                    INTEGER,
    depression                     INTEGER,
    headache                       INTEGER,
    blood_pressure                 INTEGER,
    sleep_quality                  INTEGER,
    breathing_problem              INTEGER,
    noise_level                    INTEGER,
    living_conditions              INTEGER,
    safety                         INTEGER,
    basic_needs                    INTEGER,
    academic_performance           INTEGER,
    study_load                     INTEGER,
    teacher_student_relationship   INTEGER,
    future_career_concerns         INTEGER,
    social_support                 INTEGER,
    peer_pressure                  INTEGER,
    extracurricular_activities     INTEGER,
    bullying                       INTEGER,
    created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    UNIQUE (user_id, response_date)   -- enforces one questionnaire submission per user per day
);

CREATE TABLE Predictions (
    prediction_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id         INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    predicted_stress_level INTEGER NOT NULL,   -- 0=Low, 1=Medium, 2=High
    prediction_confidence  REAL,               -- model's probability for predicted class
    shap_top_factors    TEXT,                  -- JSON array of top contributing features
    predicted_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES Daily_Responses(response_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Weekly_Reports (
    report_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL,
    week_start_date       DATE NOT NULL,
    week_end_date         DATE NOT NULL,
    average_stress_level  REAL,
    highest_stress_day    DATE,
    lowest_stress_day     DATE,
    previous_week_comparison TEXT,      -- e.g. "improved", "worsened", "stable"
    early_warning_triggered INTEGER DEFAULT 0,  -- 0/1
    generated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    UNIQUE (user_id, week_start_date)
);

-- ============================================================
-- Relationships summary:
--   Users (1) ---- (many) Daily_Responses
--   Users (1) ---- (1 active) Exam_Schedule
--   Daily_Responses (1) ---- (1) Predictions
--   Users (1) ---- (many) Weekly_Reports  [aggregated from Predictions over 7-day windows]
-- ============================================================
