"""Sanity test using PSScriptAnalyzer."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re

import lib.types as t

from lib.sanity import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    SANITY_ROOT,
)

from lib.target import (
    TestTarget,
)

from lib.util import (
    SubprocessError,
    find_executable,
    ANSIBLE_TEST_DATA_ROOT,
)

from lib.util_common import (
    run_command,
)

from lib.config import (
    SanityConfig,
)

from lib.data import (
    data_context,
)


class PslintTest(SanityVersionNeutral):
    """Sanity test using PSScriptAnalyzer."""
    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'AnsibleTest'

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] in ('.ps1', '.psm1', '.psd1')]

    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        if not find_executable('pwsh', required='warning'):
            return SanitySkipped(self.name)

        cmds = []

        if args.requirements:
            cmds.append([os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'sanity.ps1')])

        cmds.append([os.path.join(SANITY_ROOT, 'pslint', 'pslint.ps1')] + paths)

        stdout = ''

        for cmd in cmds:
            try:
                stdout, stderr = run_command(args, cmd, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name)

        severity = [
            'Information',
            'Warning',
            'Error',
            'ParseError',
        ]

        cwd = data_context().content.root + '/'

        # replace unicode smart quotes and ellipsis with ascii versions
        stdout = re.sub(u'[\u2018\u2019]', "'", stdout)
        stdout = re.sub(u'[\u201c\u201d]', '"', stdout)
        stdout = re.sub(u'[\u2026]', '...', stdout)

        messages = json.loads(stdout)

        errors = [SanityMessage(
            code=m['RuleName'],
            message=m['Message'],
            path=m['ScriptPath'].replace(cwd, ''),
            line=m['Line'] or 0,
            column=m['Column'] or 0,
            level=severity[m['Severity']],
        ) for m in messages]

        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
