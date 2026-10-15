"""PerformanceMonitor must not require psutil to import or construct."""
from valis_workstation.utils import performance


def test_monitor_works_without_psutil(monkeypatch):
    monkeypatch.setattr(performance, "psutil", None)
    monitor = performance.PerformanceMonitor()
    assert monitor.sample_memory() == 0.0
    assert monitor.get_summary() is not None
