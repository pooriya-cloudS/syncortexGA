import pytest
from syncortexGA.models.timetable_model import (
    TimeSlot,
    Instructor,
    StudentGroup,
    Room,
    Course,
    SessionPattern,
    FixedSessionPattern,
    LabSessionPattern,
    ScheduledSession,
    Timetable,
)
from syncortexGA.constraints.hard_constraints import check_h1_instructor_conflicts


# ---------- Common Fixtures ----------


@pytest.fixture
def common_setup():
    """
    Creates a standard setup of group, room, instructor, course, and time slots
    used in multiple tests.
    """
    group = StudentGroup(id=1, name="CS-A", major="CS", entry_year=2023)

    room = Room(id=1, name="Room 101", capacity=40, is_lab=False)

    slot1 = TimeSlot(day="Saturday", start="08:00", end="10:00")
    slot2 = TimeSlot(day="Saturday", start="10:00", end="12:00")
    slot3 = TimeSlot(day="Sunday", start="08:00", end="10:00")  # Not available

    instructor = Instructor(
        id=1,
        full_name="Dr. Smith",
        available_slots=[slot1, slot2],  # Only slot1 and slot2 are allowed
        preferred_slots=None,
    )

    course = Course(
        id=1,
        name="Algorithms",
        code="CS101",
        session_pattern=SessionPattern(
            type="fixed", fixed_pattern=FixedSessionPattern(slots=[slot1, slot2])
        ),
    )

    return group, room, instructor, course, slot1, slot2, slot3


# ---------- Test Cases for H1 ----------


def test_h1_valid_schedule(common_setup):
    """
    Test: Instructor has two valid sessions with no slot conflict.
    Expect: H1 passes (returns True)
    """
    group, room, instructor, course, slot1, slot2, _ = common_setup

    sessions = [
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor,
            room_id=room,
            slot=slot1,
            type="theory",
        ),
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor,
            room_id=room,
            slot=slot2,
            type="theory",
        ),
    ]

    timetable = Timetable(sessions=sessions)
    assert check_h1_instructor_conflicts(timetable) is True


def test_h1_invalid_due_to_slot_not_in_available(common_setup):
    """
    Test: Instructor is scheduled in a slot not listed in available_slots.
    Expect: H1 fails (returns False)
    """
    group, room, instructor, course, _, _, slot3 = common_setup  # slot3 is invalid

    session = ScheduledSession(
        course_id=course,
        group_id=group,
        instructor_id=instructor,
        room_id=room,
        slot=slot3,
        type="theory",
    )

    timetable = Timetable(sessions=[session])
    assert check_h1_instructor_conflicts(timetable) is False


def test_h1_invalid_due_to_slot_conflict(common_setup):
    """
    Test: Instructor has two sessions scheduled in the exact same time slot.
    Expect: H1 fails (returns False)
    """
    group, room, instructor, course, slot1, _, _ = common_setup

    sessions = [
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor,
            room_id=room,
            slot=slot1,
            type="theory",
        ),
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor,
            room_id=room,
            slot=slot1,
            type="theory",
        ),  # Conflict
    ]

    timetable = Timetable(sessions=sessions)
    assert check_h1_instructor_conflicts(timetable) is False


def test_h1_multiple_instructors_no_conflict():
    """
    Test: Two instructors teaching different sessions at the same time.
    Expect: H1 passes (returns True) — conflict is per instructor, not globally
    """
    slot = TimeSlot(day="Monday", start="10:00", end="12:00")

    instructor1 = Instructor(id=1, full_name="A", available_slots=[slot])
    instructor2 = Instructor(id=2, full_name="B", available_slots=[slot])

    group = StudentGroup(id=1, name="G1", major="CS", entry_year=2023)
    room = Room(id=1, name="Room A", capacity=30, is_lab=False)

    course = Course(
        id=1,
        name="CS",
        code="CS101",
        session_pattern=SessionPattern(
            type="lab", lab_pattern=LabSessionPattern(slot=slot)
        ),
    )

    sessions = [
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor1,
            room_id=room,
            slot=slot,
            type="lab",
        ),
        ScheduledSession(
            course_id=course,
            group_id=group,
            instructor_id=instructor2,
            room_id=room,
            slot=slot,
            type="lab",
        ),
    ]

    timetable = Timetable(sessions=sessions)
    assert check_h1_instructor_conflicts(timetable) is True
