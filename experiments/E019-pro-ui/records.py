"""E019 (T24): the shape of the experiment's records.

One run/1 record per question walk, at runs/E019/<batch>/<run id>.json, with its evidence
manifest at evidence/E019/<batch>/<run id>.manifest.json (the screenshots themselves are release
assets named by hash — rule 20; no PNG is ever committed). The record carries what the task's
Done-when names: the run id, the screenshots by name and sha256, the pixels-read results, the
cycle's before/after, the seal observations, and the walk's observation — as run/1 observations.

T48 (#149; rule 18's carve-out, constraints C and F): a walk's record is a Wine record of the
carve-out's own making, so it carries `runtime.platform = PLATFORM` (E020's token, the one
`tools/check_no_originals.py` recognises), `artifact.variant = VARIANT` (F019's row variant, which
constraint F matches on) and `start_state.sha256 = binary_sha256(install)`, the sha256 of the
`Islepro.exe` that ran, hashed from the bound install at the walk's start. Where that field's old
value went: the prefix listing's sha256 is **not dropped — it is named in `start_state.restore`**
(`restore_text`), which the schema allows and this module's docstring is asked to say (the schema's
`start_state` takes no other key).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = "E019"

# The two artifact sets a walk may be recorded under (artifacts/known.json; the recorder passes one to
# the driver, the checker compares each record's `artifact.set` with it). The successor set is for the
# walks that may write xtras/Islepro.skr by crediting a loss (F003); every other walk records the base
# set. They are repeated here (the driver's cycle.py holds the same ids) so the check can compare a
# record's identity without importing the driver, and a test pins them to the driver's constants.
ARTIFACT_SET = "iwp-2.0-996e86c5"
ARTIFACT_SET_SAVED_FILES = "iwp-2.0-de5a82a2"

# T48 (#149): the carve-out's platform (constraint C; E020 writes the same token) and the variant of
# the F019 known-good row whose sha256 constraint F checks against start_state.sha256. Both are the
# exact spellings tools/check_no_originals.py matches; a test pins the platform to the gate's own
# constants so a token the gate does not recognise cannot be written here unnoticed.
PLATFORM = "wine-on-user-machine-iwp-2.0"
VARIANT = "unregistered"
BINARY = "Islepro.exe"


def artifact_set_for(spec):
    """The artifact set a walk's record belongs to: the successor set when the walk may write a file
    of the set (may_write_saved_files), the base set otherwise."""
    return ARTIFACT_SET_SAVED_FILES if spec.get("may_write_saved_files") else ARTIFACT_SET

# The walk's intervention level, the same wording the E004 driver records (vocabulary/interventions.md).
INTERVENTIONS = [{"level": "I1", "what": "screenshots of the display and read-only reads of /proc and of "
                                         "the game copy; no memory read, no modified file"}]

# The starts every walk records from: the sealed prefix, the title screen.
START_STATE_ID = "S-cold-prefix-title"
RESTORE = ("fresh private user, mount and PID namespaces, the install bound read-only once for the command "
           "and checked at the start of every walk; the prefix sealed and its registry files equal to their "
           "baseline before anything starts and again immediately before the launch; the prefix is reset to "
           "that state after every walk")


def restore_text(prefix_sha):
    """One walk's `start_state.restore`: how the prefix was restored, plus where the prefix listing's
    sha256 went when T48 (#149) made `start_state.sha256` the binary's hash.

    The schema's `start_state` takes only `id`, `sha256` and `restore` (additionalProperties false),
    so the listing hash that `start_state.sha256` held until T48 is named here: nothing measured is
    dropped (rule 20), and this docstring is where the README-level answer to "where did it go?" is.
    `prefix_sha` is `spike.start_state_sha()`'s value, or the all-zero placeholder when the session
    stopped before its snapshot, exactly as the field itself used to carry it.
    """
    return (f"{RESTORE}; T48: start_state.sha256 is the sha256 of the install's {BINARY}, the binary "
            f"that ran, and the prefix listing it held until T48 is here at sha256 {prefix_sha}")


def arm_of_question(qid):
    """The record's arm: the question id, lowercased (a plain identifier, safeio's rule)."""
    return qid.lower()


def question_of_arm(arm):
    """The question id an arm names (the check maps a recorded file to its question this way)."""
    return arm.upper()


def batch_folder(kind, batch):
    """The tracked folder of one batch's records (`runs`) or manifests (`evidence`), relative to ROOT."""
    return f"{kind}/{EXPERIMENT}/{batch}"


