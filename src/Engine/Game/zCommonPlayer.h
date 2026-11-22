#ifndef ZCOMMONPLAYER_H
#define ZCOMMONPLAYER_H

#include "zPlayer.h"

#if GAME == RAT
struct xEnv;
struct xHierarchyBoundInitData;
struct zSurfAssetIN;
#else
#define MAX_EXP_POINTS 27500
#endif

enum zCommonPlayerUpgradeType
{
    ezCommonPlayerUpgradeType_Melee,
    ezCommonPlayerUpgradeType_AirMelee,
    ezCommonPlayerUpgradeType_Distance,
    ezCommonPlayerUpgradeType_Health,
    ezCommonPlayerUpgradeType_NukeCnt,
    ezCommonPlayerUpgradeType_Count
};

enum zCommonPlayerUpgradeLevel
{
    ezCommonPlayerUpgradeLevel_Normal,
    ezCommonPlayerUpgradeLevel_Level1,
    ezCommonPlayerUpgradeLevel_Level2,
    ezCommonPlayerUpgradeLevel_Count
};

#if GAME == RAT
struct zCommonPlayer : zPlayer
{
    virtual S32 EnvCollision(xSweptSphere* sphere, xEnv*);
    virtual void BreakGrab();
    virtual void BeforeAnimMatrices(xAnimPlay*, xQuat*, xVec3*, S32);
    virtual void LoadUpgrades();
    virtual U8 DoCriticalCollisionCheck() const;
    virtual xHierarchyBoundInitData* GetHierarchyBoundInitData() const;
    virtual F32 GetHierarchyMasterRadius() const;
    virtual void AbsControl(F32 x, F32 z, F32 dt);
    virtual void Rumble(U32 rumbleType);
    virtual void SetupRumbles();
    virtual void HandleFootstepCustom(zSurfAssetIN*);
    virtual void SavedFriend();
    virtual void SetUpgrade(zCommonPlayerUpgradeType forThisType, zCommonPlayerUpgradeLevel level);

    zCommonPlayerUpgradeLevel GetUpgradeLevel(zCommonPlayerUpgradeType forThisType);
};
#else
class zCommonPlayer : public zPlayer
{
public:
    void GetBonePos(xVec3* result, S32 index, const xVec3* offset, xMat4x3* matArray);
    void GetBoneMat(xMat4x3* mat, S32 index, xMat4x3* boneMats);
    zCommonPlayer();
    S32 GetAvailableUpgradePoints();

    virtual void Init(xEntAsset* asset);
    virtual void BoundUpdate(xVec3* _pos);
    virtual bool AllowInteraction(zInteraction*);
    virtual void AttackHit(bool);
    virtual void BeginUpdate(F32 dt);
    virtual void Update(F32 dt);
    virtual void EndUpdate(F32 dt);
    virtual void Move(xScene* s, F32 dt, xEntFrame* frame);
    virtual void Render();
    virtual void HandleEvent(xBase* from, U32 toEvent, const F32* toParam, xBase* toParamWidget, U32 toParamWidgetID);
    virtual void Reset();
    virtual bool IsDead() const;
    virtual void Exit();
    virtual void Save(xSerial* serial);
    virtual void Load(xSerial* serial);
    virtual bool Damage(const zCombatDamageInfo& damageInfo);
    virtual void PostRenderCleanup();
    virtual void RenderCustomUI();
    virtual bool CanTakeDamage() const;
    virtual void GiveHealth(S32 hitPoints, bool from_pickup);
    virtual void ResetHealth();
    virtual bool NeedsHealth() const;
    virtual bool IsVisible() const;
    virtual xVec3 get_target();
    virtual void EnemyKilled(zNPC::zNPCCommon* npc);
    virtual void ParseIni();
    virtual void AddStates(xAnimTable* table);
    virtual void AddTransitions(xAnimTable*);
    virtual bool CollisionResponse(const xVec3& currentDir, const SphereCollisionResults& sceneCollide, xVec3& responseDpos);
    virtual void RegisterCollision(const SphereCollisionResults& sceneCollide);
    virtual bool StayOnGround();
    virtual void DefaultMove(xScene* s, F32 dt, xEntFrame* frame);
    virtual void DefaultBeginUpdate(F32 dt);
    virtual void DefaultEndUpdate(F32 dt);
    virtual bool DefaultCollisionResponse(const xVec3& current_dir, const SphereCollisionResults& scene_collide, xVec3& response_dpos);
    virtual void InitActions() = 0;

protected:
    zPlayerActionManager actionManager;

private:
    U8 unkE3C[0x4F4];
};
#endif

#endif
