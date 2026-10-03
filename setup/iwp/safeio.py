"""The one confined writer of the iwp-runtime profile and the E001 cycle.

Confining a directory (locations.py) is not enough. A file written into it can still land somewhere
else:
- when its name is absolute or climbs out with `..` (a join with an absolute name drops the
  directory);
- when the destination name is already a symbolic link, or a hard link to a file that matters
  (`open(..., "w")`, `shutil.copy` and `chmod` all act through both);
- when a directory on the way is swapped for a link between a check and the write.

So every file is written, every name removed and every mode changed through this module:
- names are one plain component (`safe_name`);
- a directory is reached by opening each component of its canonical path from `/` with
  `O_NOFOLLOW`, and the work is then done relative to that open descriptor, so no link on the way is
  followed, even one swapped in after the path was checked;
- a file is written as a new file (`O_CREAT | O_EXCL | O_NOFOLLOW`), checked with `fstat` (a regular
  file with one name), and then given its name: `link` for a name that must be new (it fails if
  anything appeared there), `rename` for a name being replaced. A rename replaces the name only;
  whatever the old name pointed at keeps its bytes, its mode and its other names;
- an existing destination that is not a plain file of its own (a link, a file with another name, a
  directory, a device) is refused, never replaced and never written through;
- a copy is hashed from the bytes actually written, and refused when they are not the expected ones;
- a mode is changed through a descriptor opened with `O_NOFOLLOW`, and never on a file with more
  than one name.

A refusal is `Refused`; nothing is left behind by a refused write.
"""
import errno
import hashlib
import os
import re
import secrets
import shutil
import stat
from pathlib import Path

SAFE_NAME = re.compile(r"[A-Za-z0-9._-]{1,100}")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
LINK_ERRORS = (errno.ELOOP, errno.ENOTDIR)


class Refused(Exception):
    """A write, removal or mode change that would not stay where it was meant to."""


def safe_name(value, what="name"):
    """The value, when it is one plain path component (letters, digits, dot, dash, underscore, at
    most 100 characters, and neither `.` nor `..`); Refused otherwise."""
    if not isinstance(value, str) or not SAFE_NAME.fullmatch(value) or value in (".", ".."):
        raise Refused(f"{what} {value!r} is not a plain name")
    return value


def identifier(value, what="identifier"):
    """A safe name that also starts with a letter or a digit (an arm, a run id); Refused otherwise."""
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise Refused(f"{what} {value!r} is not a plain identifier (a letter or digit, then letters, "
                      "digits, dot, dash or underscore; no slash)")
    return value


def plain_file(info):
    """True for a regular file with exactly one name."""
    return stat.S_ISREG(info.st_mode) and info.st_nlink == 1


def describe(info):
    if stat.S_ISLNK(info.st_mode):
        return "a symbolic link"
    if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
        return f"a file with {info.st_nlink} names (a hard link)"
    if stat.S_ISDIR(info.st_mode):
        return "a directory"
    if stat.S_ISREG(info.st_mode):
        return "a plain file"
    return "a device, fifo or socket"


