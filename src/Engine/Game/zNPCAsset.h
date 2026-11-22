#ifndef ZNPCASSET_H
#define ZNPCASSET_H

#include "xDynAsset.h"
#include "xEntAsset.h"

struct zNPCAssetRATS : xDynAsset
{
    xEntAsset ent_asset;
    U32 lightKitID;
    U32 npcWalls;
    U32 npcPerception;
    F32 updateDistance;
    U32 flags;
};

bool zNPCAsset_IsNPC(const xDynAsset& asset);

#if GAME != RAT
struct zNPCAsset : xDynAsset
{
    xEntAsset ent_asset;
    U32 navigation_mesh_id;
    U32 npcFlags;
    U32 respawnCounterID;
    U32 settingsHashID;
    U32 interestPointerGroupID;
    U32 lightKitID;
};
#endif

#endif
