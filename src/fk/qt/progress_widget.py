#  Flowkeeper - Pomodoro timer for power users and teams
#  Copyright (c) 2023 Constantine Kulak
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from fk.core.abstract_event_source import AbstractEventSource
from fk.core.backlog import Backlog
from fk.core.event_source_holder import EventSourceHolder, AfterSourceChanged
from fk.core.tag import Tag


class ProgressWidget(QWidget):
    _label: QLabel

    def __init__(self,
                 parent: QWidget,
                 source_holder: EventSourceHolder):
        super().__init__(parent)
        self.setObjectName('progress')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._label = QLabel(self)
        self._label.setObjectName("footerLabel")
        layout.addWidget(self._label)
        self.setVisible(False)
        source_holder.on(AfterSourceChanged, self._on_source_changed)

    def _on_source_changed(self, event: str, source: AbstractEventSource) -> None:
        self.update_progress(None)
        source.on("AfterWorkitem*", lambda workitem, **kwargs: self.update_progress(workitem.get_parent()))
        source.on("AfterPomodoro*", lambda workitem, **kwargs: self.update_progress(workitem.get_parent()))

    def update_progress(self, backlog_or_tag: Backlog | Tag | None) -> None:
        total_items: int = 0
        done_items: int = 0
        total_pomodoros: int = 0
        done_pomodoros: int = 0
        if backlog_or_tag:
            workitems = backlog_or_tag.values() if type(backlog_or_tag) is Backlog else backlog_or_tag.get_workitems()

            for wi in workitems:
                # Non startable workitems and not finished are not counted (they don't have any pomodoros, meaning they are not planned)
                if not wi.is_startable() and not wi.is_sealed() and not wi.is_running():
                    continue
                total_items += 1
                # sealed items are counted as done
                if wi.is_sealed():
                    done_items += 1

                for p in wi.values():
                    # TODO: activate with a configuration ?
                    # # We do not count non started pomodoros of sealed workitems
                    # if wi.is_sealed() and p.is_startable():
                    #     print(" ➡️ ignored", end="")
                    #     continue
                    total_pomodoros += 1
                    if p.is_finished() or p.is_canceled():
                        done_pomodoros += 1
                    # We count non started pomodoros of sealed workitems as done
                    if wi.is_sealed() and p.is_startable():
                        done_pomodoros += 1

        self.setVisible(total_pomodoros > 0 or total_items > 0)
        self._label.setVisible(total_pomodoros > 0 or total_items > 0)
        percent_items = f' ({round(100 * done_items / total_items)}%)' if total_items > 0 else ''
        percent_pomodoros = f' ({round(100 * done_pomodoros / total_pomodoros)}%)' if total_pomodoros > 0 else ''
        self._label.setText(f'✔️ planned items : {done_items} of {total_items} done{percent_items} - '
                            f'🍅 pomodoros : {done_pomodoros} of {total_pomodoros} done{percent_pomodoros}')
