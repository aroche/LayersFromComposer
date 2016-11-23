# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayersFromComposer
                                 A QGIS plugin
 For a composer with locked layers, will set activated layers and styles in the main canvas accordingly
                             -------------------
        begin                : 2016-11-22
        copyright            : (C) 2016 by A. Roche
        email                : aroche@photoherbarium.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LayersFromComposer class from file LayersFromComposer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .layers_from_composer import LayersFromComposer
    return LayersFromComposer(iface)