def open_directory(path, create_below=None):
    """An open descriptor of the directory at a canonical absolute path, reached without following
    any link. Components strictly below `create_below` (a canonical ancestor) are created when
    missing; nothing else is. The caller closes the descriptor."""
    path = Path(path)
    if not path.is_absolute() or any(part in ("", ".", "..") for part in path.parts[1:]):
        raise Refused("a directory must be given by a canonical absolute path")
    creatable = None
    if create_below is not None:
        base = Path(create_below)
        if not (path == base or base in path.parents):
            raise Refused("the directory is not under the place it may be created in")
        creatable = len(base.parts)
    fd = os.open("/", DIR_FLAGS)
    try:
        for depth, part in enumerate(path.parts[1:], start=2):
            try:
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
            except FileNotFoundError:
                if creatable is None or depth <= creatable:
                    raise Refused(f"the directory {part} does not exist") from None
                try:
                    os.mkdir(part, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
                child = _open_dir_at(part, fd)
            except OSError as exc:
                if exc.errno in LINK_ERRORS:
                    raise Refused(f"{part} is a link or not a directory; nothing is followed") from None
                raise
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_dir_at(name, dir_fd):
    try:
        return os.open(name, DIR_FLAGS, dir_fd=dir_fd)
    except OSError as exc:
        if exc.errno in LINK_ERRORS:
            raise Refused(f"{name} is a link or not a directory; nothing is followed") from None
        raise


def lstat_at(dir_fd, name):
    try:
        return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


def open_source(path):
    """A file object for reading a regular file, its own name not followed; Refused otherwise."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as exc:
        if exc.errno in LINK_ERRORS:
            raise Refused(f"{Path(path).name} is a link; it is not read through") from None
        raise
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise Refused(f"{Path(path).name} is not a regular file")
    return os.fdopen(fd, "rb")


def write_file(directory, name, data=None, source=None, exist="new", mode=0o644,
               expect_sha256=None, create_below=None, times_from_source=False, replace_shared=False):
    """Write bytes (`data`) or a copy of a file (`source`) as `name` in a canonical directory.

    exist: "new"     the name must not exist (records: never overwritten);
           "same"    an existing plain file with the same bytes is kept, anything else is refused
                     (content-addressed bundle assets);
           "replace" an existing plain file of its own is replaced by rename; with
                     `replace_shared`, so is a regular file with other names (that is how such a
                     file is given a file of its own: the other names keep the old one).
    Returns "written" or "kept". Refused when the name, the directory, an existing destination or
    the written bytes (`expect_sha256`) are not what they must be.
    """
    if exist not in ("new", "same", "replace") or (data is None) == (source is None):
        raise ValueError("write_file needs exactly one of data and source, and a known exist mode")
    name = safe_name(name, "file name")
    dir_fd = open_directory(directory, create_below)
    try:
        existing = lstat_at(dir_fd, name)
        if existing is not None:
            shared_ok = replace_shared and exist == "replace" and stat.S_ISREG(existing.st_mode)
            if not (plain_file(existing) or shared_ok):
                raise Refused(f"{name} already exists as {describe(existing)}; it is never written through")
            if exist == "new":
                raise Refused(f"{name} already exists; it is never overwritten")
        tmp = f".{name}.{secrets.token_hex(8)}.tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600,
                     dir_fd=dir_fd)
        try:
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb", closefd=False) as out:
                if data is not None:
                    digest.update(data)
                    out.write(data)
                else:
                    with open_source(source) as src:
                        for chunk in iter(lambda: src.read(1 << 20), b""):
                            digest.update(chunk)
                            out.write(chunk)
                        src_info = os.fstat(src.fileno())
                out.flush()
            if expect_sha256 is not None and digest.hexdigest() != expect_sha256:
                raise Refused(f"{name}: the bytes copied are not the expected ones")
            written = os.fstat(fd)
            if not plain_file(written):
                raise Refused(f"{name}: the new file is not a plain file of its own")
            os.fchmod(fd, mode)
            if times_from_source and source is not None:
                os.utime(fd, ns=(src_info.st_atime_ns, src_info.st_mtime_ns))
            os.fsync(fd)
            if exist == "same" and existing is not None:
                if _sha256_at(dir_fd, name) == digest.hexdigest():
                    os.unlink(tmp, dir_fd=dir_fd)
                    return "kept"
                raise Refused(f"{name} already exists with other bytes")
            if existing is not None and exist == "replace":
                os.replace(tmp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
            else:
                try:
                    os.link(tmp, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)
                except FileExistsError:
                    raise Refused(f"{name} appeared while it was being written; nothing was overwritten") from None
                os.unlink(tmp, dir_fd=dir_fd)
            return "written"
        except BaseException:
            try:
                os.unlink(tmp, dir_fd=dir_fd)
            except OSError:
                pass
            raise
        finally:
            os.close(fd)
    finally:
        os.close(dir_fd)


def _sha256_at(dir_fd, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
    try:
        if not plain_file(os.fstat(fd)):
            raise Refused(f"{name} is not a plain file of its own")
        digest = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


def sha256_plain(base, rel):
    """sha256 of the plain file at base/rel, reached without following any link; None when the
    entry is missing or is not a plain file of its own."""
    rel = Path(rel)
    try:
        dir_fd = open_directory(Path(base).joinpath(*rel.parts[:-1]))
    except (Refused, OSError):
        return None
    try:
        return _sha256_at(dir_fd, rel.name)
    except (Refused, OSError):
        return None
    finally:
        os.close(dir_fd)


def remove(base, rel):
    """Remove the entry base/rel (a directory with everything in it), reached without following any
    link. A link or a file with other names loses this name only. Returns False when it was absent."""
    rel = Path(rel)
    if rel.is_absolute() or not rel.parts or any(p in ("", ".", "..") for p in rel.parts):
        raise Refused(f"{rel.as_posix()} is not a path inside {Path(base).name}")
    try:
        dir_fd = open_directory(Path(base).joinpath(*rel.parts[:-1]))
    except Refused:
        if not os.path.lexists(Path(base).joinpath(*rel.parts[:-1])):
            return False
        raise
    try:
        info = lstat_at(dir_fd, rel.name)
        if info is None:
            return False
        if stat.S_ISDIR(info.st_mode):
            _refuse_other_filesystems(dir_fd, rel.name, os.fstat(dir_fd).st_dev)
            shutil.rmtree(rel.name, dir_fd=dir_fd)     # descriptor-based: never follows a link
        else:
            os.unlink(rel.name, dir_fd=dir_fd)         # the name only
        return True
    finally:
        os.close(dir_fd)


def _refuse_other_filesystems(dir_fd, name, device):
    """Refused when anything in the tree at name lies on another filesystem (a mount): removing it
    would remove another place's files."""
    for _, dirnames, filenames, fd in os.fwalk(name, dir_fd=dir_fd, follow_symlinks=False):
        if os.fstat(fd).st_dev != device:
            raise Refused(f"{name} holds a mount; nothing under it is removed")
        for entry in dirnames + filenames:
            if os.stat(entry, dir_fd=fd, follow_symlinks=False).st_dev != device:
                raise Refused(f"{name} holds a mount; nothing under it is removed")


def set_mode(base, rel, mode):
    """chmod base/rel (a plain file of its own or a directory) through a descriptor; never through a
    link and never on a file with other names."""
    rel = Path(rel)
    dir_fd = open_directory(Path(base).joinpath(*rel.parts[:-1])) if rel.parts else None
    try:
        if dir_fd is None:
            fd = open_directory(base)
        else:
            try:
                fd = os.open(rel.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            except OSError as exc:
                if exc.errno in LINK_ERRORS:
                    raise Refused(f"{rel.as_posix()} is a link; its mode is not changed") from None
                raise
        try:
            info = os.fstat(fd)
            if not (stat.S_ISDIR(info.st_mode) or plain_file(info)):
                raise Refused(f"{rel.as_posix()} is {describe(info)}; its mode is not changed")
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
    finally:
        if dir_fd is not None:
            os.close(dir_fd)


def make_link(base, rel, target):
    """Create the symbolic link base/rel -> target (a relative target inside the prefix), refusing
    an existing name."""
    rel = Path(rel)
    dir_fd = open_directory(Path(base).joinpath(*rel.parts[:-1]))
    try:
        os.symlink(target, safe_name_or_drive(rel.name), dir_fd=dir_fd)
    finally:
        os.close(dir_fd)


def make_directory(base, rel):
    """Create the directory base/rel, its parent reached without following any link."""
    rel = Path(rel)
    dir_fd = open_directory(Path(base).joinpath(*rel.parts[:-1]))
    try:
        os.mkdir(rel.name, 0o755, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)


def safe_name_or_drive(name):
    """A plain name, or a drive mapping such as `c:`."""
    if re.fullmatch(r"[a-z]:", name):
        return name
    return safe_name(name)


def create_stream(directory, name):
    """A new file `name` in a canonical directory, opened for writing (a log a child process writes
    to); refused when the name exists in any form."""
    name = safe_name(name, "file name")
    dir_fd = open_directory(directory)
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644,
                     dir_fd=dir_fd)
    except FileExistsError:
        raise Refused(f"{name} already exists; it is never written through") from None
    finally:
        os.close(dir_fd)
    return os.fdopen(fd, "wb")
