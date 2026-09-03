from app.models.main import Connection
from app.utils.crypto import decrypt, encrypt
from app.utils.key_manager import key_manager


MASTERPASS_CHECK_TEXT = 'Knowledge is power'


def validate_master_password(current_user, password):
    """
    Validate the password/key against the stored encrypted text
    :param current_user: current user instance
    :param password: password/key
    :return: Valid or not
    """
    # master pass is incorrect if decryption fails
    try:
        decrypted_text = decrypt(current_user.masterpass_check, password)

        if isinstance(decrypted_text, bytes):
            decrypted_text = decrypted_text.decode()

        if MASTERPASS_CHECK_TEXT != decrypted_text:
            return False
        else:
            return True
    except Exception:
        return False


def set_masterpass_check_text(current_user, password, reset=False):
    """
    Set the encrypted text which will be used later to validate entered key
    :param current_user: current user instance
    :param password: key
    """
    try:
        masterpass_check = ''

        if not reset:
            masterpass_check = encrypt(MASTERPASS_CHECK_TEXT, password)

        # set the encrypted sample text with the new
        # master pass

        current_user.masterpass_check = masterpass_check
        current_user.save()

    except Exception:
        raise


def reset_master_pass(current_user):
    """
    Remove the master password and saved passwords from DB which are
    encrypted using master password. Also remove the encrypted text
    """

    # also remove the master password check string as it will help if master
    # password entered/enabled again
    try:
        set_masterpass_check_text(current_user, '', reset=True)

        key_manager.remove(current_user)

        connections = Connection.objects.filter(user=current_user.user)

        if connections:
            for conn in connections:
                conn.password = ''
                conn.ssh_password = ''
                conn.ssh_key = ''
                conn.save()

    except Exception:
        raise
