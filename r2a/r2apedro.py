# -*- coding: utf-8 -*-
"""
@author: Pedro Pessoa Ramos (180026488@aluno.unb.br) 19/11/2020

@description: ABR V1.0

"""


from time import time

from player.parser import *
from r2a.ir2a import IR2A


class R2APedro(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

        self.lastRequestTime = 0

        self.bpsList = []
        self.downloadTaxas = (0,0,0)
        self.qtdPactosAnalisados = 10
        self.bufferSizesLimits = [40,30,25,20]
        self.confiabilidade = 1
        self.setLestDecrementoConfiabilidade = 0

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        self.rewriteLog('\n')
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.lastRequestTime = time()        

        msg.add_quality_id(self.qi[self.SetQualidade()])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        taxaDownload = msg.get_bit_length()/(time()-self.lastRequestTime)
        self.setConfiabilidade()
        self.bpsList.append(taxaDownload)
        if len(self.bpsList) == 0:
            self.downloadTaxas = (taxaDownload,taxaDownload,taxaDownload)
        else:
            downloadMin = min(self.bpsList[len(self.bpsList)-self.qtdPactosAnalisados:])
            downloadAvg = sum(self.bpsList[len(self.bpsList)-self.qtdPactosAnalisados:])/len(self.bpsList[len(self.bpsList)-self.qtdPactosAnalisados:])
            downloadMax = max(self.bpsList[len(self.bpsList)-self.qtdPactosAnalisados:])
            self.downloadTaxas = (downloadMin,downloadAvg,downloadMax)
        self.send_up(msg)

    def initialize(self):
        self.logInitialize()

    def finalization(self):
        self.logFinalization()

    def rewriteLog(self, txt):
        self.clearLog()
        self.logInitialize()
        self.writeLog(txt)

    def writeLog(self, txt):
        with open('r2apedro.log','a') as log:
            log.writelines(str(txt)+'\n')

    def clearLog(self):
        with open('r2apedro.log','w') as log:
            log.writelines('')

    def logInitialize(self):
        self.clearLog()
        self.writeLog('#-START-#')
        self.writeLog('bps disponiveis: '+str(self.qi))

    def logFinalization(self):
        self.writeLog(self.whiteboard.get_playback_buffer_size())
        self.writeLog('#-END-#')

    def SetQualidade(self):
        lastBuffer = self.whiteboard.get_playback_buffer_size()
        if len(lastBuffer) != 0:
            lastBuffer = lastBuffer[len(lastBuffer)-1][1]
        else:
            lastBuffer = 0
        
        if lastBuffer > int(self.bufferSizesLimits[0]*self.confiabilidade):

            valorReferencia = self.downloadTaxas[2]

        elif lastBuffer > int(self.bufferSizesLimits[1]*self.confiabilidade):

            valorReferencia = int(self.downloadTaxas[1]+self.downloadTaxas[2])/2

        elif lastBuffer > int(self.bufferSizesLimits[2]*self.confiabilidade):

            valorReferencia = self.downloadTaxas[1]

        elif lastBuffer > int(self.bufferSizesLimits[3]*self.confiabilidade):

            valorReferencia = int(self.downloadTaxas[0]+self.downloadTaxas[1])/2

        else:
            valorReferencia = self.downloadTaxas[0]


        melhorID = self.QiIdMaisProximo(valorReferencia)
        if melhorID < len(self.qi) and lastBuffer > 40 and abs(melhorID - len(self.qi)) <= 3:
            melhorID = len(self.qi) -1
        
        stringRewriteLog = 'Taxas de Download (min,avg,max):'+str(self.downloadTaxas)+'\n'
        stringRewriteLog += 'Melhor id:'+str(melhorID)+'\n'
        stringRewriteLog += 'Melhor bps:'+str(self.qi[melhorID])+'\n'
        stringRewriteLog += 'Buffer:'+str(lastBuffer)+'\n'
        stringRewriteLog += 'Confiabilidade: '+str(self.confiabilidade)+'\n'
        #self.rewriteLog(stringRewriteLog)

        return melhorID

    def QiIdMaisProximo(self, v):
        indice = 0
        for key, value in enumerate(self.qi):
            if key == 0:
                indice = key
            if abs(v-value) < abs(v-self.qi[indice]) and (v-value) > 0:
                indice = key
        return indice

    def setConfiabilidade(self):
        lastBuffer = self.whiteboard.get_playback_buffer_size()
        if len(lastBuffer) != 0:
            lastBuffer = lastBuffer[len(lastBuffer)-1][1]
        else:
            lastBuffer = 0

        minConfiabilidade = 2
        maxConfiabilidade = 1
        deltaTime = int(time()-self.lastRequestTime)
        deltaTimeUtilimoDecremento = time()-self.setLestDecrementoConfiabilidade
        if self.setLestDecrementoConfiabilidade == 0:
            deltaTimeUtilimoDecremento = 0

        if deltaTimeUtilimoDecremento > 8 or lastBuffer > 25:
            self.setLestDecrementoConfiabilidade = 0
            self.confiabilidade = maxConfiabilidade
            self.qtdPactosAnalisados = 10 #fase de teste

        if deltaTime >= 2 or lastBuffer <= 4:
            self.setLestDecrementoConfiabilidade = time()
            self.confiabilidade += deltaTime/10
            self.qtdPactosAnalisados = 7 #fase de teste

        if self.confiabilidade > minConfiabilidade:
            self.confiabilidade = minConfiabilidade

        if self.confiabilidade < maxConfiabilidade:
            self.confiabilidade = maxConfiabilidade
                
            