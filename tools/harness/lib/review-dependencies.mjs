// Give Claude review worktrees a private copy of the launcher's installed dependencies.
// This keeps a reviewer's writes inside its retained worktree while preserving npm .bin links.
import fs from 'node:fs';
import path from 'node:path';

const inside = (parent, candidate) => candidate === parent || candidate.startsWith(parent + path.sep);

function realDirectory(value, label) {
  const real = fs.realpathSync(value);
  if (!fs.statSync(real).isDirectory()) throw new Error(`${label} must be a directory: ${value}`);
  return real;
}

function assertContainedSymlinks(source, directory = source) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const item = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) {
      const link = fs.readlinkSync(item);
      if (path.isAbsolute(link)) throw new Error(`Dependency copy contains an absolute symlink: ${item}`);
      let target;
      try { target = fs.realpathSync(item); }
      catch { throw new Error(`Dependency copy contains a broken symlink: ${item}`); }
      if (!inside(source, target)) throw new Error(`Dependency copy symlink escapes its source tree: ${item}`);
    } else if (entry.isDirectory()) {
      assertContainedSymlinks(source, item);
    }
  }
}

/** Copy installed dependencies into an owned review worktree without replacing anything.
 * Returns `null` when the trusted launcher has no node_modules directory.
 */
export function materializeReviewDependencies({ source, destination, ownedRoot }) {
  try { fs.lstatSync(source); }
  catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
  let sourceStat;
  try { sourceStat = fs.statSync(source); }
  catch (error) {
    if (error.code === 'ENOENT') throw new Error(`Dependency source does not resolve to a directory: ${source}`);
    throw error;
  }
  if (!sourceStat.isDirectory()) throw new Error(`Dependency source must be a directory: ${source}`);

  const realSource = realDirectory(source, 'Dependency source');
  const realRoot = realDirectory(ownedRoot, 'Owned review root');
  const parent = realDirectory(path.dirname(destination), 'Dependency destination parent');
  const target = path.resolve(parent, path.basename(destination));
  if (!inside(realRoot, target)) throw new Error(`Dependency destination is outside the owned review root: ${target}`);
  if (inside(realSource, target) || inside(target, realSource)) throw new Error('Dependency source and destination overlap.');
  assertContainedSymlinks(realSource);

  try {
    fs.lstatSync(target);
    throw new Error(`Dependency destination already exists; refusing to overwrite: ${target}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  // mkdir is the no-overwrite claim. If another process creates the path after lstat,
  // mkdir fails rather than merging into or replacing that path.
  fs.mkdirSync(target);
  for (const name of fs.readdirSync(realSource)) {
    fs.cpSync(path.join(realSource, name), path.join(target, name), {
      recursive: true,
      force: false,
      errorOnExist: true,
      dereference: false,
      verbatimSymlinks: true,
    });
  }
  return { source: realSource, destination: target };
}
