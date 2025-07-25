import pytest
from pydantic import ValidationError
from syncortexGA.models.timetable_model import (
    TimeSlot,
    FixedSessionPattern,
    AlternatingSessionPattern,
    SessionPattern,
    Course,
    CourseOffering,
    Student,
    StudentGroup,
    Instructor,
    Room,
    ScheduledSession,
    Timetable,
)


# ====== TimeSlot Tests ======


def test_timeslot_valid():
    ts = TimeSlot(day="Monday", start="08:00", end="10:00")
    assert ts.day == "Monday"
    assert ts.start == "08:00"
    assert ts.end == "10:00"


def test_timeslot_invalid_day():
    with pytest.raises(ValidationError):
        TimeSlot(day="Friday", start="08:00", end="10:00")


def test_timeslot_invalid_time_format():
    with pytest.raises(ValidationError):
        TimeSlot(day="Monday", start="8am", end="10am")


# ====== FixedSessionPattern Tests ======


def test_fixed_session_pattern_valid():
    slots = [
        TimeSlot(day="Saturday", start="08:00", end="10:00"),
        TimeSlot(day="Monday", start="10:00", end="12:00"),
    ]
    pattern = FixedSessionPattern(slots=slots)
    assert len(pattern.slots) == 2


def test_fixed_session_pattern_invalid_count():
    with pytest.raises(ValidationError):
        FixedSessionPattern(
            slots=[TimeSlot(day="Saturday", start="08:00", end="10:00")]
        )


def test_fixed_session_pattern_empty():
    with pytest.raises(ValidationError):
        FixedSessionPattern(slots=[])


# ====== AlternatingSessionPattern Tests ======


def test_alternating_session_pattern_valid():
    pattern = AlternatingSessionPattern(
        fixed_slot=TimeSlot(day="Sunday", start="08:00", end="10:00"),
        alternating_slot=TimeSlot(day="Tuesday", start="10:00", end="12:00"),
        alternating_mode="odd",
        paired_course_id=123,
    )
    assert pattern.alternating_mode == "odd"


def test_alternating_session_pattern_invalid_mode():
    with pytest.raises(ValidationError):
        AlternatingSessionPattern(
            fixed_slot=TimeSlot(day="Sunday", start="08:00", end="10:00"),
            alternating_slot=TimeSlot(day="Tuesday", start="10:00", end="12:00"),
            alternating_mode="week3",
            paired_course_id=123,
        )


# ====== SessionPattern Tests ======


def test_session_pattern_fixed_valid():
    fixed = FixedSessionPattern(
        slots=[
            TimeSlot(day="Saturday", start="08:00", end="10:00"),
            TimeSlot(day="Monday", start="10:00", end="12:00"),
        ]
    )
    sp = SessionPattern(type="fixed", fixed_pattern=fixed)
    assert sp.type == "fixed"


def test_session_pattern_alternating_valid():
    alt = AlternatingSessionPattern(
        fixed_slot=TimeSlot(day="Sunday", start="08:00", end="10:00"),
        alternating_slot=TimeSlot(day="Tuesday", start="10:00", end="12:00"),
        alternating_mode="even",
        paired_course_id=99,
    )
    sp = SessionPattern(type="alternating", alternating_pattern=alt)
    assert sp.type == "alternating"


def test_session_pattern_invalid_type():
    with pytest.raises(ValidationError):
        SessionPattern(type="random")


def test_session_pattern_mismatch_fixed():
    fixed = FixedSessionPattern(
        slots=[
            TimeSlot(day="Saturday", start="08:00", end="10:00"),
            TimeSlot(day="Monday", start="10:00", end="12:00"),
        ]
    )
    alt = AlternatingSessionPattern(
        fixed_slot=fixed.slots[0],
        alternating_slot=fixed.slots[1],
        alternating_mode="odd",
        paired_course_id=5,
    )
    with pytest.raises(ValidationError):
        SessionPattern(type="fixed", fixed_pattern=fixed, alternating_pattern=alt)


def test_session_pattern_mismatch_alternating():
    fixed = FixedSessionPattern(
        slots=[
            TimeSlot(day="Saturday", start="08:00", end="10:00"),
            TimeSlot(day="Monday", start="10:00", end="12:00"),
        ]
    )
    with pytest.raises(ValidationError):
        SessionPattern(type="alternating", fixed_pattern=fixed)


# ====== Course Tests ======


def test_course_lab_valid():
    course = Course(
        id=1,
        name="Physics Lab",
        code="PHY101",
        instructor_id=10,
        has_lab=True,
        lab_slot=TimeSlot(day="Wednesday", start="14:00", end="16:00"),
        lab_room_id=3,
        lab_instructor_id=15,
    )
    assert course.has_lab is True


def test_course_lab_missing_lab_slot():
    with pytest.raises(ValidationError):
        Course(
            id=2, name="Chemistry Lab", code="CHEM101", instructor_id=11, has_lab=True
        )


