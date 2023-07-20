from random import random

pos: float = 0.0


def step():
    global pos
    pos += 2.0 * random() - 1.0


def get_pos():
    return pos


def set_pos(_val: float):
    global pos
    pos = _val


if __name__ == '__main__':
    i = 0
    while i < 100:
        print(i, get_pos())
        step()
        i += 1
    print(i, get_pos())
