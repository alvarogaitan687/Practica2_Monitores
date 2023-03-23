"""

@author: Álvaro Gaitán Martín

"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 15
NPED = 5
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (0.5, 1) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.npedestrian = Value('i', 0)
        self.ncarN = Value('i', 0)
        self.ncarS = Value('i', 0)
        self.npedestrian_waiting = Value('i', 0)
        self.ncarN_waiting = Value('i', 0)
        self.ncarS_waiting = Value('i', 0)
        self.mutex = Lock()
        self.ok_pedestrian = Condition(self.mutex)
        self.ok_carN = Condition(self.mutex)
        self.ok_carS = Condition(self.mutex)
    
    def are_no_ped_carS(self):
        return self.npedestrian.value == 0 and self.ncarS.value == 0 
 
    def are_no_ped_carN(self):
        return self.npedestrian.value == 0 and self.ncarN.value == 0

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        if (direction == 0): #Norte
            self.ncarN_waiting.value += 1
            self.ok_carN.wait_for(self.are_no_ped_carS) 
            self.ncarN_waiting.value -= 1
            self.ncarN.value += 1
        else: #Sur
            self.ncarS_waiting.value += 1
            self.ok_carS.wait_for(self.are_no_ped_carN) 
            self.ncarS_waiting.value -= 1
            self.ncarS.value += 1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        if (direction == 0): #Norte
            self.ncarN.value -= 1
            if self.ncarN.value == 0:
                if self.ncarS_waiting.value > 0:
                    self.ok_carS.notify_all()  
                else:
                    self.ok_pedestrian.notify_all()  
        else: #Sur
            self.ncarS.value -= 1
            if self.ncarS.value == 0:
                if self.npedestrian_waiting.value > 0:
                    self.ok_pedestrian.notify_all() 
                else:
                    self.ok_carN.notify_all()
        self.mutex.release()
    
    def are_no_cars(self):
        return self.ncarN.value == 0 and self.ncarS.value == 0 
    
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.npedestrian_waiting.value += 1
        self.ok_pedestrian.wait_for(self.are_no_cars) 
        self.npedestrian_waiting.value -= 1
        self.npedestrian.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.npedestrian.value -= 1
        if self.npedestrian.value == 0:
            if self.ncarN_waiting.value > 0:
                self.ok_carN.notify_all()  
            else:
                self.ok_carS.notify_all()                
        self.mutex.release()

    def __repr__(self) -> str:
        return f"M<ncarN:{self.ncarN.value}, ncarN_w:{self.ncarN_waiting.value}, ncarS:{self.ncarS.value}, ncarS_w:{self.ncarS_waiting.value}, nped:{self.npedestrian.value}, nped_w:{self.npedestrian_waiting.value}>"

def delay_car_north() -> None:
    time.sleep(random.uniform(0.5,1))

def delay_car_south() -> None:
    time.sleep(random.uniform(0.5,1))

def delay_pedestrian() -> None:
    time.sleep(random.uniform(10,30))

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()