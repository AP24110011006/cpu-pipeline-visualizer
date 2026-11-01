# The Two Testing Bots

Requested by faculty: two automated bots that test the simulator. Both run from the terminal and from the
**Testing bots** tab of the app.

## Bot 1 - Test Bot (`bots/test_bot.py`)
*Scenario regression testing.* It runs 17 programs whose cycle counts were worked out by hand
(for example: the sample chain takes 11 cycles without forwarding and 7 with it) and checks total cycles,
stall counts, forwarding events, control penalties and final register values. It also feeds the parser
10 invalid programs and checks each one is rejected with a clear message.

```
python -m bots.test_bot
```

## Bot 2 - Verifier Bot (`bots/verifier_bot.py`)
*Differential testing.* It generates random programs (loads, stores, ALU ops, forward branches, jumps and
counted loops - always terminating), runs each on a simple non-pipelined **reference CPU**, then on the
pipeline in **8 configurations** (forwarding on/off x branch policy x register-write timing), and compares:

* final registers and memory, and number of executed instructions,
* structural rules: stage order IF>ID>EX>MEM>WB, one instruction per stage per cycle, in-order completion,
  cycles >= instructions + 4, forwarding never slower than no forwarding (straight-line code).

```
python -m bots.verifier_bot --programs 200 --seed 1
python -m bots                      # both bots
```

The Verifier Bot can also verify *your own loaded program* in all configurations (button in the app).

## Do the bots really find bugs?
Yes: `tests/test_bots.py` deliberately breaks the stall unit and asserts that **both** bots then report failures.
A bot that cannot fail is useless, so this "mutation test" is part of the suite.
