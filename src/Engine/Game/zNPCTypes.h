#ifndef ZNPCTYPES_H
#define ZNPCTYPES_H

#include "types.h"

enum eNPCType
{
    eNPCType_None = -1,
    eNPCType_Unknown = -1,
    eNPCType_First = 0,
#if GAME == RAT
    eNPCType_SwarmMember = 0,
    eNPCType_Swarm_Owl,
    eNPCType_Swarm_Bug,
    eNPCType_Thief,
    eNPCType_Simpleton,
    eNPCType_Alarmer,
    eNPCType_Waiter,
    eNPCType_CMG_StirringPlayer,
    eNPCType_CMG_StirringRemy,
    eNPCType_CMG_LeftArm,
    eNPCType_CMG_RightArm,
    eNPCType_CMG_PourNSwirl,
    eNPCType_SpringBoard,
    eNPCType_ContextSensitive,
    eNPCType_AnimViewer,
    eNPCType_InstaKill,
#else
    eNPCType_Common = 0,
    eNPCType_Humanoid,
    eNPCType_Rat,
    eNPCType_Chicken,
    eNPCType_Driller,
    eNPCType_Shooter,
    eNPCType_Bomber,
    eNPCType_RobotTank,
    eNPCType_Enforcer,
    eNPCType_Scientist,
    eNPCType_BossUnderminerDrill,
    eNPCType_BossUnderminerUM,
#endif
    eNPCTypeCount,
    eNPCTypeForceInt = FORCEENUMSIZEINT
};

#endif
