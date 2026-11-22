#include "xCommon.h"
#include "zPlayerContainer.h"

#if GAME == ROTU
#include "zMrIncrediblePlayer.h"
#include "zFrozonePlayer.h"

namespace {

zFrozonePlayer frozone;
zMrIncrediblePlayer mrI;

}

zPlayerContainer::zPlayerContainer()
{
    playerArray[0] = &mrI;
    playerArray[1] = &frozone;
}
#endif

bool zPlayerContainer::IsPlayer(xEnt* ptr)
{
#if GAME == RAT
    for (S32 i = 0; i < numPlayers; i++) {
        if ((xEnt*)playerArray[i] == ptr)
            return true;
    }
#else
    for (S32 i = 0; i < 2; i++) {
        if (playerArray[i] == ptr)
            return true;
    }
#endif
    return false;
}
