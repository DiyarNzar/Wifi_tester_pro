"""
WiFi Tester Pro v6.0 - Threading Engine
Background task execution to prevent GUI freezing
"""

import threading
import queue
import time
import uuid
from typing import Callable, Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor, Future


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class Task:
    """Represents a background task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    func: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    progress_callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return end_time - self.started_at


class Engine:
    """
    Background task execution engine.
    Runs slow operations in threads to keep GUI responsive.
    Implements Singleton pattern.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_workers: int = 4):
        if self._initialized:
            return
        
        self._initialized = True
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, Task] = {}
        self._futures: Dict[str, Future] = {}
        self._running = True
        self._task_queue = queue.Queue()
        
        # Callbacks for UI updates (set by GUI)
        self._on_task_complete: Optional[Callable] = None
        self._on_task_error: Optional[Callable] = None
        self._on_task_progress: Optional[Callable] = None
        
        print("[Engine] Background task engine initialized")
    
    def submit(
        self,
        func: Callable,
        *args,
        name: str = "",
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> Task:
        """
        Submit a task for background execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            name: Human-readable task name
            callback: Called with result on success
            error_callback: Called with exception on failure
            progress_callback: Called with progress updates
            **kwargs: Keyword arguments for func
        
        Returns:
            Task object for tracking
        """
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            callback=callback,
            error_callback=error_callback,
            progress_callback=progress_callback,
        )
        
        self._tasks[task.id] = task
        
        # Submit to thread pool
        future = self._executor.submit(self._execute_task, task)
        self._futures[task.id] = future
        
        print(f"[Engine] Task submitted: {task.name} ({task.id})")
        return task
    
    def _execute_task(self, task: Task) -> Any:
        """Execute a task in background thread"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # Execute the function
            result = task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            
            # Call success callback
            if task.callback:
                try:
                    task.callback(result)
                except Exception as e:
                    print(f"[Engine] Callback error for {task.name}: {e}")
            
            # Global callback
            if self._on_task_complete:
                self._on_task_complete(task)
            
            print(f"[Engine] Task completed: {task.name} ({task.duration:.2f}s)")
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = time.time()
            
            # Call error callback
            if task.error_callback:
                try:
                    task.error_callback(e)
                except Exception as cb_error:
                    print(f"[Engine] Error callback failed: {cb_error}")
            
            # Global error callback
            if self._on_task_error:
                self._on_task_error(task)
            
            print(f"[Engine] Task failed: {task.name} - {e}")
            raise
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id not in self._futures:
            return False
        
        future = self._futures[task_id]
        cancelled = future.cancel()
        
        if cancelled:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
            print(f"[Engine] Task cancelled: {task_id}")
        
        return cancelled
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    def get_running_tasks(self) -> List[Task]:
        """Get list of currently running tasks"""
        return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
    
    def get_pending_tasks(self) -> List[Task]:
        """Get list of pending tasks"""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
    
    def is_busy(self) -> bool:
        """Check if any tasks are running"""
        return len(self.get_running_tasks()) > 0
    
    def wait_for(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for a specific task to complete"""
        if task_id not in self._futures:
            return None
        
        future = self._futures[task_id]
        return future.result(timeout=timeout)
    
    def wait_all(self, timeout: Optional[float] = None):
        """Wait for all tasks to complete"""
        for future in self._futures.values():
            try:
                future.result(timeout=timeout)
            except:
                pass
    
    def set_callbacks(
        self,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_progress: Optional[Callable] = None
    ):
        """Set global callbacks for task events"""
        self._on_task_complete = on_complete
        self._on_task_error = on_error
        self._on_task_progress = on_progress
    
    def report_progress(self, task_id: str, progress: float, message: str = ""):
        """
        Report progress for a running task.
        Call from within the task function.
        
        Args:
            task_id: Task identifier
            progress: Progress value 0.0 to 1.0
            message: Optional progress message
        """
        task = self._tasks.get(task_id)
        if task and task.progress_callback:
            try:
                task.progress_callback(progress, message)
            except:
                pass
        
        if self._on_task_progress:
            self._on_task_progress(task_id, progress, message)
    
    def clear_completed(self):
        """Remove completed tasks from tracking"""
        completed_ids = [
            tid for tid, task in self._tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
        ]
        
        for tid in completed_ids:
            del self._tasks[tid]
            if tid in self._futures:
                del self._futures[tid]
        
        print(f"[Engine] Cleared {len(completed_ids)} completed tasks")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the engine"""
        self._running = False
        self._executor.shutdown(wait=wait)
        print("[Engine] Shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global engine instance
_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Get or create the global engine instance"""
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine


def run_async(
    func: Callable,
    *args,
    callback: Optional[Callable] = None,
    error_callback: Optional[Callable] = None,
    **kwargs
) -> Task:
    """
    Convenience function to run a function asynchronously.
    
    Usage:
        def slow_scan():
            # ... scanning logic
            return results
        
        task = run_async(slow_scan, callback=on_scan_complete)
    """
    engine = get_engine()
    return engine.submit(
        func, *args,
        callback=callback,
        error_callback=error_callback,
        **kwargs
    )


__all__ = [
    'Engine',
    'Task',
    'TaskStatus',
    'get_engine',
    'run_async',
]
