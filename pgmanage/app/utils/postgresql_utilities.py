import os
import shutil
from typing import Union

from app.models.main import UserDetails
from django.contrib.auth.models import User


def check_utility_path(
    utility: str, binary_path: Union[str, os.PathLike]
) -> Union[os.PathLike, None]:
    path = (
        shutil.which(utility)
        if not binary_path
        else os.path.join(binary_path, f"{utility}.exe" if os.name == "nt" else utility)
    )
    return path


def get_utility_path(utility: str, current_user: User, pg_version: int | None = None) -> os.PathLike:
    user_details = UserDetails.objects.get(user=current_user)

    if utility == "pigz":
        binary_path = user_details.pigz_path
    else:
        binary_path = user_details.get_pg_bin(pg_version)

    utility_path = check_utility_path(utility=utility, binary_path=binary_path)

    if utility_path is None or not os.path.exists(utility_path):
        error_msg = f"{utility_path if utility_path else utility} not found."
        if utility == "pigz":
            error_msg += "\nPlease make sure that you have pigz installed."
        else:
            error_msg += (
                "\nPlease make sure that you have Postgresql Client installed."
                "\nMore information: $install_guide$"
            )
        raise FileNotFoundError(error_msg)
    return utility_path
