import can

from can_env import bus_kwargs

# Vector settings come from the environment when launched by the backend,
# and fall back to the original hard-coded defaults when run by hand.
bus = can.Bus(**bus_kwargs())
