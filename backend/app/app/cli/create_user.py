import click

from app.crud import user
from app.db.session import SessionLocal
from app.schemas import UserCreate


@click.command()
@click.option("--username", required=True, help="The username.")
@click.option("--fullname", required=True, help="The full name.")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create(username, fullname, password):
    user_info = UserCreate(username=username, full_name=fullname, password=password)
    with SessionLocal() as db:
        user.create_user(db, user_info)


if __name__ == "__main__":
    create()
