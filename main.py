from datetime import datetime

import loguru
from fpdf import FPDF
from rich.console import Console
from tabulate import tabulate

from completion import GEMINI_API_KEY, GeminiTextGenerator

logger = loguru.logger
console = Console()


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
            cell_content = ""  # Default empty cell
            if day in schedule_dict:
                for start, end in schedule_dict[day]:
                    start_time = datetime.strptime(start, "%I:%M %p").time()
                    end_time = datetime.strptime(end, "%I:%M %p").time()
                    # Check if the current hour falls within the scheduled time
                    if start_time.hour <= hour < end_time.hour:
                        if start_time.hour == hour and start_time.minute == 30:
                            cell_content = "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄"  # Starts at half-hour
                        elif end_time.hour == hour + 1 and end_time.minute == 30:
                            cell_content = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"  # Ends at half-hour
                        else:
                            cell_content = "█████████████████"  # Full block
                        break
                    # Check if the current hour is the start time
                    elif start_time.hour == hour and start_time.minute == 0:
                        cell_content = "█████████████████"  # Full block
                        break

            row.append(cell_content)
        table_data.append(row)
    # Generate the transposed table string
    table_string = tabulate(table_data, headers=["Time"] + days, tablefmt="grid")
    return table_string


def generate_schedule_from_instructions(notes: str = "") -> dict:
    generator = GeminiTextGenerator(api_key=GEMINI_API_KEY)

    system_prompt = """
    You are a helpful AI assistant that helps me organize my weekly schedule. You take in information about my week and then you give me a structured object that includes start and end times for each day. Each day can have multiple blocks of time that signify breaks in the day.

    The format I want you to use is as follows:
    - Return your response in 5 arrays; one for each day of the week.
    - Each array should contain arrays that represent the start and end times for each block of time in the day.
    - Each tuple should contain two strings: the start time and end time in the format "hh:mm AM/PM".
    - If there are no breaks in the day, return a single tuple with the default start and end times for the day.
    - If there are multiple blocks of time in the day, return multiple tuples in the array.
    """
    user_input = f"""
    I want my schedule to follow these rules:

    Every day has a default start time of 9:00 AM and end time of 5:00 PM unless stated otherwise. 
    Every day typically lasts about 8 hours.
    Consider the following exceptions when developing the schedule:

    These are the special exceptions that apply to my schedule:

    {notes}
    """

    try:
        response = generator.generate_text(
            system_instruction=system_prompt,
            user_input=user_input,
            temperature=1,
            max_output_tokens=1000,
        )
        schedule = {}
        for day, blocks in eval(response).items():
            schedule[day] = [tuple(block) for block in blocks]
        return schedule
    except ValueError as e:
        logger.error(f"Error: {e}")


def txt_to_pdf(txt_filename: str, pdf_filename: str):
    """
    Converts a .txt file to a .pdf file.

    Args:
        txt_filename (str): The path to the .txt file.
        pdf_filename (str): The path to save the .pdf file.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)  # Use a monospaced font for alignment

    with open(txt_filename, "r") as txt_file:
        for line in txt_file:
            pdf.multi_cell(0, 10, line.strip())  # Add each line to the PDF

    pdf.output(pdf_filename)
    print(f"PDF saved as {pdf_filename}")


def main():
    notes = """
    - On Tuesday, I want to start at 5AM and end at 2:00 PM.
    - On Friday, start at 1pm and end at 9:00 PM.
    """
    schedule = generate_schedule_from_instructions(notes)
    table_string = generate_weekly_schedule_transpose_12hr(schedule)
    # Print the table to the console
    console.print(table_string)
    # save_schedule_to_pdf(table_string, filename="schedule.pdf")
    with open("schedule.txt", "w") as f:
        f.write(table_string)
    txt_to_pdf("schedule.txt", "schedule.pdf")


if __name__ == "__main__":
    main()
