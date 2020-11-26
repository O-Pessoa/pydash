# -*- coding: utf-8 -*-
"""
@author: Pedro Pessoa Ramos (180026488@aluno.unb.br) 22/11/2020

@description: ABR V2.0

"""

from time import time
import json
from player.parser import *
from r2a.ir2a import IR2A


class R2APedroV2(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

        self.nameLog = 'r2a.log'

        self.maxBufferSize = 0

        self.lastRequestTime = 0
        self.bpsHistory = []
        self.QiHistory = []
        self.windowSize = 10
        self.minDownload = 0
        self.avgDownload = 0
        self.maxDownload = 0

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.lastRequestTime = time()
        msg.add_quality_id(self.qi[self.setQI()])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        currentBps = msg.get_bit_length()/(time()-self.lastRequestTime) # Velocidade Atual
        self.bpsHistory.append(currentBps) # Historico de velocidade
        
        analyzedWindow = self.bpsHistory[len(self.bpsHistory)-self.windowSize:] # Janela de velocidades que será analisada
        self.minDownload = min(analyzedWindow) # Menor valor da janela analisada
        self.avgDownload = sum(analyzedWindow)/len(analyzedWindow) # Valor medio da janela analisada
        self.maxDownload = max(analyzedWindow) # Valor maximo da janela analisada

        self.send_up(msg)

    def initialize(self):
        self.logInitialize() # Iniciar o log
        self.carregarParametros() # Carregando os parametros do JSON

    def finalization(self):
        self.logFinalization() # Finalizar o log

    def getIndiceQiMenorMaisProximo(self, v):
        #irá retornar o indice do self.qi onde a qualidade do video seja mais proximo de v e menor que v
        indice = 0
        for key, value in enumerate(self.qi):
            if key == 0:
                indice = key
            if abs(v-value) < abs(v-self.qi[indice]) and (v-value) > 0:
                indice = key
        return indice

    def setQI(self):
        temp = self.whiteboard.get_playback_buffer_size()[-1:] # Variavel temporaria utilizada para transformar o array em float
        currentBufferSize = temp[0][1] if len(temp) != 0 else 0 # Tamanho atual do buffer

        
        
        
        
        ValorReferencia = self.avgDownload*(currentBufferSize/(self.maxBufferSize))

        QiRetornado = self.getIndiceQiMenorMaisProximo(ValorReferencia)
        self.QiHistory.append(QiRetornado)

        strRewriteLog = 'Ultimo Bps: '+str(self.bpsHistory[-1:])+'\n'
        strRewriteLog += 'Buffer atual: '+str(currentBufferSize)+'\n'
        strRewriteLog += 'Download min: '+str(self.minDownload)+'\n'
        strRewriteLog += 'Download avg: '+str(self.avgDownload)+'\n'
        strRewriteLog += 'Download max: '+str(self.maxDownload)+'\n'
        strRewriteLog += 'Qi Retonado: '+str(self.qi[QiRetornado])+'\n'
        strRewriteLog += 'Qi Retonado: '+str(QiRetornado)+'\n'
        self.rewriteLog(strRewriteLog)
        #QiRetornado = int(sum(self.QiHistory[-4:]+[QiRetornado])/5)
        return QiRetornado

    def carregarParametros(self):
        with open('dash_client.json') as f:
            dados = json.load(f)
            self.maxBufferSize = dados['max_buffer_size']

    #Funções de Log
    def rewriteLog(self, txt):
        self.clearLog()
        self.logInitialize()
        self.writeLog(txt)

    def writeLog(self, txt):
        with open(self.nameLog,'a') as log:
            log.writelines(str(txt)+'\n')

    def clearLog(self):
        with open(self.nameLog,'w') as log:
            log.writelines('')

    def logInitialize(self):
        self.clearLog()
        self.writeLog('#-START-#')
        self.writeLog('bps disponiveis: '+str(self.qi))

    def logFinalization(self):
        self.writeLog(self.whiteboard.get_playback_buffer_size())
        self.writeLog('#-END-#')
