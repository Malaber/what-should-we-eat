import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('simulator', Path(__file__).parents[2] / 'ios/Onionary/Scripts/resolve_simulator.py')
simulator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simulator)
DUO = 'com.apple.CoreSimulator.SimDeviceType.iPhone-Duo'


def runtime(version, device=DUO, available=True):
    return {'identifier': 'com.apple.CoreSimulator.SimRuntime.iOS-' + version.replace('.', '-'),
            'version': version, 'isAvailable': available, 'supportedDeviceTypes': [{'identifier': device}]}


def test_declared_duo_runtime_wins_over_newer_installed_runtime():
    runtimes = [runtime('27.2'), runtime('27.1')]
    for order in (runtimes, list(reversed(runtimes))):
        assert simulator.select_runtime(order, DUO).endswith('iOS-27-1')
        assert simulator.select_runtime(order, DUO, '27.2').endswith('iOS-27-2')


@pytest.mark.parametrize('runtimes', [
    [runtime('27.2')],
    [runtime('27.1', available=False)],
    [runtime('27.1', device=simulator.DEFAULT_DEVICE)],
])
def test_missing_or_incompatible_pin_fails_without_fallback(runtimes):
    with pytest.raises(ValueError, match='no fallback'):
        simulator.select_runtime(runtimes, DUO)


def test_standard_phone_uses_270_even_when_newer_compatible_runtime_exists():
    runtimes = [runtime('27.2', simulator.DEFAULT_DEVICE), runtime('27.0', simulator.DEFAULT_DEVICE)]
    assert simulator.select_runtime(runtimes).endswith('iOS-27-0')