def record_paths(batch, run_id):
    """Where one walk's record and manifest sit, relative to ROOT."""
    return {"run": f"{batch_folder('runs', batch)}/{run_id}.json",
            "manifest": f"{batch_folder('evidence', batch)}/{run_id}.manifest.json"}


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binary_sha256(install):
    """The `Islepro.exe` of the bound install, hashed in place: the binary that ran (T48, constraint C).

    `install` is `locs["IWP_DIR"]`, the install bound read-only for the command — never the prefix
    and never the run copy in it (E020 hashes both only to check they agree with F019; the record
    names the install's), and never a constant: the walk's test feeds this two different fake
    binaries. OSError propagates, so a walk whose binary cannot be hashed writes no record.
    """
    return sha256_file(Path(install) / BINARY)


def rep_of(batch, arm, root=ROOT):
    """One more than the records of this arm in this batch's folder (never rewrites one)."""
    folder = Path(root) / batch_folder("runs", batch)
    if not folder.is_dir():
        return 1
    return 1 + sum(1 for p in folder.glob("*.json")
                   if json.loads(p.read_text(encoding="utf-8")).get("arm") == arm)


def build_record(run_id, spec, argv, commit, machine, state_sha, binary_sha, fingerprint, observations, outputs,
                 started, ended, status, elapsed, set_id, root=ROOT):
    """The run/1 record of one question walk. `outputs` is [(name, path, class)] of the stored
    bundle files; the record names each by its sha256 and the release store, never by a local path.

    `state_sha` is the prefix listing's sha256 (`spike.start_state_sha`), which this field held
    until T48 (#149) and which `restore_text` names now; `binary_sha` is `binary_sha256(install)`,
    the sha256 of the `Islepro.exe` that ran, which `start_state.sha256` is since T48 — the value
    `tools/check_no_originals.py`'s wine gate verifies against F019's row (set + VARIANT + sha256).
    """
    return {
        "schema": "run/1",
        "run_id": run_id,
        "experiment": EXPERIMENT,
        "arm": arm_of_question(spec_qid(spec)),
        "rep": rep_of(spec["batch"], arm_of_question(spec_qid(spec)), root),
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": set_id, "variant": VARIANT},
        "runtime": {
            "driver": f"experiments/{EXPERIMENT}-pro-ui/run_walk.py@{commit}",
            "platform": PLATFORM,
            "fingerprint": fingerprint,
        },
        "interventions": INTERVENTIONS,
        "start_state": {"id": START_STATE_ID, "sha256": binary_sha, "restore": restore_text(state_sha)},
        "seed": None,
        "actions": {"script": f"experiments/{EXPERIMENT}-pro-ui/run_walk.py",
                    "sha256": sha256_file(Path(__file__).with_name("run_walk.py")), "args": argv},
        "observations": observations,
        "outputs": [{"name": name, "sha256": sha256_file(path), "store": f"release:{EXPERIMENT}"}
                    for name, path, _ in outputs],
        "started": started,
        "ended": ended,
        "status": status,
    }


def build_manifest(run_id, outputs, set_id):
    """The evidence manifest of one walk: every bundle file named by hash (its release asset name)."""
    files = []
    for name, path, klass in outputs:
        digest = sha256_file(path)
        files.append({"name": name, "bytes": Path(path).stat().st_size, "sha256": digest,
                      "asset": f"{digest[:16]}-{name}", "class": klass})
    return {"schema": "evidence-manifest/1", "run_id": run_id, "experiment": EXPERIMENT,
            "store": f"release:{EXPERIMENT}", "artifact": {"set": set_id, "variant": None},
            "files": files}


def spec_qid(spec):
    """The question id a spec dict carries (the recorder injects `qid` when it loads the table)."""
    return spec["qid"]
