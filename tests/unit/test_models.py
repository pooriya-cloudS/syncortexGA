import pytest
from pydantic import ValidationError
from syncortexGA.models.timetable_model import (
    TimeSlot,
    FixedSessionPattern,
    AlternatingSessionPattern,
    LabSessionPattern,
    SessionPattern,
    StudentGroup,
    Student,
    Instructor,
    Room,
    Course,
    CourseOffering,
    ScheduledSession,
    Timetable,
)


# ==== Helper functions to create reusable sample data ====


def sample_timeslot(day="Monday", start="08:00", end="10:00"):
    return TimeSlot(day=day, start=start, end=end)


def sample_student_group():
    return StudentGroup(
        id=1, name="CS-401", major="Computer Engineering", entry_year=2022
    )


def sample_instructor():
    return Instructor(
        id=1,
        full_name="Dr. Smith",
        available_slots=[sample_timeslot()],
        preferred_slots=[sample_timeslot("Tuesday", "10:00", "12:00")],
    )


def sample_room():
    return Room(id=1, name="Room 101", capacity=40, is_lab=False)


def sample_fixed_session_pattern():
    return FixedSessionPattern(
        slots=[
            sample_timeslot("Saturday", "08:00", "10:00"),
            sample_timeslot("Monday", "10:00", "12:00"),
        ]
    )


def sample_alternating_session_pattern():
    return AlternatingSessionPattern(
        fixed_slot=sample_timeslot("Sunday", "08:00", "10:00"),
        alternating_slot=sample_timeslot("Tuesday", "10:00", "12:00"),
        alternating_mode="odd",
        paired_course_id=123,
    )


def sample_lab_session_pattern():
    return LabSessionPattern(slot=sample_timeslot("Wednesday", "14:00", "16:00"))


def sample_session_pattern_fixed():
    return SessionPattern(type="fixed", fixed_pattern=sample_fixed_session_pattern())


def sample_session_pattern_alternating():
    return SessionPattern(
        type="alternating", alternating_pattern=sample_alternating_session_pattern()
    )


def sample_session_pattern_lab():
    return SessionPattern(type="lab", lab_pattern=sample_lab_session_pattern())


def sample_course_with_pattern(session_pattern=None):
    return Course(
        id=1,
        name="Advanced Mathematics",
        code="MATH401",
        session_pattern=session_pattern,
    )


def sample_course_without_pattern():
    return Course(id=2, name="Philosophy", code="PHIL101", session_pattern=None)


def sample_course_offering(course=None, instructor=None, sub_group=1):
    return CourseOffering(
        course_id=course, instructor_id=instructor, sub_group=sub_group
    )


def sample_scheduled_session():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    group = sample_student_group()
    instructor = sample_instructor()
    room = sample_room()
    slot = sample_timeslot()
    return ScheduledSession(
        course_id=course,
        group_id=group,
        instructor_id=instructor,
        room_id=room,
        slot=slot,
        type="theory",
    )


# ==== Tests ====


# ----- TimeSlot -----
def test_timeslot_valid():
    ts = sample_timeslot()
    assert ts.day == "Monday"
    assert ts.start == "08:00"
    assert ts.end == "10:00"


def test_timeslot_invalid_day():
    with pytest.raises(ValidationError):
        TimeSlot(day="Friday", start="08:00", end="10:00")  # Friday not allowed


def test_timeslot_invalid_time_format():
    with pytest.raises(ValidationError):
        TimeSlot(day="Monday", start="8am", end="10:00")


# ----- FixedSessionPattern -----
def test_fixed_session_pattern_valid():
    pattern = sample_fixed_session_pattern()
    assert len(pattern.slots) == 2


def test_fixed_session_pattern_invalid_count():
    with pytest.raises(ValidationError):
        FixedSessionPattern(slots=[sample_timeslot()])


def test_fixed_session_pattern_empty():
    with pytest.raises(ValidationError):
        FixedSessionPattern(slots=[])


# ----- AlternatingSessionPattern -----
def test_alternating_session_pattern_valid():
    pattern = sample_alternating_session_pattern()
    assert pattern.alternating_mode in ("odd", "even")


def test_alternating_session_pattern_invalid_mode():
    with pytest.raises(ValidationError):
        AlternatingSessionPattern(
            fixed_slot=sample_timeslot(),
            alternating_slot=sample_timeslot(),
            alternating_mode="weekly",
            paired_course_id=1,
        )


# ----- LabSessionPattern -----
def test_lab_session_pattern_valid():
    pattern = sample_lab_session_pattern()
    assert pattern.slot.day == "Wednesday"


