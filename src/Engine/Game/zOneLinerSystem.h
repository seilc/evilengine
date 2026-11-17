#ifndef ZONELINERSYSTEM_H
#define ZONELINERSYSTEM_H

struct zPlayer;

enum zOneLinerTypes
{
#if GAME == ROTU
    zOLT_FreezeObject = 49,
    zOLT_ShatterObject = 51,
    zOLT_Total = 55
#endif
};

void zOneLinerSystemSetup();
void zOneLinerSystemReset();
void zOneLinerSystemPlay(zPlayer* player, zOneLinerTypes type);

#endif
