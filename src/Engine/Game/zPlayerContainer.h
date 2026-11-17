#ifndef ZPLAYERCONTAINER_H
#define ZPLAYERCONTAINER_H

#include "xDebug.h"
#include "xEnt.h"

struct zPlayer;

#if GAME == RAT
#define MAX_PLAYERS_PER_SCENE 4
#endif

class zPlayerContainer
{
public:
#if GAME != RAT
    zPlayerContainer();
#endif

    zPlayer* operator[](S32 index)
    {
#if GAME == RAT
        xASSERT_L(23, index >= 0 && index < numPlayers);
#endif
        return playerArray[index];
    }

#if GAME == RAT
    S32 size() { return numPlayers; }
#else
    S32 size() { return 2; }
#endif
    bool IsPlayer(xEnt* ptr);

#if GAME == RAT
    void PushBack(zPlayer* player)
    {
        xASSERT_FMT_L(39, numPlayers < MAX_PLAYERS_PER_SCENE, "You can only have %i players in the scene and you are trying to add more", MAX_PLAYERS_PER_SCENE);
        playerArray[numPlayers] = player;
        numPlayers++;
    }
#endif

private:
#if GAME == RAT
    zPlayer* playerArray[MAX_PLAYERS_PER_SCENE];
    S32 numPlayers;
#else
    zPlayer* playerArray[2];
#endif
};

#endif
