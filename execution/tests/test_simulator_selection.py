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
    for runtime in runtimes:
        runtime['supportedDeviceTypes'] = [{'identifier': simulator.DEFAULT_DEVICE}]
    assert simulator.select_runtime(runtimes).endswith('iOS-27-10')
    assert simulator.select_runtime(list(reversed(runtimes))).endswith('iOS-27-10')
    assert simulator.DEFAULT_DEVICE == 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro'


def test_newer_duo_only_runtime_is_not_used_for_standard_phone():
    runtimes = [
        {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-27-0', 'version': '27.0', 'isAvailable': True,
         'supportedDeviceTypes': [{'identifier': simulator.DEFAULT_DEVICE}]},
        {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-27-1', 'version': '27.1', 'isAvailable': True,
         'supportedDeviceTypes': [{'identifier': 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo'}]},
    ]
    assert simulator.select_runtime(runtimes).endswith('iOS-27-0')
