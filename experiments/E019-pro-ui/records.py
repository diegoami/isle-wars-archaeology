"""E019 (T24): the shape of the experiment's records.

One run/1 record per question walk, at runs/E019/<batch>/<run id>.json, with its evidence
manifest at evidence/E019/<batch>/<run id>.manifest.json (the screenshots themselves are release
assets named by hash — rule 20; no PNG is ever committed). The record carries what the task's
Done-when names: the run id, the screenshots by name and sha256, the pixels-read results, the
cycle's before/after, the seal observations, and the walk's observation — as run/1 observations.
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
           "baseline before anything starts and again immediately before the launch; start_state.sha256 lists "
           "every entry of the prefix; the prefix is reset to that state after every walk")


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


def rep_of(batch, arm, root=ROOT):
    """One more than the records of this arm in this batch's folder (never rewrites one)."""
    folder = Path(root) / batch_folder("runs", batch)
    if not folder.is_dir():
        return 1
    return 1 + sum(1 for p in folder.glob("*.json")
                   if json.loads(p.read_text(encoding="utf-8")).get("arm") == arm)


def build_record(run_id, spec, argv, commit, machine, state_sha, fingerprint, observations, outputs,
                 started, ended, status, elapsed, set_id, root=ROOT):
    """The run/1 record of one question walk. `outputs` is [(name, path, class)] of the stored
    bundle files; the record names each by its sha256 and the release store, never by a local path."""
    return {
        "schema": "run/1",
        "run_id": run_id,
        "experiment": EXPERIMENT,
        "arm": arm_of_question(spec_qid(spec)),
        "rep": rep_of(spec["batch"], arm_of_question(spec_qid(spec)), root),
        "code_commit": commit,
        "machine": machine,
        "artifact": {"set": set_id, "variant": None},
        "runtime": {
            "driver": f"experiments/{EXPERIMENT}-pro-ui/run_walk.py@{commit}",
            "platform": "linux-wsl2/wine-xvfb-xfwm4",
            "fingerprint": fingerprint,
        },
        "interventions": INTERVENTIONS,
        "start_state": {"id": START_STATE_ID, "sha256": state_sha, "restore": RESTORE},
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
