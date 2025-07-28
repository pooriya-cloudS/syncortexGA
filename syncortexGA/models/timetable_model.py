from pydantic import BaseModel, model_validator, StringConstraints, ConfigDict
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


class LabSessionPattern(BaseModel):
    """
    Represents a lab session pattern that occurs weekly at a fixed time.
    This is used for lab courses that do not have a session pattern.
    """

    slot: TimeSlot

    @model_validator(mode="after")
    def check_single_slot(cls, model):
        if not model.slot:
            raise ValueError("LabSessionPattern must have exactly 1 slot")
        return model


class SessionPattern(BaseModel):
    """
    Wraps either a fixed or alternating session pattern.
    Only one of the patterns must be set based on the type.
    """

    type: Literal["fixed", "alternating", "lab"]
    fixed_pattern: Optional[FixedSessionPattern] = None
    alternating_pattern: Optional[AlternatingSessionPattern] = None
    lab_pattern: Optional[LabSessionPattern] = None

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
        elif model.type == "lab":
            if (
                not model.lab_pattern
                or model.fixed_pattern
                or model.alternating_pattern
            ):
                raise ValueError("For type='lab', only lab_pattern must be set")
        return model


# ========== StudentGroup ==========
class StudentGroup(BaseModel):
    """Represents a group of students (e.g., a class or cohort)."""

    id: int
    name: str  # e.g., "CS-401"
    major: str  # e.g., "Computer Engineering"
    entry_year: int  # e.g., 2022


# ========== Student ==========
class Student(BaseModel):
    """Represents a student belonging to a specific group."""

    full_name: str
    student_number: str  # e.g., "401234567"
    group_id: StudentGroup  # Refers to StudentGroup.id


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
    # has_lab: bool = False
    # lab_room_id: Optional[int] = None
    session_pattern: Optional[SessionPattern] = None


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

    course_id: Course
    instructor_id: Instructor
    sub_group: int = 1  # Default subgroup is 1


# ========== Scheduled Session & Timetable ==========
class ScheduledSession(BaseModel):
    """Represents a scheduled class session (theory or lab)."""

    course_id: Course
    group_id: StudentGroup
    instructor_id: Instructor
    room_id: Room
    slot: TimeSlot
    type: Literal["theory", "lab"]

    @model_validator(mode="after")
    def validate_slot(cls, model):
        if model.type == "lab" and not model.course_id.session_pattern:
            raise ValueError("Lab sessions must have a lab session pattern defined")
        elif model.type == "theory" and not model.course_id.session_pattern:
            raise ValueError("Theory sessions must have a session pattern defined")
        elif model.type not in ("theory", "lab"):
            raise ValueError("Session type must be either 'theory' or 'lab'")
        return model



class Timetable(BaseModel):
    """Represents the final schedule as a list of sessions."""

    sessions: List[ScheduledSession]
