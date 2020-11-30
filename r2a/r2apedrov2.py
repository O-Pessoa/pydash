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
        self.lastDecreaseNetworkReliability = 0
        self.bpsHistory = []
        self.QiHistory = []
        self.initWindowSize = 10
        self.windowSize = self.initWindowSize
        self.windowSizeQi = 5
        self.minDownload = 0
        self.avgDownload = 0
        self.maxDownload = 0
        self.networkReliability = 100
        self.timeReturnNetworkReliability = 10
        self.timeVariationMultiplier = 1

        self.bufferSizeLimitsPct = [70,60,40,30]
        self.maximumRisePercentageQi = 2
        self.networkReliabilityLimit = 5


    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        msg.add_quality_id(self.qi[self.setQI()])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        currentBps = msg.get_bit_length()/(time()-self.lastRequestTime) # Velocidade Atual
        self.bpsHistory.append(currentBps) # Historico de velocidade
        
        analyzedWindow = self.bpsHistory[-self.windowSize:] # Janela de velocidades que será analisada
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
        pctBufferSize = (currentBufferSize/self.maxBufferSize)*100 # Tamanho do buffer atual em procentagem do tamanho maximo
        
        self.setNetworkReliability(currentBufferSize)

        # Define os valores possiveis para a velocidade de referencia de acorco com o tamanho do Buffer

        if pctBufferSize >= self.bufferSizeLimitsPct[0]/(self.networkReliability/100):
            referenceValue = self.maxDownload

        elif pctBufferSize >= self.bufferSizeLimitsPct[1]/(self.networkReliability/100):
            referenceValue = (self.avgDownload+self.maxDownload)/2

        elif pctBufferSize >= self.bufferSizeLimitsPct[2]/(self.networkReliability/100):
            referenceValue = self.avgDownload

        elif pctBufferSize >= self.bufferSizeLimitsPct[3]/(self.networkReliability/100):
            referenceValue = (self.avgDownload+self.minDownload)/2
    
        else:
            referenceValue = self.minDownload
        

        QiRetornado = self.getIndiceQiMenorMaisProximo(referenceValue)
        
        analyzedWindow = self.QiHistory[-self.windowSizeQi:] # Janela de analise do historico dos Qi retornados
        avgAnalyzedWindow = int(sum(analyzedWindow+[QiRetornado])/(len(analyzedWindow)+1)) # Media dos valores da janela analisada
        if QiRetornado > avgAnalyzedWindow and abs(QiRetornado - avgAnalyzedWindow) > avgAnalyzedWindow*(1+(self.maximumRisePercentageQi/100)):
            # Caso o Qi que iria se retornado for muito maior que a media anterior ele será retornado como o valor limite da taxa de subida de Qi
            # Esse if serve para evitar grandes subidas no Qi repentinamente
            QiRetornado = int(avgAnalyzedWindow*(1+(self.maximumRisePercentageQi/100)))

        self.QiHistory.append(QiRetornado) # Historico de Indices retornados
        self.lastRequestTime = time()
        return QiRetornado

    def setNetworkReliability(self, currentBufferSize): # Define a confiabilidade da rede
        if self.lastRequestTime != 0:
            deltaTime = time()-self.lastRequestTime

            if deltaTime > self.networkReliabilityLimit: # Diminuir a confiabilidade da rede caso tenha um tempo muito grande sem receber pacotes
                self.lastDecreaseNetworkReliability = time()
                self.windowSize = int(self.initWindowSize/1.4)
                self.networkReliability -=  deltaTime*self.timeVariationMultiplier
                if self.networkReliability < 1:
                    self.networkReliability = 1

            if self.lastDecreaseNetworkReliability != 0: # Voltar a confiabilidade da rede depois de um determinado tempo sem cair
                if time() - self.lastDecreaseNetworkReliability >= self.timeReturnNetworkReliability:
                    self.networkReliability += 5
                    self.windowSize = self.initWindowSize
                    if self.networkReliability > 100:
                        self.networkReliability = 100
                        self.lastDecreaseNetworkReliability = 0


    def carregarParametros(self):
        # Carrega o self.maxBufferSize do json
        
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
