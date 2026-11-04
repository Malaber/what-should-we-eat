import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('simulator', Path(__file__).parents[2] / 'ios/Onionary/Scripts/resolve_simulator.py')
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)


def test_selection_is_numeric_and_independent_of_installed_device_order():
    runtimes = [
        {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-27-2', 'version': '27.2', 'isAvailable': True},
        {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-27-10', 'version': '27.10', 'isAvailable': True},
        {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-28-0', 'version': '28.0', 'isAvailable': False},
    ]
    assert simulator.select_runtime(runtimes).endswith('iOS-27-10')
    assert simulator.select_runtime(list(reversed(runtimes))).endswith('iOS-27-10')
    assert simulator.DEFAULT_DEVICE == 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro'
