import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { TaskManager } from 'file:///D:/Project/dsh-harness-pilot/lib/tasks.js';
import { patchTaskManager } from './patch.js';

export const name = '@dsh-external/harness-unlimited';

/** Hot-load this additive plugin; do not reload Harness Pilot's active task owner. */
export function apply(ctx) {
  const directory = process.env.HARNESS_PILOT_HOME || join(homedir(), '.dsh', 'plugins', 'harness-pilot');
  const readLimit = () => {
    try { return JSON.parse(readFileSync(join(directory, 'runtime-settings.json'), 'utf8')).maxConcurrent; }
    catch { return undefined; }
  };
  const dispose = patchTaskManager(TaskManager, readLimit);
  ctx.effect(() => dispose, 'harness-unlimited: live TaskManager start policy');
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, 'unlimited-live.json'), JSON.stringify({
    pid: process.pid, appliedAt: new Date().toISOString(), maxConcurrent: readLimit(),
    taskModule: 'D:/Project/dsh-harness-pilot/lib/tasks.js', preservesExistingTasks: true
  }, null, 2) + '\n');
}