def test_course_lab_with_session_pattern():
    lab_slot = TimeSlot(day="Wednesday", start="14:00", end="16:00")
    session_pattern = SessionPattern(
        type="fixed",
        fixed_pattern=FixedSessionPattern(
            slots=[
                TimeSlot(day="Monday", start="08:00", end="10:00"),
                TimeSlot(day="Thursday", start="08:00", end="10:00"),
            ]
        ),
    )
    with pytest.raises(ValidationError):
        Course(
            id=3,
            name="Bio Lab",
            code="BIO101",
            instructor_id=12,
            has_lab=True,
            lab_slot=lab_slot,
            session_pattern=session_pattern,
        )


def test_course_non_lab_valid():
    session_pattern = SessionPattern(
        type="fixed",
        fixed_pattern=FixedSessionPattern(
            slots=[
                TimeSlot(day="Monday", start="08:00", end="10:00"),
                TimeSlot(day="Thursday", start="08:00", end="10:00"),
            ]
        ),
    )
    course = Course(
        id=4,
        name="Math",
        code="MATH101",
        instructor_id=13,
        has_lab=False,
        session_pattern=session_pattern,
    )
    assert course.has_lab is False


def test_course_non_lab_missing_session_pattern():
    with pytest.raises(ValidationError):
        Course(id=5, name="History", code="HIST101", instructor_id=14, has_lab=False)


def test_course_non_lab_with_lab_slot():
    with pytest.raises(ValidationError):
        Course(
            id=6,
            name="English",
            code="ENG101",
            instructor_id=15,
            has_lab=False,
            lab_slot=TimeSlot(day="Wednesday", start="14:00", end="16:00"),
        )


# ====== Student Tests ======


def test_student_valid():
    student = Student(full_name="Alice Smith", student_number="401234567", group_id=100)
    assert student.student_number == "401234567"


def test_student_missing_field():
    with pytest.raises(ValidationError):
        Student(full_name="Bob")


# ====== StudentGroup Tests ======


def test_student_group_valid():
    group = StudentGroup(
        id=1, name="CS-401", major="Computer Engineering", entry_year=2023
    )
    assert group.name == "CS-401"


# ====== Instructor Tests ======


def test_instructor_valid():
    instructor = Instructor(
        id=1,
        full_name="Dr. John",
        available_slots=[TimeSlot(day="Monday", start="08:00", end="12:00")],
        preferred_slots=[TimeSlot(day="Monday", start="10:00", end="12:00")],
    )
    assert instructor.full_name == "Dr. John"


def test_instructor_no_preferred():
    instructor = Instructor(
        id=2,
        full_name="Dr. Jane",
        available_slots=[TimeSlot(day="Tuesday", start="08:00", end="10:00")],
    )
    assert instructor.preferred_slots is None


# ====== Room Tests ======


def test_room_valid():
    room = Room(id=1, name="Room 101", capacity=30, is_lab=False)
    assert room.capacity == 30


def test_room_lab_flag():
    room = Room(id=2, name="Lab 1", capacity=20, is_lab=True)
    assert room.is_lab is True


# ====== ScheduledSession Tests ======


def test_scheduled_session_valid():
    session = ScheduledSession(
        course_id=1,
        group_id=10,
        instructor_id=5,
        room_id=3,
        slot=TimeSlot(day="Thursday", start="10:00", end="12:00"),
        type="theory",
    )
    assert session.type == "theory"


def test_scheduled_session_invalid_type():
    with pytest.raises(ValidationError):
        ScheduledSession(
            course_id=1,
            group_id=10,
            instructor_id=5,
            room_id=3,
            slot=TimeSlot(day="Thursday", start="10:00", end="12:00"),
            type="exam",
        )


# ====== Timetable Tests ======


def test_timetable_valid():
    session = ScheduledSession(
        course_id=1,
        group_id=10,
        instructor_id=5,
        room_id=3,
        slot=TimeSlot(day="Thursday", start="10:00", end="12:00"),
        type="lab",
    )
    timetable = Timetable(sessions=[session])
    assert len(timetable.sessions) == 1


def test_timetable_empty():
    timetable = Timetable(sessions=[])
    assert timetable.sessions == []


def test_course_offering_valid_defaults():
    offering = CourseOffering(course_id=10, instructor_id=5)
    assert offering.course_id == 10
    assert offering.instructor_id == 5
    assert offering.sub_group == 1  # Default value


def test_course_offering_valid_with_subgroup():
    offering = CourseOffering(course_id=20, instructor_id=7, sub_group=3)
    assert offering.course_id == 20
    assert offering.instructor_id == 7
    assert offering.sub_group == 3


def test_course_offering_invalid_missing_course_id():
    with pytest.raises(ValidationError):
        CourseOffering(instructor_id=1)


def test_course_offering_invalid_missing_instructor_id():
    with pytest.raises(ValidationError):
        CourseOffering(course_id=1)


def test_course_offering_invalid_sub_group_type():
    # sub_group should be int
    with pytest.raises(ValidationError):
        CourseOffering(course_id=1, instructor_id=1, sub_group="two")
