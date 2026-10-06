-- ============================================================
-- MindTrack database schema (SQLite; ports to PostgreSQL with minor type changes)
-- GENERATED from backend/app/models.py, so it matches the running application.
-- 5 entities: users, exam_schedule, daily_responses, predictions, weekly_reports
-- Change vs the Week 4 draft: predictions.risk_score (0-10, probability-weighted score used for
-- trend tracking and early warnings); questionnaire answers are stored on the 0-4 option scale.
-- Relationships:
--   users 1--* daily_responses    users 1--* exam_schedule (latest row = active exam)
--   daily_responses 1--1 predictions    users 1--* weekly_reports (one per user per week)
-- ============================================================

CREATE TABLE users (
	user_id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	age INTEGER, 
	gender VARCHAR, 
	course VARCHAR, 
	year VARCHAR, 
	living_conditions VARCHAR, 
	mental_health_history INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (user_id)
);

CREATE TABLE daily_responses (
	response_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	response_date DATE NOT NULL, 
	anxiety_level INTEGER NOT NULL, 
	self_esteem INTEGER NOT NULL, 
	depression INTEGER NOT NULL, 
	headache INTEGER NOT NULL, 
	blood_pressure INTEGER NOT NULL, 
	sleep_quality INTEGER NOT NULL, 
	breathing_problem INTEGER NOT NULL, 
	noise_level INTEGER NOT NULL, 
	living_conditions INTEGER NOT NULL, 
	safety INTEGER NOT NULL, 
	basic_needs INTEGER NOT NULL, 
	academic_performance INTEGER NOT NULL, 
	study_load INTEGER NOT NULL, 
	teacher_student_relationship INTEGER NOT NULL, 
	future_career_concerns INTEGER NOT NULL, 
	social_support INTEGER NOT NULL, 
	peer_pressure INTEGER NOT NULL, 
	extracurricular_activities INTEGER NOT NULL, 
	bullying INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (response_id), 
	CONSTRAINT uq_user_day UNIQUE (user_id, response_date), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE exam_schedule (
	exam_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	exam_date DATE NOT NULL, 
	exam_label VARCHAR, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (exam_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE weekly_reports (
	report_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	week_start_date DATE NOT NULL, 
	week_end_date DATE NOT NULL, 
	average_stress_level FLOAT, 
	highest_stress_day DATE, 
	lowest_stress_day DATE, 
	previous_week_comparison VARCHAR, 
	early_warning_triggered INTEGER NOT NULL, 
	generated_at DATETIME NOT NULL, 
	PRIMARY KEY (report_id), 
	CONSTRAINT uq_user_week UNIQUE (user_id, week_start_date), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);

CREATE TABLE predictions (
	prediction_id INTEGER NOT NULL, 
	response_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	predicted_stress_level INTEGER NOT NULL, 
	prediction_confidence FLOAT NOT NULL, 
	risk_score FLOAT NOT NULL, 
	shap_top_factors TEXT, 
	predicted_at DATETIME NOT NULL, 
	PRIMARY KEY (prediction_id), 
	UNIQUE (response_id), 
	FOREIGN KEY(response_id) REFERENCES daily_responses (response_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);
