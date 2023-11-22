from RandomWalkerFactory import random_walker_simservice
# Create ten simulators
proxies = [random_walker_simservice() for _ in range(10)]
# Do startup
for proxy in proxies:
    proxy.run()
    proxy.init()
    proxy.start()
# Simulate for 100 steps
for _ in range(100):
    for proxy in proxies:
        proxy.step()
        # Impose periodic boundary conditions on a domain [-1, 1]
        pos = proxy.get_pos()
        if pos < -1.0:
            proxy.set_pos(pos + 2.0)
        elif pos > 1.0:
            proxy.set_pos(pos - 2.0)
