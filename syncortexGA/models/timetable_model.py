from pydantic import BaseModel, model_validator
from typing import List, Optional, Literal

# ========== TimeSlot ==========
class TimeSlot(BaseModel):
    """
    Represents a specific time slot on a given day.
    """
    day: Literal["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    start: str  # Format: "HH:MM", e.g., "08:00"
    end: str    # Format: "HH:MM", e.g., "10:00"

# ========== Session Patterns ==========

class FixedSessionPattern(BaseModel):
    """
    Represents a fixed pattern with exactly 2 weekly sessions.
    """
    slots: List[TimeSlot]

    @model_validator(mode='after')
    def check_two_slots(cls, model):
        if len(model.slots) != 2:
            raise ValueError("FixedSessionPattern must have exactly 2 slots")
        return model


class AlternatingSessionPattern(BaseModel):
    """
    Represents a pattern where a course alternates between two slots weekly.
    Paired with another course (by course_id), and occurs on even or odd weeks.
    """
    fixed_slot: TimeSlot
    alternating_slot: TimeSlot
    alternating_mode: Literal["odd", "even"]
    paired_course_id: int


class SessionPattern(BaseModel):
    """
    Wraps either a fixed or alternating session pattern.
    Only one of the patterns must be set based on the type.
    """
    type: Literal["fixed", "alternating"]
    fixed_pattern: Optional[FixedSessionPattern] = None
    alternating_pattern: Optional[AlternatingSessionPattern] = None

    @model_validator(mode='after')
    def validate_only_one_pattern(cls, model):
        pattern_type = model.type
        fixed = model.fixed_pattern
        alternating = model.alternating_pattern

        if pattern_type == "fixed":
            if not fixed or alternating:
                raise ValueError("For type='fixed', only fixed_pattern must be set")
        elif pattern_type == "alternating":
            if not alternating or fixed:
                raise ValueError("For type='alternating', only alternating_pattern must be set")
        else:
            raise ValueError("Invalid session pattern type")

        return model

# ========== Course ==========

class Course(BaseModel):
    """
    Represents a course that may or may not include a lab.
    Lab courses must define a lab slot and cannot have a session pattern.
    Non-lab courses must define a session pattern and cannot have a lab slot.
    """
    id: int
    name: str
    code: str
    instructor_id: int

    has_lab: bool = False
    lab_slot: Optional[TimeSlot] = None
    lab_room_id: Optional[int] = None
    lab_instructor_id: Optional[int] = None

    session_pattern: Optional[SessionPattern] = None

    @model_validator(mode='after')
    def validate_course(cls, model):
        has_lab = model.has_lab
        lab_slot = model.lab_slot
        session_pattern = model.session_pattern

        if has_lab:
            if not lab_slot:
                raise ValueError("Lab slot must be defined for lab courses")
            if session_pattern:
                raise ValueError("Lab courses must not have session pattern")
        else:
            if not session_pattern:
                raise ValueError("Non-lab courses must have a session pattern")
            if lab_slot:
                raise ValueError("Non-lab courses must not have lab slot")

        return model

# ========== Student ==========

class Student(BaseModel):
    """
    Represents a student belonging to a specific group.
    """
    full_name: str
    student_number: str  # e.g., "401234567"
    group_id: int        # Refers to StudentGroup.id

# ========== StudentGroup ==========

class StudentGroup(BaseModel):
    """
    Represents a group of students (e.g., a class or cohort).
    """
    id: int
    name: str        # e.g., "CS-401"
    major: str       # e.g., "Computer Engineering"
    entry_year: int  # e.g., 2022

# ========== Instructor ==========

class Instructor(BaseModel):
    """
    Represents an instructor with available and preferred time slots.
    """
    id: int
    full_name: str
    available_slots: List[TimeSlot]                 # Instructor is only assignable within these slots
    preferred_slots: Optional[List[TimeSlot]] = None  # Soft preference (optional)

# ========== Room ==========

class Room(BaseModel):
    """
    Represents a classroom or lab with capacity constraints.
    """
    id: int
    name: str        # e.g., "Room 101"
    capacity: int    # Max number of students
    is_lab: bool = False  # True if lab; used only for lab courses

# ========== Scheduled Session & Timetable ==========

class ScheduledSession(BaseModel):
    """
    Represents a scheduled class session (theory or lab).
    """
    course_id: int         # ID of the course being taught
    group_id: int          # ID of the student group attending the session
    instructor_id: int     # ID of the instructor assigned to this session
    room_id: int           # ID of the room assigned for this session
    slot: TimeSlot         # Scheduled time slot for the session
    type: Literal["theory", "lab"]  # Type of session (theory or lab)

class Timetable(BaseModel):
    """
    Represents the final schedule as a list of sessions.
    This is the output of the scheduling algorithm.
    """
    sessions: List[ScheduledSession]
