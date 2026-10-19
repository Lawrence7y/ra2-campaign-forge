/** Keep existing TaskManager instances and callbacks while applying the on-disk limit. */
export function patchTaskManager(TaskManager, readLimit) {
  const original = TaskManager.prototype.start;
  const wrapped = function (input) {
    const limit = readLimit();
    if (limit === 0) this.setMaxConcurrent(Infinity);
    else if (typeof limit === 'number' && Number.isFinite(limit) && limit > 0) this.setMaxConcurrent(Math.round(limit));
    return original.call(this, input);
  };
  TaskManager.prototype.start = wrapped;
  return () => {
    if (TaskManager.prototype.start === wrapped) TaskManager.prototype.start = original;
  };
}
