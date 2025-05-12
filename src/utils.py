from datetime import datetime as dt
import re
from pathlib import Path


def date_to_db_format(data):
    """Takes dd.mm.yyyy date formats with different separators and returns yyyy-mm-dd."""

    # define valid patterns, everything else is returned as is
    pattern = r"^(0[1-9]|[12][0-9]|3[01])[/-](0[1-9]|1[012])[/-]\d{4}$"

    new_record_dates_fixed = []

    for data_item in data:

        # test to determine if format is date we can change to db format
        if re.fullmatch(pattern, data_item):

            # if record has date structure, alter it, everything else throws exception and no changes made
            try:
                sep = "/" if "/" in data_item else "-" if "-" in data_item else None
                new_record_dates_fixed.append(
                    dt.strftime(dt.strptime(data_item, f"%d{sep}%m{sep}%Y"), "%Y-%m-%d")
                )

            except:
                new_record_dates_fixed.append(data_item)
        else:
            new_record_dates_fixed.append(data_item)

    print("inside func", new_record_dates_fixed)
    return new_record_dates_fixed


def log_action_in_db(db_cursor, table_name, idMember="", idPlaca=""):
    """Registers scraping action in actions table in database."""

    _values = (table_name, idMember, idPlaca, dt.now().strftime("%Y-%m-%d %H:%M:%S"))
    db_cursor.execute(f"INSERT INTO actions VALUES {_values}")


def revisar_symlinks():
    """validate symlink to see image files is active, if not create it"""
    link_path = Path("static/images")
    target_path = Path("../data/images").resolve()

    if link_path.exists():
        if link_path.is_symlink():
            if link_path.resolve() == target_path:
                print("✅ Symlink data/images.")
                return
            else:
                print("⚠ Recreando symlink data/images...")
                link_path.unlink()
                link_path.parent.mkdir(parents=True, exist_ok=True)
                link_path.symlink_to(target_path, target_is_directory=True)
                print("✅ Symlink creado.")
        else:
            raise Exception(
                f"❌ {link_path} existe pero no es un symlink. Remover de forma manual."
            )
