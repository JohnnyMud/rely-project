"""Seed the database with synthetic demo data.

Inserts a set of fictional patients with upcoming appointments, plus call
history in a mix of lifecycle states (pending, initiated, ended, failed) so
the UI has something realistic to show.

All data is synthetic: 555 phone numbers, made-up addresses and IDs. No real
patient information — except one optional "callable" patient whose phone
number comes from the TEST_NUMBER env var, so you can place a real Retell
call during a demo.

Usage (from the project root):

    uv run python scripts/seed_demo.py           # add demo data (skips if already seeded)
    uv run python scripts/seed_demo.py --reset   # delete previous demo data first, then reseed

Requires TEST_NUMBER in the environment (or in .env) for the callable patient.
The script only ever touches rows it created itself (medical record numbers
prefixed with DEMO-), so it will not delete data you added by hand.
"""

import argparse
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import CallAttempts, Patients

DEMO_MRN_PREFIX = "DEMO-"
ROOT = Path(__file__).resolve().parent.parent

# (first_name, last_name, date_of_birth, home_address, timezone)
DEMO_PEOPLE = [
    ("Ava", "Thompson", date(1988, 3, 14), "2847 Maplewood Drive, Portland, OR 97201", "America/Los_Angeles"),
    ("Marcus", "Rivera", date(1975, 11, 2), "915 Sycamore Lane, Austin, TX 78704", "America/Chicago"),
    ("Priya", "Natarajan", date(1992, 7, 28), "406 Birchwood Court, Edison, NJ 08817", "America/New_York"),
    ("Daniel", "Okafor", date(1969, 1, 19), "1730 Crestview Avenue, Atlanta, GA 30309", "America/New_York"),
    ("Sofia", "Lindqvist", date(1996, 9, 5), "58 Harbor View Road, San Diego, CA 92109", "America/Los_Angeles"),
]

APPOINTMENT_TIMES = [
    time(9, 0), time(9, 30), time(10, 15), time(11, 0),
    time(13, 30), time(14, 0), time(15, 45), time(16, 30),
]

ENDED_SUMMARIES_SUCCESS = [
    "Patient confirmed the appointment and asked for the clinic address.",
    "Patient confirmed they will attend and requested a reminder text.",
    "Spoke with patient; appointment confirmed, no changes needed.",
]

ENDED_SUMMARIES_UNSUCCESSFUL = [
    "Reached voicemail; left a reminder message with the appointment details.",
    "Patient answered but asked to reschedule; follow-up needed.",
    "Call connected briefly and dropped before confirmation.",
]


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ if not already set."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def synthetic_phone(rng: random.Random) -> str:
    # 555-01xx numbers are reserved for fictional use.
    return f"+1{rng.choice(['415', '512', '732', '404', '619'])}555{rng.randint(100, 199):04d}"


def build_patients(rng: random.Random, test_number: str | None) -> list[Patients]:
    today = date.today()
    patients = []
    for i, (first, last, dob, address, tz) in enumerate(DEMO_PEOPLE):
        # First patient uses TEST_NUMBER so Start Call can place a real Retell call.
        phone = test_number if i == 0 and test_number else synthetic_phone(rng)
        patients.append(
            Patients(
                first_name=first,
                last_name=last,
                date_of_birth=dob,
                phone_number=phone,
                home_address=address,
                insurance_number=f"INS-{rng.randint(10_000_000, 99_999_999)}",
                medical_record_number=f"{DEMO_MRN_PREFIX}{1000 + i}",
                # Spread appointments over the next two weeks.
                appointment_date=today + timedelta(days=rng.randint(1, 14)),
                appointment_time=rng.choice(APPOINTMENT_TIMES),
                timezone=tz,
            )
        )
    return patients


def build_call_history(patients: list[Patients], rng: random.Random) -> list[CallAttempts]:
    """Give most patients a few past call attempts in varied states."""
    now = datetime.now()
    calls = []

    for patient in patients:
        for _ in range(rng.randint(0, 3)):
            created_at = now - timedelta(days=rng.randint(0, 10), minutes=rng.randint(0, 600))
            status = rng.choices(
                ["ended", "initiated", "failed", "pending"],
                weights=[6, 2, 1, 1],
            )[0]

            call = CallAttempts(
                patient_id=patient.id,
                created_at=created_at,
                call_status=status,
            )

            if status in ("initiated", "ended"):
                call.retell_call_id = f"call_demo_{uuid.uuid4().hex[:16]}"
                call.started_at = created_at + timedelta(seconds=rng.randint(2, 15))

            if status == "ended":
                duration = rng.randint(20, 180)
                call.call_duration = duration
                call.ended_at = call.started_at + timedelta(seconds=duration)
                call.successful = rng.random() < 0.7
                call.summary = rng.choice(
                    ENDED_SUMMARIES_SUCCESS if call.successful else ENDED_SUMMARIES_UNSUCCESSFUL
                )

            calls.append(call)

    return calls


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database with synthetic demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete previously seeded demo data before inserting fresh data.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    test_number = os.getenv("TEST_NUMBER")
    if not test_number:
        print("Warning: TEST_NUMBER is not set. All patients will use synthetic 555 numbers.")
        print("Set TEST_NUMBER in .env (or the environment) to make Ava Thompson callable.")

    rng = random.Random(42)
    db = SessionLocal()
    try:
        existing = (
            db.query(Patients)
            .filter(Patients.medical_record_number.like(f"{DEMO_MRN_PREFIX}%"))
            .all()
        )

        if existing and not args.reset:
            print(f"Found {len(existing)} demo patients already seeded. Use --reset to reseed.")
            return

        if existing:
            patient_ids = [p.id for p in existing]
            deleted_calls = (
                db.query(CallAttempts)
                .filter(CallAttempts.patient_id.in_(patient_ids))
                .delete(synchronize_session=False)
            )
            for patient in existing:
                db.delete(patient)
            db.commit()
            print(f"Removed {len(existing)} demo patients and {deleted_calls} call records.")

        patients = build_patients(rng, test_number)
        db.add_all(patients)
        db.commit()

        calls = build_call_history(patients, rng)
        db.add_all(calls)
        db.commit()

        print(f"Seeded {len(patients)} patients and {len(calls)} call records.")
        if test_number:
            print(f"Callable patient: Ava Thompson ({test_number})")
        print("Open the frontend and pick a patient to see their call history.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
