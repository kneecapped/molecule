#  Copyright (c) 2015-2017 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os

import pytest
import sh

from molecule import config
from molecule.dependency import gilt


@pytest.fixture
def _patched_gilt_has_requirements_file(mocker):
    m = mocker.patch('molecule.dependency.gilt.Gilt._has_requirements_file')
    m.return_value = True

    return m


@pytest.fixture
def _dependency_section_data():
    return {
        'dependency': {
            'name': 'gilt',
            'options': {
                'foo': 'bar',
            },
            'env': {
                'FOO': 'bar',
            }
        }
    }


# NOTE(retr0h): The use of the `patched_config_validate` fixture, disables
# config.Config._validate from executing.  Thus preventing odd side-effects
# throughout patched.assert_called unit tests.
@pytest.fixture
def _instance(_dependency_section_data, patched_config_validate,
              config_instance):
    return gilt.Gilt(config_instance)


@pytest.fixture
def gilt_config(_instance):
    return os.path.join(_instance._config.scenario.directory, 'gilt.yml')


def test_config_private_member(_instance):
    assert isinstance(_instance._config, config.Config)


def test_default_options_property(gilt_config, _instance):
    x = {'config': gilt_config}

    assert x == _instance.default_options


def test_default_env_property(_instance):
    assert 'MOLECULE_FILE' in _instance.default_env
    assert 'MOLECULE_INVENTORY_FILE' in _instance.default_env
    assert 'MOLECULE_SCENARIO_DIRECTORY' in _instance.default_env
    assert 'MOLECULE_INSTANCE_CONFIG' in _instance.default_env


@pytest.mark.parametrize(
    'config_instance', ['_dependency_section_data'], indirect=True)
def test_name_property(_instance):
    assert 'gilt' == _instance.name


def test_enabled_property(_instance):
    assert _instance.enabled


@pytest.mark.parametrize(
    'config_instance', ['_dependency_section_data'], indirect=True)
def test_options_property(gilt_config, _instance):
    x = {'config': gilt_config, 'foo': 'bar'}

    assert x == _instance.options


@pytest.mark.parametrize(
    'config_instance', ['_dependency_section_data'], indirect=True)
def test_options_property_handles_cli_args(gilt_config, _instance):
    _instance._config.args = {'debug': True}
    x = {'config': gilt_config, 'foo': 'bar', 'debug': True}

    assert x == _instance.options


@pytest.mark.parametrize(
    'config_instance', ['_dependency_section_data'], indirect=True)
def test_env_property(_instance):
    assert 'bar' == _instance.env['FOO']


@pytest.mark.parametrize(
    'config_instance', ['_dependency_section_data'], indirect=True)
def test_bake(gilt_config, _instance):
    _instance.bake()
    x = [
        str(sh.gilt), '--foo=bar', '--config={}'.format(gilt_config), 'overlay'
    ]
    result = str(_instance._sh_command).split()

    assert sorted(x) == sorted(result)


def test_execute(patched_run_command, _patched_gilt_has_requirements_file,
                 patched_logger_success, _instance):
    _instance._sh_command = 'patched-command'
    _instance.execute()

    patched_run_command.assert_called_once_with('patched-command', debug=False)

    msg = 'Dependency completed successfully.'
    patched_logger_success.assert_called_once_with(msg)


def test_execute_does_not_execute_when_disabled(
        patched_run_command, patched_logger_warn, _instance):
    _instance._config.config['dependency']['enabled'] = False
    _instance.execute()

    assert not patched_run_command.called

    msg = 'Skipping, dependency is disabled.'
    patched_logger_warn.assert_called_once_with(msg)


def test_execute_does_not_execute_when_no_requirements_file(
        patched_run_command, _patched_gilt_has_requirements_file,
        patched_logger_warn, _instance):
    _patched_gilt_has_requirements_file.return_value = False
    _instance.execute()

    assert not patched_run_command.called

    msg = 'Skipping, missing the requirements file.'
    patched_logger_warn.assert_called_once_with(msg)


def test_execute_bakes(patched_run_command, gilt_config,
                       _patched_gilt_has_requirements_file, _instance):
    _instance.execute()
    assert _instance._sh_command is not None

    assert 1 == patched_run_command.call_count


def test_executes_catches_and_exits_return_code(
        patched_run_command, _patched_gilt_has_requirements_file, _instance):
    patched_run_command.side_effect = sh.ErrorReturnCode_1(sh.gilt, b'', b'')
    with pytest.raises(SystemExit) as e:
        _instance.execute()

    assert 1 == e.value.code


def test_config_file(_instance, gilt_config):
    assert gilt_config == _instance._config_file()


def test_has_requirements_file(_instance):
    assert not _instance._has_requirements_file()
