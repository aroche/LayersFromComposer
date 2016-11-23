# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayersFromComposer
                                 A QGIS plugin
 For a composer with locked layers, will set activated layers and styles in the main canvas accordingly
                              -------------------
        begin                : 2016-11-22
        git sha              : $Format:%H$
        copyright            : (C) 2016 by A. Roche
        email                : aroche@photoherbarium.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox
from PyQt4.QtXml import QDomDocument
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from layers_from_composer_dialog import LayersFromComposerDialog
import os.path
from qgis.core import QgsMessageLog, QgsMapLayerRegistry


class LayersFromComposer:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LayersFromComposer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Restore layers from composer')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'LayersFromComposer')
        self.toolbar.setObjectName(u'LayersFromComposer')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LayersFromComposer', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = LayersFromComposerDialog()
        
        # signals
        self.dlg.comboBox.currentIndexChanged.connect(self.populate_maps)
        self.dlg.comboBox_2.currentIndexChanged.connect(self.enable_style_check)

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/LayersFromComposer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Restore layer visibility from composer'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Restore layers from composer'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        
    def populate_composers(self):
        """ Populates the first comboBox with eligiblecomposer names
            Filters out the composers with no maps with locked layers """
        self.dlg.comboBox.clear()
        self.dlg.comboBox_2.clear()
        for i, composer in enumerate(self.iface.activeComposers()):
            composition = composer.composition()
            maps = composition.composerMapItems()
            if len(maps) == 0:
                continue
            hasLockedLayers = False
            for theMap in maps:
                hasLockedLayers = hasLockedLayers or (theMap.keepLayerSet() and len(theMap.layerSet()) > 0)
            if hasLockedLayers:
                self.dlg.comboBox.insertItem(i, composer.composerWindow().windowTitle())
                
    def populate_maps(self):
        """ Gets the maps for the selected composer and populates second combobox """
        composition = self.getSelectedComposition()
        if composition is None:
            return
        maps = composition.composerMapItems()
        self.dlg.comboBox_2.clear()
        for map_ in maps:
            if map_.keepLayerSet():
                self.dlg.comboBox_2.addItem(map_.displayName(), map_.id())
                
    def enable_style_check(self):
        """ checks if styles are locked and enables the checkbox """
        composition = self.getSelectedComposition()
        if composition:
            theMap = self.getSelectedMap()
            if theMap and theMap.keepLayerStyles():
                self.dlg.checkBox.setEnabled(True)
            else:
                self.dlg.checkBox.setEnabled(False)
                  
            
    def getSelectedComposition(self):
        """ returns the composition corresponding to selected composer """
        name = self.dlg.comboBox.currentText()
        for composer in self.iface.activeComposers():
            if composer.composerWindow().windowTitle() == name:
                return composer.composition()
                
    def getSelectedMap(self):
        composition = self.getSelectedComposition()
        if composition:
            mapId= self.dlg.comboBox_2.itemData(self.dlg.comboBox_2.currentIndex())
            if mapId is not None:
                theMap = composition.getComposerMapById(mapId)
                return theMap

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.populate_composers()
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            theMap = self.getSelectedMap()
            layers = theMap.layerSet()
            
            # check if some layers do not exist in legend and warns
            for compLyr in layers:
                if not QgsMapLayerRegistry.instance().mapLayers().has_key(compLyr):
                    ret = QMessageBox.warning(self, self.tr("Layers frm composer"),
                        self.tr("Some of the layers registered in the composer " + \
                        "do not exist anymore in the project.\nDo you want to continue?"),
                        QMessageBox.Yes | QMessageBox.No)
                    if not ret:
                        return
                    break
            
            for lyr in self.iface.legendInterface().layers():
                # set styles
                if (lyr.id() in layers) and self.dlg.checkBox.isChecked() and theMap.keepLayerStyles():
                    style = theMap.layerStyleOverrides()[lyr.id()]
                    doc = QDomDocument()
                    doc.setContent(style.encode('utf-8'))
                    res, error = lyr.importNamedStyle(doc)
                    if error:
                        QgsMessageLog.logMessage(self.tr("Error in setting layer style for ") + lyr.id() + ': ' + error, level=QgsMessageLog.ERROR)
                    
                self.iface.legendInterface().setLayerVisible(lyr, lyr.id() in layers)

