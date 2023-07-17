# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ToHNOR
                                 A QGIS plugin
 Realiza a conversão de altitudes para o modelo hgeoHNOR2020
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-01-26
        git sha              : $Format:%H$
        copyright            : (C) 2023 by IFG - Eng. Cartográfica e de Agrimensura
        email                : joao.paulo@ifg.edu.br
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QCheckBox
from qgis.core import *
from qgis.core import QgsVectorLayer, QgsProject
from qgis.core import QgsField
from qgis.core import QgsFeatureRequest
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .to_HNOR_dialog import ToHNORDialog
import os.path
import processing
import requests
import sys, os
import PyQt5
import qgsmaplayercombobox
import qgis.analysis

from osgeo import ogr
from qgis.analysis import QgsInterpolator

class ToHNOR:
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
            'ToHNOR_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&toHNOR')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('ToHNOR', message)


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

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/to_HNOR/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'toHNOR'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&toHNOR'),
                action)
            self.iface.removeToolBarIcon(action)
 
    def checkbox_changed(self, state):
        if state == 2:  # O estado 2 representa o QCheckBox marcado
            self.incerteza_valor = feature[self.incerteza]
            self.incerteza_altitude_geom_valor = feature[self.atributo_precisao]
            print("marcado")
        else:
            self.incerteza_valor = feature[self.incerteza]
            self.incerteza_altitude_geom_valor = 0.0
            print("desmarcado")

    def carregaVetor(self):
        """Preenche o combox com as layers vetoriais"""
        self.dlg.cbEntrada.clear()
        self.dlg.cbAltitude.clear()
        layers = [layer for layer in QgsProject.instance().mapLayers().values()]
        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.cbEntrada.addItems(layer_list)
        
    def abrirVetor(self):
        """abre a janela de diálogo para abrir uma layer"""
        camada_abrir = str(QFileDialog.getOpenFileName(caption = "Escolha a camada...",
                                                        filter="Shapefiles (*.shp)") [0])
        # se camada_abrir não for vazio
        if (camada_abrir != ""):
            self.iface.addVectorLayer(camada_abrir, str.split(os.path.basename(camada_abrir),".") [0], "ogr")
            self.carregaVetor()

    def update_combobox2(self):
        self.dlg.cbAltitude.clear()
        selectedLayerText = self.dlg.cbEntrada.currentText()
        selectedLayer = QgsProject.instance().mapLayersByName(str(selectedLayerText))[0]
        fields = [field.name() for field in selectedLayer.fields()]
        if selectedLayer:
            self.dlg.cbAltitude.addItems(fields)
            self.dlg.cbSigma_h.addItems(fields)
            return selectedLayer
            
    def salvarSaida(self):
        """Seleciona o diretório de saida"""
        camada_salvar = str(QFileDialog.getSaveFileName(caption = "Escolha a camada de saída",
                                                        filter="Shapefiles (*.shp)") [0])
        return camada_salvar

    def isfloat(num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def variaveis(self):
        """define as variáveis para a função run"""
        camadaEntradaText = self.dlg.cbEntrada.currentText()
        self.camadaEntrada = QgsProject.instance().mapLayersByName(str(camadaEntradaText))[0]
        self.camadaSaida = self.salvarSaida()
 #       camadaSaidaIndex = self.camadaSaidaText.fields().indexFromName(str.split(os.path.basename(self.camada_salvar)))
        self.limitesEntrada = self.camadaEntrada.extent()
        self.atributo_altitude = self.camadaEntrada.fields().indexFromName(str(self.dlg.cbAltitude.currentText()))
        self.atributo_precisao = self.camadaEntrada.fields().indexFromName(str(self.dlg.cbSigma_h.currentText()))
                  
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ToHNORDialog()

        # show the dialog
        self.dlg.show()
         
        # Adicionando as funções criadas
        self.carregaVetor()
        self.dlg.tbEntrada.clicked.connect(self.abrirVetor) 
        self.dlg.cbEntrada.activated.connect(self.update_combobox2)

        # Habilitar ou desabilitar o cbSigma_h dependendo do cbPrecisao
        self.dlg.cbPrecisao.setChecked(False)  # Desmarcar inicialmente
        self.dlg.cbPrecisao.stateChanged.connect(lambda state: self.dlg.cbSigma_h.setEnabled(state == Qt.Checked))
      
        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
              
            self.variaveis()
            
            #verificar se os atributos de entrada são do tipo float
            features = self.camadaEntrada.getFeatures() 
            for feature in features:
                try:
                    float(feature[self.atributo_altitude])
                    tipo_atributo_altitude = "float"
                except ValueError:
                    tipo_atributo_altitude = "nofloat"
 
            features = self.camadaEntrada.getFeatures() 
            for feature in features:
                try:
                    float(feature[self.atributo_precisao])
                    tipo_atributo_precisao = "float"
                except ValueError:
                    tipo_atributo_precisao = "nofloat"
            
            if tipo_atributo_altitude == "nofloat":
                print("O atributo selecionado não é do tipo float(double)")
                iface.messageBar().pushMessage("Erro", f"O atributo {self.atributo_altitude} não é do tipo float.", level=Qgis.Critical)
               # exit()

            else:
                #Buscar Grade do Fator de Conversão
                
                grade_url = "http://github.com/pibic-ifg2022/PIBIC2022/raw/main/to_hnor/grades/FC.sdat"
                save_path_grade = 'C:/temp/FC.sdat'
                grade_url2 = "http://github.com/pibic-ifg2022/PIBIC2022/raw/main/to_hnor/grades/FC.sgrd"
                save_path_grade2 = 'C:/temp/FC.sgrd'
    
                incerteza_url = "http://github.com/pibic-ifg2022/PIBIC2022/raw/main/to_hnor/grades/incerteza3.sdat"
                save_path_incerteza = 'C:/temp/incerteza3.sdat'
                incerteza_url2 = "http://github.com/pibic-ifg2022/PIBIC2022/raw/main/to_hnor/grades/incerteza3.sgrd"
                save_path_incerteza2 = 'C:/temp/incerteza3.sgrd'
    
                # Call the function to download the image
                response = requests.get(grade_url)
                if response.status_code == 200:
                    with open(save_path_grade, 'wb') as file:
                        file.write(response.content)
    
                response = requests.get(grade_url2)
                if response.status_code == 200:
                    with open(save_path_grade2, 'wb') as file:
                        file.write(response.content)
    
                response = requests.get(incerteza_url)
                if response.status_code == 200:
                    with open(save_path_incerteza, 'wb') as file:
                        file.write(response.content)
    
                response = requests.get(incerteza_url2)
                if response.status_code == 200:
                    with open(save_path_incerteza2, 'wb') as file:
                        file.write(response.content)
    
                params1 = {
                    'SHAPES': self.camadaEntrada,
                #   'GRIDS': ['D:/GitHUB_Repositorios/PIBIC2022/to_hnor/grades/tps.sdat','D:/GitHUB_Repositorios/PIBIC2022/to_hnor/grades/incerteza3.sdat'],
                    'GRIDS': ['C:/temp/FC.sdat','C:/temp/incerteza3.sdat'],
                    'RESULT':self.camadaSaida,
                    'RESAMPLING': 2
                }
                
                print(params1)
                #QgsProject.instance().addMapLayer(grade)
                processing.run("saga:addrastervaluestofeatures", params1)
                nome_camada_saida = str.split(os.path.basename(self.camadaSaida),".") [0]
                self.iface.addVectorLayer(self.camadaSaida, nome_camada_saida , "ogr")
                self.carregaVetor()
    
                layer = QgsProject.instance().mapLayersByName(nome_camada_saida)[0]
                provider = layer.dataProvider()
                provider.addAttributes([QgsField("Hnormal",QVariant.Double)])
                provider.addAttributes([QgsField("HN_Inc",QVariant.Double)])
                layer.updateFields()
                self.altitude_normal_index = layer.fields().indexFromName('Hnormal')
                self.incerteza_index = layer.fields().indexFromName('HN_Inc')
                self.fator_conversao = layer.fields().indexFromName('FC')
                self.incerteza = layer.fields().indexFromName('incerteza3')
    
                layer.startEditing()
                for feature in layer.getFeatures():
                    #Cálculo da Altitude Normal
                    self.fator_conversao_valor = feature[self.fator_conversao]
                    self.altitude_geom_valor = feature[self.atributo_altitude]
                    self.altitude_normal = self.altitude_geom_valor - self.fator_conversao_valor
                    feature[self.altitude_normal_index]=self.altitude_normal
                    layer.changeAttributeValue(feature.id(),self.altitude_normal_index, self.altitude_normal)
    
                    #Cálculo da Incerteza
                    if self.dlg.cbPrecisao.isChecked():
                        self.incerteza_valor = feature[self.incerteza]
                        self.incerteza_altitude_geom_valor = feature[self.atributo_precisao]         
                        if self.incerteza_altitude_geom_valor:
                            self.incerteza_altitude_normal = (self.incerteza_altitude_geom_valor**2 + self.incerteza_valor**2)**(0.5)
                        else:
                            self.incerteza_altitude_normal = self.incerteza_valor
                    else:
                        self.incerteza_valor = feature[self.incerteza]
                        self.incerteza_altitude_geom_valor = 0.0                
                        self.incerteza_altitude_normal = self.incerteza_valor  
    
                    
                    feature[self.incerteza_index]=self.incerteza_altitude_normal
                    layer.changeAttributeValue(feature.id(),self.incerteza_index, self.incerteza_altitude_normal)
    
                layer.updateFields()
                layer.commitChanges()
            
    pass