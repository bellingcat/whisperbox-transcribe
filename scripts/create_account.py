import argparse
from dotenv import load_dotenv
from app.db.base import get_db
from app.db.models import Account

load_dotenv()

def create_account(name: str) -> Account:
    db = get_db().__next__()
    account = Account(name=name)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str, nargs=1)
    args = parser.parse_args()
    create_account(args.name[0])
