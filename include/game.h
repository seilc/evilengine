#ifndef GAME_H
#define GAME_H

// The games in release order. configure.py passes -DGAME=<name> per version; use them only in GAME comparisons
// (`#if GAME == ROTU`, `#if GAME >= TSSM`): a bare `#if ROTU` is true for every game but N100F.
#define N100F 0
#define BFBB 1
#define TSSM 2
#define INCREDIBLES 3
#define ROTU 4
#define RAT 5

#endif
