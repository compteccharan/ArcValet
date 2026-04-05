# ArcValet

ArcValet is a desktop parking management app built with **Python + CustomTkinter + SQLite3**.

## Features

- Spot seeding on first run (17 total spots)
- Vehicle entry with spot preference
- Vehicle exit with automatic billing by duration and spot hourly rate
- Dashboard metrics (total, occupied, available, today's revenue)
- Records view for active and completed sessions

## Run

1. Install UI dependency:
	- `pip install customtkinter`
2. Start the app:
	- `python main.py`

Database file `arcvalet/arcvalet.db` is created automatically on first run.