def test_lab_session_pattern_invalid_missing_slot():
    with pytest.raises(ValidationError):
        LabSessionPattern(slot=None)


# ----- SessionPattern -----
def test_session_pattern_fixed_valid():
    sp = sample_session_pattern_fixed()
    assert sp.type == "fixed"
    assert sp.fixed_pattern is not None
    assert sp.alternating_pattern is None
    assert sp.lab_pattern is None


def test_session_pattern_alternating_valid():
    sp = sample_session_pattern_alternating()
    assert sp.type == "alternating"
    assert sp.alternating_pattern is not None


def test_session_pattern_lab_valid():
    sp = sample_session_pattern_lab()
    assert sp.type == "lab"
    assert sp.lab_pattern is not None


def test_session_pattern_invalid_type():
    with pytest.raises(ValidationError):
        SessionPattern(type="random")


def test_session_pattern_mismatched_patterns():
    fixed = sample_fixed_session_pattern()
    alt = sample_alternating_session_pattern()
    lab = sample_lab_session_pattern()

    # fixed type but alternating pattern set
    with pytest.raises(ValidationError):
        SessionPattern(
            type="fixed", fixed_pattern=fixed, alternating_pattern=alt, lab_pattern=lab
        )

    # alternating type but fixed pattern set
    with pytest.raises(ValidationError):
        SessionPattern(type="alternating", fixed_pattern=fixed)

    # lab type but fixed pattern set
    with pytest.raises(ValidationError):
        SessionPattern(type="lab", fixed_pattern=fixed)

    # lab type but alternating pattern set
    with pytest.raises(ValidationError):
        SessionPattern(type="lab", alternating_pattern=alt)


# ----- StudentGroup -----
def test_student_group_valid():
    group = sample_student_group()
    assert group.name == "CS-401"


# ----- Student -----
def test_student_valid():
    group = sample_student_group()
    student = Student(
        full_name="Alice Smith", student_number="401234567", group_id=group
    )
    assert student.group_id.id == group.id


def test_student_missing_fields():
    with pytest.raises(ValidationError):
        Student(full_name="Bob")


# ----- Instructor -----
def test_instructor_valid():
    instructor = sample_instructor()
    assert instructor.full_name == "Dr. Smith"
    assert len(instructor.available_slots) == 1


def test_instructor_optional_preferred_slots():
    inst = Instructor(id=2, full_name="Jane Doe", available_slots=[sample_timeslot()])
    assert inst.preferred_slots is None


# ----- Room -----
def test_room_valid():
    room = sample_room()
    assert room.capacity == 40
    assert room.is_lab is False


def test_room_lab_flag_true():
    room = Room(id=10, name="Lab 1", capacity=20, is_lab=True)
    assert room.is_lab is True


# ----- Course -----
def test_course_with_valid_session_pattern():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    assert course.session_pattern is not None


def test_course_without_session_pattern():
    course = sample_course_without_pattern()
    assert course.session_pattern is None


# ----- CourseOffering -----
def test_course_offering_valid_default_subgroup():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    instructor = sample_instructor()
    offering = sample_course_offering(course=course, instructor=instructor)
    assert offering.sub_group == 1


def test_course_offering_valid_custom_subgroup():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    instructor = sample_instructor()
    offering = sample_course_offering(course=course, instructor=instructor, sub_group=3)
    assert offering.sub_group == 3


def test_course_offering_missing_course_id():
    instructor = sample_instructor()
    with pytest.raises(ValidationError):
        CourseOffering(instructor_id=instructor)


def test_course_offering_missing_instructor_id():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    with pytest.raises(ValidationError):
        CourseOffering(course_id=course)


def test_course_offering_invalid_subgroup_type():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    instructor = sample_instructor()
    with pytest.raises(ValidationError):
        CourseOffering(course_id=course, instructor_id=instructor, sub_group="two")


# ----- ScheduledSession -----
def test_scheduled_session_valid():
    session = sample_scheduled_session()
    assert session.type in ("theory", "lab")


def test_scheduled_session_invalid_type():
    course = sample_course_with_pattern(sample_session_pattern_fixed())
    group = sample_student_group()
    instructor = sample_instructor()
    room = sample_room()
    slot = sample_timeslot()
    with pytest.raises(ValidationError):
        sess = ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor,
            room_id=room,
            slot=slot,
            type="exam",
        )


# ----- Timetable -----
def test_timetable_valid():
    session = sample_scheduled_session()
    timetable = Timetable(sessions=[session])
    assert len(timetable.sessions) == 1


def test_timetable_empty():
    timetable = Timetable(sessions=[])
    assert timetable.sessions == []
