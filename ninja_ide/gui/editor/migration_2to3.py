# -*- coding: utf-8 -*-
#
# This file is part of NINJA-IDE (http://ninja-ide.org).
#
# NINJA-IDE is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# NINJA-IDE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NINJA-IDE; If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import
from __future__ import unicode_literals

import subprocess

from PyQt4.QtCore import QThread

from ninja_ide.core import file_manager
from ninja_ide.core import settings


class MigrationTo3(QThread):

    def __init__(self, editor):
        QThread.__init__(self)
        self._editor = editor
        self._path = ''
        self.migration_data = {}

    def check_style(self):
        if not self.isRunning():
            self._path = self._editor.ID
            self.start()

    def run(self):
        self.sleep(1)
        exts = settings.SYNTAX.get('python')['extension']
        file_ext = file_manager.get_file_extension(self._path)
        if file_ext in exts:
            self.migration_data = {}
            lineno = 0
            lines_to_remove = []
            lines_to_add = []
            parsing_adds = False
            output = subprocess.check_output(['2to3', self._path])
            output = output.split('\n')
            for line in output[2:]:
                if line.startswith('+'):
                    lines_to_add.append(line)
                    parsing_adds = True
                    continue

                if parsing_adds:
                    # Add in migration
                    removes = '\n'.join([liner
                        for _, liner in lines_to_remove])
                    adds = '\n'.join(lines_to_add)
                    message = self.tr(
                        'The actual code look like this:\n%s\n\n'
                        'For Python3 support should look like:\n%s' %
                        (removes, adds))
                    lineno = -1
                    for nro, _ in lines_to_remove:
                        if lineno == -1:
                            lineno = nro
                        self.migration_data[nro] = (message, lineno)
                    parsing_adds = False
                    lines_to_add = []
                    lines_to_remove = []

                if line.startswith('-'):
                    lines_to_remove.append((lineno, line))
                lineno += 1

                if line.startswith('@@'):
                    lineno = int(line[line.index('-') + 1:line.index(',')]) - 1
