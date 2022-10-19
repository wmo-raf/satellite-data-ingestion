import os
import shutil
import stat
import tempfile


def copy_with_metadata(source, target):
    """Copy file with all its permissions and metadata.

    Lifted from https://stackoverflow.com/a/43761127/2860309
    :param source: source file name
    :param target: target file name
    """
    # copy content, stat-info (mode too), timestamps...
    shutil.copy2(source, target)
    # copy owner and group
    st = os.stat(source)
    os.chown(target, st[stat.ST_UID], st[stat.ST_GID])


def atomic_write(file_contents, target_file_path, mode="w"):
    """Write to a temporary file and rename it to avoid file corruption.
    Attribution: @therightstuff, @deichrenner, @hrudham
    :param file_contents: contents to be written to file
    :param target_file_path: the file to be created or replaced
    :param mode: the file mode defaults to "w", only "w" and "a" are supported
    """
    # Use the same directory as the destination file so that moving it across
    # file systems does not pose a problem.
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        dir=os.path.dirname(target_file_path))
    try:
        # preserve file metadata if it already exists
        if os.path.exists(target_file_path):
            copy_with_metadata(target_file_path, temp_file.name)
        with open(temp_file.name, mode) as f:
            f.write(file_contents)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file.name, target_file_path)
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass
