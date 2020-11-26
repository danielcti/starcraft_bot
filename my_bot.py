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

class BotDaGalera(BotAI):

    async def on_step(self, iteration):
        if (
            self.supply_left < 5
            and self.townhalls
            and self.supply_used >= 14
            and self.can_afford(UnitTypeId.SUPPLYDEPOT)
            and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 1
        ):
            workers: Units = self.workers.gathering
            # Caso exista algum operário
            if workers:
                worker: Unit = workers.furthest_to(workers.center)
                location: Point2 = await self.find_placement(UnitTypeId.SUPPLYDEPOT, worker.position, placement_step=3)
                # Se existir local disponível
                if location:
                    # Operário constrói os depos de supplies naquele exato local
                    worker.build(UnitTypeId.SUPPLYDEPOT, location)

         # Abaixe os depos após serem construidos
        for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
            
        # Suba os depois caso inimigos estejam por perto
        for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            for unit in self.enemy_units:
                if unit.distance_to(depo) < 15:
                    break
            else:
                depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        # Checa se os requisitos para construção do orbital são atendidos. Se sim, constrói o comando orbital
        orbital_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.ORBITALCOMMAND)
        if orbital_tech_requirement == 1:
            # Loopzão em cima dos centros de comando
            for cc in self.townhalls(UnitTypeId.COMMANDCENTER).idle:
                # Verifica se há 150 minerals para dar o upgrade para comando orbital
                if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                    cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)

        # Expande a base caso tenhamos 400 minerais e só existe menos que duas bases
        if (
            1 <= self.townhalls.amount < 2
            and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
            and self.can_afford(UnitTypeId.COMMANDCENTER)
        ):
            # Retorna a posição de onde será a construção da próxima futura base na expansão
            location: Point2 = await self.get_next_expansion()
            if location:
                # Designa-se o operário mais próximo para a construção do mesmo
                worker: Unit = self.select_build_worker(location)
                if worker and self.can_afford(UnitTypeId.COMMANDCENTER):
                    # Operário começa a construir o centro de comandos na localização previamente obtida
                    worker.build(UnitTypeId.COMMANDCENTER, location)

        # Verifica se os requisitos para construção das barracas são atendidos
        # Caso sim, constrói 3 barracas
        barracks_tech_requirement: float = self.tech_requirement_progress(UnitTypeId.BARRACKS)
        if (
            barracks_tech_requirement == 1
            and self.structures(UnitTypeId.BARRACKS).ready.amount + self.already_pending(UnitTypeId.BARRACKS) < 3
            and self.can_afford(UnitTypeId.BARRACKS)
        ):
            workers: Units = self.workers.gathering
            if (
                workers and self.townhalls
            ):  # Checa se existe mais de um 'nexus' já que o placement é focado na sua localização
                worker: Unit = workers.furthest_to(workers.center)
                # O placement_step serão os passos de distâncias entra as barracas
                location: Point2 = await self.find_placement(
                    UnitTypeId.BARRACKS, self.townhalls.random.position, placement_step=4
                )
                if location:
                    worker.build(UnitTypeId.BARRACKS, location)

        # Começa a construir as refinarias assim que as barracas estejam prontas, de preferência perto ou em cima do gás vespeno
        if (
            self.structures(UnitTypeId.BARRACKS).ready.amount + self.already_pending(UnitTypeId.BARRACKS) > 0
            and self.already_pending(UnitTypeId.REFINERY) < 1
        ):
            # Laço de iteração até que os townhalls ('nexus') estão prontos
            for th in self.townhalls.ready:
                # Faz uma busca a fim de achar os spots de gas vespeno
                vgs: Units = self.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if (await self.can_place(UnitTypeId.REFINERY, [vg.position]))[0] and self.can_afford(
                        UnitTypeId.REFINERY
                    ):
                        workers: Units = self.workers.gathering
                        if workers:  # Note que utilizaremos o mesmo operário da tarefa anterior
                            worker: Unit = workers.closest_to(vg)
                            # Detalhe que o target da refinaria deve ser o geyser de gás vespeno e não a sua posição
                            worker.build(UnitTypeId.REFINERY, vg)

                            break

        # Criação dos operários (SCVs)
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
                _townhall.train(UnitTypeId.SCV)


        #criando soldados
        for rax in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE):
                rax.train(UnitTypeId.MARINE)
        


        # Administrando a energia do comando orbital e enviando os MULES               
        for orbital_command in self.townhalls(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
                mineral_fields: Units = self.mineral_field.closer_than(10, orbital_command)
                if mineral_fields:
                    mineral_field: Unit = max(mineral_fields, key=lambda x: x.mineral_contents)
                    orbital_command(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mineral_field)


        # Envie workers que estão na mina para a refinaria
        if iteration % 25 == 0:
            await self.distribute_workers()
      


def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Terran, BotDaGalera()), Computer(Race.Zerg, Difficulty.Hard)],
        realtime=False)

if __name__ == "__main__":
    main()