import sys, os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import sc2
from sc2 import Race, Difficulty, BotAI
from sc2.constants import *
from sc2.position import Point2
from sc2.unit import Unit
from sc2.player import Bot, Computer
from sc2.player import Human
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.units import Units

class ExplorationAgent(BotAI):

    def __init__(self):
        self.pylonList = []
        self.enemy_location = None
        self.explorer_list = []


    async def on_step(self, iteration):
        
        if iteration == 0:
            print(f"Enemy Position -> {self.enemy_start_locations}")
            
            for _ in range(len(self.enemy_start_locations)):
                self.explorer_list.append(None)

            # Procura onde o inimigo nasceu
            await self.find_enemy_start_locations()

        self.trainSCV()
        
        
    async def find_enemy_start_locations(self):
        '''
            Procura onde é local de nascimento do inimigo
            e manda um CSV ir até lá explorar
        '''
        for i in range(len(self.enemy_start_locations)):
            location = self.enemy_start_locations[i]
            explorer = self.workers.random_or(None)
            if explorer:
                self.explorer_list[i] = explorer
                print(f"Sending a CSV to enemy's location")
                explorer.move(location)
            
    def trainSCV(self):
        if (
            self.can_afford(UnitTypeId.SCV)
            and self.supply_left > 0
            and self.supply_workers < 22
            and (
                self.structures(UnitTypeId.BARRACKS).ready.amount < 1
                and self.townhalls(UnitTypeId.COMMANDCENTER).idle
                or self.townhalls(UnitTypeId.ORBITALCOMMAND).idle
            )
        ):
            for _townhall in self.townhalls.idle:
                print(f"Train SCV")
                _townhall.train(UnitTypeId.SCV)
        
        

def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Terran, ExplorationAgent()), Computer(Race.Zerg, Difficulty.Hard)],
        realtime=True)

if __name__ == "__main__":
    main()