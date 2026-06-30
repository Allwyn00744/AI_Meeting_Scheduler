from app.models.meeting import Meeting


class ConflictService:

    @staticmethod
    def has_time_conflict(
        start_time,
        end_time,
        meetings: list[Meeting],
    ):
        for meeting in meetings:
            if (
                start_time < meeting.end_time
                and end_time > meeting.start_time
            ):
                return True, meeting

        return False, None