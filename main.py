from datetime import datetime

from rich.console import Console
from tabulate import tabulate


def generate_weekly_schedule_transpose_12hr(schedule_dict, start_day="Monday"):
    """
    Generates a transposed weekly work schedule table (time rows, day columns) with 12-hour AM/PM format.

    Args:
        schedule_dict (dict): A dictionary where keys are day names (e.g., "Monday")
                             and values are lists of tuples representing time slots.
                             Example: {"Monday": [("09:00 AM", "05:00 PM")], "Tuesday": [("10:00 AM", "04:00 PM"), ("06:00 PM", "08:00 PM")]}
        start_day (str): The day to start the week (default is "Monday").

    Returns:
        str: A string representing the transposed weekly schedule table.
    """

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Reorder days if a different start day is specified
    start_index = days.index(start_day)
    days = days[start_index:] + days[:start_index]

    time_slots = []
    for day in days:
        if day in schedule_dict:
            for start, end in schedule_dict[day]:
                start_time = datetime.strptime(start, "%I:%M %p").time()
                end_time = datetime.strptime(end, "%I:%M %p").time()
                time_slots.extend([(day, start_time, end_time)])
        else:
            time_slots.append(
                (
                    day,
                    datetime.strptime("12:00 AM", "%I:%M %p").time(),
                    datetime.strptime("12:00 AM", "%I:%M %p").time(),
                )
            )

    # Determine the earliest and latest hours
    earliest_hour = min(
        slot[1].hour
        for slot in time_slots
        if slot[1] != datetime.strptime("12:00 AM", "%I:%M %p").time()
    )
    latest_hour = (
        max(
            slot[2].hour
            for slot in time_slots
            if slot[2] != datetime.strptime("12:00 AM", "%I:%M %p").time()
        )
        + 1
    )

    # Create time rows
    time_rows = []
    for hour in range(earliest_hour, latest_hour):
        time_format = "%I:00 %p" if hour != 0 else "%I:00 AM"  # midnight edge case.
        time_rows.append(datetime(1900, 1, 1, hour).strftime(time_format))

    # Create the table data (transposed)
    table_data = []
    for time_str in time_rows:
        row = [time_str]
        hour = (
            datetime.strptime(time_str, "%I:00 %p").hour
            if time_str != "12:00 AM"
            else 0
        )
        for day in days:
            is_scheduled = False
            if day in schedule_dict:
                for start, end in schedule_dict[day]:
                    start_time = datetime.strptime(start, "%I:%M %p").time()
                    end_time = datetime.strptime(end, "%I:%M %p").time()
                    if start_time.hour <= hour < end_time.hour:
                        is_scheduled = True
                        break
                    elif start_time.hour == hour and start_time.minute == 0:
                        is_scheduled = True
                        break
            row.append("██████████" if is_scheduled else "")  # full block
        table_data.append(row)

    # Generate the transposed table string
    table_string = tabulate(table_data, headers=["Time"] + days, tablefmt="grid")
    return table_string


def main():
    console = Console()

    # Example usage
    schedule = {
        "Monday": [("09:00 AM", "05:00 PM")],
        "Tuesday": [("10:00 AM", "04:00 PM"), ("06:00 PM", "08:00 PM")],
        "Wednesday": [("09:00 AM", "05:00 PM")],
        "Thursday": [("09:00 AM", "05:00 PM")],
        "Friday": [("09:00 AM", "01:00 PM")],
    }

    table_string = generate_weekly_schedule_transpose_12hr(schedule)
    # Print the table to the console
    # console.print(table_string)

    schedule2 = {
        "Wednesday": [("12:00 PM", "09:00 PM")],
        "Friday": [("08:00 AM", "04:00 PM")],
    }

    table_string = generate_weekly_schedule_transpose_12hr(schedule2, "Wednesday")
    console.print(table_string)


if __name__ == "__main__":
    main()
