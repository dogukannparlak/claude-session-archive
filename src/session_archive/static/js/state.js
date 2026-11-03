// Mutable UI state shared between modules.
export const S = {
  config: { sources: [] }, // from /api/config: source keys, labels, icons (user-configurable)
  all: [],      // session summaries from /api/sessions
  cur: null,    // id of the open session
  curCmd: '',   // `claude --resume ...` command of the open session
  hits: {},     // full-text search hits by session id
  hitsQ: '',    // query the hits belong to
};
