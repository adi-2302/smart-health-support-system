"""Single source of truth for the daily check-in. The frontend renders from GET /questions,
so question wording/options only ever live here."""

INTENSITY = ["Not at all", "A little", "Somewhat", "Quite a bit", "Extremely"]
QUALITY = ["Very poor", "Poor", "Okay", "Good", "Very good"]
FREQUENCY = ["Never", "Rarely", "Sometimes", "Often", "Very often"]
LOAD = ["Very light", "Light", "Moderate", "Heavy", "Very heavy"]
NOISE = ["Very quiet", "Quiet", "Moderate", "Noisy", "Very noisy"]
SAFETY = ["Very unsafe", "Unsafe", "Neutral", "Safe", "Very safe"]
SUPPORT = ["Not at all", "A little", "Somewhat", "Well", "Very well"]
PRESSURE = ["None", "A little", "Some", "Quite a bit", "A lot"]
BUSY = ["Not at all", "A little", "Somewhat", "Quite busy", "Very busy"]
NEEDS = ["Very poorly", "Poorly", "Okay", "Well", "Very well"]


def _opts(labels, start=0):
    return [{"label": l, "value": start + i} for i, l in enumerate(labels)]


QUESTIONS = [
    # Mind
    {"key": "anxiety_level", "group": "Mind", "text": "How anxious have you felt today?", "options": _opts(INTENSITY)},
    {"key": "self_esteem", "group": "Mind", "text": "How good do you feel about yourself today?", "options": _opts(QUALITY)},
    {"key": "depression", "group": "Mind", "text": "How low or down have you felt today?", "options": _opts(INTENSITY)},
    # Body
    {"key": "headache", "group": "Body", "text": "Have you had a headache today?", "options": _opts(["Not at all", "A little", "Somewhat", "Quite a bit", "Severely"])},
    {"key": "sleep_quality", "group": "Body", "text": "How well did you sleep last night?", "options": _opts(QUALITY)},
    {"key": "breathing_problem", "group": "Body", "text": "Have you felt short of breath today?", "options": _opts(["Not at all", "A little", "Somewhat", "Quite a bit", "A lot"])},
    {"key": "blood_pressure", "group": "Body", "text": "How was your blood pressure last time you checked?", "options": _opts(["Low", "Normal", "High"], start=1)},
    # Studies
    {"key": "academic_performance", "group": "Studies", "text": "How are your grades / academic performance right now?", "options": _opts(QUALITY)},
    {"key": "study_load", "group": "Studies", "text": "How heavy does your study workload feel today?", "options": _opts(LOAD)},
    {"key": "teacher_student_relationship", "group": "Studies", "text": "How is your relationship with your teachers/faculty?", "options": _opts(QUALITY)},
    {"key": "future_career_concerns", "group": "Studies", "text": "How worried do you feel about your future career?", "options": _opts(INTENSITY)},
    # People
    {"key": "social_support", "group": "People", "text": "How supported do you feel by friends or family right now?", "options": _opts(SUPPORT)},
    {"key": "peer_pressure", "group": "People", "text": "How much peer pressure have you felt today?", "options": _opts(PRESSURE)},
    {"key": "extracurricular_activities", "group": "People", "text": "How busy have extracurriculars kept you today?", "options": _opts(BUSY)},
    {"key": "bullying", "group": "People", "text": "Have you experienced bullying or unkind treatment lately?", "options": _opts(FREQUENCY)},
    # Surroundings
    {"key": "noise_level", "group": "Surroundings", "text": "How noisy has your environment been today?", "options": _opts(NOISE)},
    {"key": "living_conditions", "group": "Surroundings", "text": "How would you rate your living conditions?", "options": _opts(QUALITY)},
    {"key": "safety", "group": "Surroundings", "text": "How safe do you feel in your environment?", "options": _opts(SAFETY)},
    {"key": "basic_needs", "group": "Surroundings", "text": "How well are your basic needs (food, rest, essentials) met?", "options": _opts(NEEDS)},
]

QUESTION_KEYS = [q["key"] for q in QUESTIONS]
ALLOWED_VALUES = {q["key"]: {o["value"] for o in q["options"]} for q in QUESTIONS}
