from pydantic import BaseModel, model_validator, StringConstraints
from typing import List, Optional, Literal, Annotated

# Accepts only time strings in 24-hour format like "08:00", "23:59"
TimeStr = Annotated[str, StringConstraints(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]


# ========== TimeSlot ==========
class TimeSlot(BaseModel):
    """Represents a specific time slot on a given day."""

    day: Literal["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    start: TimeStr  # Format: "HH:MM"
    end: TimeStr  # Format: "HH:MM"


# ========== Session Patterns ==========
class FixedSessionPattern(BaseModel):
    """Represents a fixed pattern with exactly 2 weekly sessions."""

    slots: List[TimeSlot]

    @model_validator(mode="after")
    def check_two_slots(cls, model):
        if len(model.slots) != 2:
            raise ValueError("FixedSessionPattern must have exactly 2 slots")
        return model


class AlternatingSessionPattern(BaseModel):
    """
    Represents a pattern where a course alternates between two slots weekly.
    Paired with another course and occurs on even or odd weeks.
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

    @model_validator(mode="after")
    def validate_only_one_pattern(cls, model):
        if model.type == "fixed":
            if not model.fixed_pattern or model.alternating_pattern:
                raise ValueError("For type='fixed', only fixed_pattern must be set")
        elif model.type == "alternating":
            if not model.alternating_pattern or model.fixed_pattern:
                raise ValueError(
                    "For type='alternating', " "only alternating_pattern must be set"
                )
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
    session_pattern: Optional[SessionPattern] = None

    @model_validator(mode="after")
    def validate_course(cls, model):
        if model.has_lab:
            if not model.lab_slot:
                raise ValueError("Lab slot must be defined for lab courses")
            if model.session_pattern:
                raise ValueError("Lab courses must not have session pattern")
        else:
            if not model.session_pattern:
                raise ValueError("Non-lab courses must have a session pattern")
            if model.lab_slot:
                raise ValueError("Non-lab courses must not have lab slot")
        return model


class CourseOffering(BaseModel):
    """
    Represents the offering of a course by an instructor for a specific subgroup.
    Allows multiple instructors to offer the same course to different subgroups,
    and a single instructor to teach the same course in multiple subgroups.

    Attributes:
        course_id (int): Identifier of the course being offered.
        instructor_id (int): Identifier of the instructor teaching the course.
        sub_group (int): Sub-group number within the course offering. Default is 1.
    """

    course_id: int
    instructor_id: int
    sub_group: int = 1  # Default subgroup is 1


# ========== Student ==========
class Student(BaseModel):
    """Represents a student belonging to a specific group."""

    full_name: str
    student_number: str  # e.g., "401234567"
    group_id: int  # Refers to StudentGroup.id


# ========== StudentGroup ==========
class StudentGroup(BaseModel):
    """Represents a group of students (e.g., a class or cohort)."""

    id: int
    name: str  # e.g., "CS-401"
    major: str  # e.g., "Computer Engineering"
    entry_year: int  # e.g., 2022


# ========== Instructor ==========
class Instructor(BaseModel):
    """Represents an instructor with available and preferred time slots."""

    id: int
    full_name: str
    available_slots: List[TimeSlot]
    preferred_slots: Optional[List[TimeSlot]] = None


# ========== Room ==========
class Room(BaseModel):
    """Represents a classroom or lab with capacity constraints."""

    id: int
    name: str  # e.g., "Room 101"
    capacity: int
    is_lab: bool = False


# ========== Scheduled Session & Timetable ==========
class ScheduledSession(BaseModel):
    """Represents a scheduled class session (theory or lab)."""

    course_id: int
    group_id: int
    instructor_id: int
    room_id: int
    slot: TimeSlot
    type: Literal["theory", "lab"]


class Timetable(BaseModel):
    """Represents the final schedule as a list of sessions."""

    sessions: List[ScheduledSession]
