from PySide6.QtCore import QObject, Signal
from core.safechunk_engine import SafeChunkEngine


class ProjectController(QObject):
    """
    Central mediator between the SafeChunkEngine and the UI.

    Signals:
        status_message  — emitted with human-readable status text for the status bar
        sync_completed  — emitted after a successful disk commit (data is safe)
        fault_occurred  — emitted when a critical IO error happens (show error to user)
        dirty_changed   — emitted with True when unsaved changes exist, False when clean
        project_loaded  — emitted once the engine is fully attached and ready to serve data.
                          All widgets should connect refresh_from_engine() to THIS signal,
                          not to sync_completed, and not rely on __init__-time refresh.
    """
    status_message = Signal(str)
    sync_completed = Signal()
    fault_occurred = Signal(str)
    dirty_changed  = Signal(bool)
    project_loaded = Signal()       # ← THE FIX: fired when engine is ready for data reads

    def __init__(self):
        super().__init__()
        self.engine = None
        self.active_project_id = None

    def init_project(self, project_id: str, is_new: bool = False) -> bool:
        """
        Initialises or opens a project and wires all engine callbacks to Qt signals.
        Returns True on success, False on failure.
        """
        if is_new:
            self.engine, status = SafeChunkEngine.new(project_id)
        else:
            self.engine, status = SafeChunkEngine.open(project_id)

        if self.engine and self.engine.is_active():
            self.active_project_id = project_id

            # Wire all engine callbacks to Qt signals so the UI reacts correctly
            self.engine.on_sync   = lambda: self.sync_completed.emit()
            self.engine.on_status = lambda msg: self.status_message.emit(msg)
            self.engine.on_fault  = lambda msg: self.fault_occurred.emit(msg)   # FIX: was never wired
            self.engine.on_dirty  = lambda dirty: self.dirty_changed.emit(dirty) # NEW

            # Auto-create an initial checkpoint so .bak files exist from day one
            # and there is always at least one restore point for new projects.
            if is_new:
                self.engine.create_checkpoint(label="initial", notes="Auto-checkpoint on project creation")

            # Signal all widgets that the engine is ready and they can now load their data.
            # This is the correct moment — engine is attached, data is readable.
            self.project_loaded.emit()
            return True

        return False

    def save_chunk_data(self, chunk_name: str, data: dict):
        """
        The key method for autosave.
        Passes data to the engine's staging area (debounced write).
        """
        if self.engine and self.engine.is_active():
            self.engine.stage_update(data, chunk_name)

    def close_project(self):
        """Force-syncs and detaches the engine cleanly."""
        if self.engine:
            self.engine.force_sync()
            self.engine.detach()
            self.engine = None
            self.active_project_id = None

    # --------------------------------------------------------------------------
    # CHECKPOINT API — used by CheckpointDialog
    # --------------------------------------------------------------------------

    def save_checkpoint(self, label: str = "manual", notes: str = "") -> str | None:
        """
        Creates a named checkpoint. Returns the zip filename, or None on failure.
        Force-syncs before snapshotting so the checkpoint is always up-to-date.
        """
        if self.engine and self.engine.is_active():
            return self.engine.create_checkpoint(label=label, notes=notes)
        return None

    def load_checkpoint(self, zip_name: str) -> bool:
        """
        Restores the project from a checkpoint ZIP.
        Emits sync_completed after a successful restore so the UI refreshes.
        """
        if self.engine and self.engine.is_active():
            success = self.engine.restore_checkpoint(zip_name)
            if success:
                self.sync_completed.emit()
                self.project_loaded.emit()  # Re-trigger full UI repopulation after restore
            return success
        return False

    def list_checkpoints(self) -> list:
        """Returns checkpoint metadata list (newest first)."""
        if self.engine and self.engine.is_active():
            return self.engine.list_checkpoints()
        return []

    def delete_checkpoint(self, zip_name: str) -> bool:
        """Deletes a specific checkpoint by filename."""
        if self.engine and self.engine.is_active():
            return self.engine.delete_checkpoint(zip_name)
        return False

    def get_engine_logs(self) -> list:
        """Returns the engine's rolling log history for display in the Logs panel."""
        if self.engine:
            return list(self.engine.log_history)
        return []

    def get_health_report(self) -> dict:
        """Returns engine diagnostics."""
        if self.engine:
            return self.engine.get_health_report()
        return {}

    def is_dirty(self) -> bool:
        """Returns True if there are pending unsaved changes in memory."""
        if self.engine:
            return self.engine.is_dirty()
        return False


# Single instance used across the app
controller = ProjectController()