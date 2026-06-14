// IRONLOG — Alpine.js helpers and HTMX configuration

// Redirect to login on 401 responses (HTMX)
document.addEventListener("htmx:responseError", (evt) => {
  if (evt.detail.xhr.status === 401) {
    window.location.href = "/login";
  }
});

// Recording screen Alpine.js store.
// JSON データは window.__recordData__ から読み込む（record.html の script タグで設定）。
function recordStore() {
  const d = window.__recordData__;
  return {
    date: d.date,
    allExercises: d.exercises,
    parts: d.parts,
    blocks: d.blocks,
    showPicker: false,
    pickerFilter: "all",
    saved: false,
    saving: false,

    get filteredExercises() {
      if (this.pickerFilter === "all") return this.allExercises;
      return this.allExercises.filter((e) => e.body_part === this.pickerFilter);
    },

    get totalVolume() {
      return this.blocks.reduce(
        (sum, b) => sum + b.sets.reduce((s, x) => s + (x.reps || 0) * (x.weight || 0), 0),
        0
      );
    },

    get totalSets() {
      return this.blocks.reduce((sum, b) => sum + b.sets.length, 0);
    },

    addExercise(ex) {
      // Avoid duplicate exercises in one session
      if (this.blocks.some((b) => b.exercise_id === ex.exercise_id)) {
        this.showPicker = false;
        return;
      }
      this.blocks.push({
        exercise_id: ex.exercise_id,
        exercise: ex,
        sets: [{ reps: 10, weight: ex.best_weight || 40 }],
      });
      this.showPicker = false;
    },

    removeBlock(idx) {
      this.blocks.splice(idx, 1);
    },

    addSet(bi) {
      const last = this.blocks[bi].sets.at(-1) || { reps: 10, weight: 40 };
      this.blocks[bi].sets.push({ ...last });
    },

    removeSet(bi, si) {
      if (this.blocks[bi].sets.length > 1) {
        this.blocks[bi].sets.splice(si, 1);
      }
    },

    updateReps(bi, si, val) {
      this.blocks[bi].sets[si].reps = parseInt(val) || 0;
    },

    updateWeight(bi, si, val) {
      this.blocks[bi].sets[si].weight = parseFloat(val) || 0;
    },

    async save() {
      this.saving = true;
      try {
        const resp = await fetch("/record/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: this.date,
            blocks: this.blocks.map((b) => ({
              exercise_id: b.exercise_id,
              sets: b.sets,
            })),
          }),
        });
        if (resp.ok) {
          this.saved = true;
          setTimeout(() => (this.saved = false), 2400);
        }
      } finally {
        this.saving = false;
      }
    },
  };
}

// Exercise management Alpine.js store
function exerciseStore() {
  return {
    showAddModal: false,
    showEditModal: false,
    showDeleteModal: false,
    editTarget: null,
    deleteTarget: null,

    openAdd() {
      this.showAddModal = true;
    },

    openEdit(ex) {
      this.editTarget = { ...ex };
      this.showEditModal = true;
    },

    openDelete(ex) {
      this.deleteTarget = ex;
      this.showDeleteModal = true;
    },

    closeAll() {
      this.showAddModal = false;
      this.showEditModal = false;
      this.showDeleteModal = false;
      this.editTarget = null;
      this.deleteTarget = null;
    },
  };
}
