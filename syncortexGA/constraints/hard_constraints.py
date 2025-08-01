from syncortexGA.models.timetable_model import Timetable


def check_h1_instructor_conflicts(timetable: Timetable) -> bool:
    """
    Ensures no instructor is scheduled for more than one session at the same time
    and only in their available time slots.
    """
    seen = {}  # key: (instructor_id, day, start, end), value: count

    for session in timetable.sessions:
        instructor = session.instructor_id
        slot = session.slot

        # 1. Check if the session is in instructor's available slots
        if slot not in instructor.available_slots:
            return False

        # 2. Check if this slot already assigned to this instructor
        key = (instructor.id, slot.day, slot.start, slot.end)
        if key in seen:
            return (
                False  # Conflict detected: instructor already has session in this slot
            )
        seen[key] = True

    return True
