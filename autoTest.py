import json
import os

class AutoTest:

    def __init__(self,arr):
        self.obj = {}
        self.arr = arr
        self.carregarObj()
        for v in self.arr:
            self.definirJson(v)

    def carregarObj(self):
        with open('./dash_client.json','r') as arquivo:
            self.obj = json.loads(''.join(arquivo.readlines()))
            

    def definirJson(self, sequence):
        self.obj["traffic_shaping_profile_sequence"] = sequence
        with open('./dash_client.json','w') as arquivo:
            arquivo.write(json.dumps(self.obj))
        os.mkdir('results')
        os.system('python3 main.py')
        os.rename('results','results'+self.obj["traffic_shaping_profile_sequence"])

AutoTest(['L','M','H','LM','LMH','HMHLMHHMLH'])