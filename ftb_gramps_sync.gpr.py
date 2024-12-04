#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2024-2025 Vazar00
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
from gramps.gen.plug._pluginreg import *
# from gramps.gen.const import GRAMPS_LOCALE as glocale
# _ = glocale.translation.gettext

"""GRAMPS registration file."""

register(
    TOOL,
    id="FTB_Gramps_sync",
    name="FTB to Gramps data transfer",
    description=_("Transfers data from MyHeritage Family Tree Builder to Gramps"),
    version = '1.0.0',
    gramps_target_version="5.2",
    status=BETA,
    fname="ftb_gramps_sync.py",
    authors=["Vazar"],
    authors_email=["aleksandr.mincenko01@gmail.com"],
    category=TOOL_DBPROC,
    toolclass="FTB_Gramps_sync",
    optionclass="FTB_Gramps_sync_options",
    tool_modes=[TOOL_MODE_GUI],
)