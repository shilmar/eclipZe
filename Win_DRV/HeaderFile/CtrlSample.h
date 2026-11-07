//================================================================================================
// Copyright Nikon Corporation - All rights reserved
//
// View this file in a non-proportional font, tabs = 3
//================================================================================================

#ifndef _CTRLSAMPLE_		// We only want to be included once
#define _CTRLSAMPLE_

#include "Maid3.h"
#include "Maid3d1.h"

#define PERFORMANCECHECK
#include <chrono>

extern LPMAIDEntryPointProc	g_pMAIDEntryPoint ;
extern LPMAIDInitializeSDKProc g_pMAIDInitializeSDK ;
extern LPMAIDFreeSDKProc g_pMAIDFreeSDK ;
extern LPMAIDConnectDeviceProc g_pMAIDConnectDevice ;
extern LPMAIDDisconnectDeviceProc g_pMAIDDisconnectDevice ;
extern LPMAIDStartLiveView g_pMAIDStartLiveView ;
extern LPMAIDStopLiveView g_pMAIDStopLiveView ;
extern LPMAIDGetLiveViewStatus g_pMAIDGetLiveViewStatus ;
extern LPMAIDGetLoggingLevel g_pMAIDGetLoggingLevel ;
extern LPMAIDSetLoggingLevel g_pMAIDSetLoggingLevel ;
extern LPMAIDStartShooting g_pMAIDStartShooting ;
extern LPMAIDGetShootingStatus g_pMAIDGetShootingStatus ;
extern LPMAIDGetRemainingShootCount g_pMAIDGetRemainingShootCount ;
extern LPMAIDCancelShooting g_pMAIDCancelShooting ;
extern LPMAIDGetCapability g_pMAIDGetCapability ;
extern LPMAIDSetCapability g_pMAIDSetCapability ;
extern LPMAIDEnumCapabilities g_pMAIDEnumCapabilities ;
extern LPMAIDEnumDevices g_pMAIDEnumDevices ;
extern LPMAIDStartMovieRecording g_pMAIDStartMovieRecording ;
extern LPMAIDStopMovieRecording g_pMAIDStopMovieRecording ;
extern LPMAIDStartOperation g_pMAIDStartOperation ;
extern LPNkMAIDEnumDevices pDeviceList ;
extern LPMAIDSetImageVideoSavePath g_pMAIDSetImageVideoSavePath;

extern HINSTANCE	g_hInstModule;

extern LPNkMAIDEnumCapInfo pEnumCapInfo;

extern std::mutex device_list_lock;
extern std::mutex m_capability_list_lock;

typedef struct tagRefObj
{
	LPNkMAIDObject	pObject;
	SLONG lMyID;
	LPVOID pRefParent;
	ULONG ulChildCount;
	LPVOID pRefChildArray;
	ULONG ulCapCount;
	LPNkMAIDCapInfo pCapArray;
} RefObj, *LPRefObj;


//void	InitRefObj(LPRefObj pRef);
BOOL	Load_Module(const char *Path);
BOOL	SourceCommandLoop( ULONG ulSrcID);
BOOL	SetUpCamera1();
BOOL	SetUpCamera2();
BOOL	SetMovieMenu();
BOOL	SetShootingMenu();
BOOL	CheckCapabilityupdated(ULONG ulCapID, eNkMAIDCapOperations operationDesc);
BOOL	SetLiveView();
BOOL	SetCustomSettings();
BOOL	SetSBMenu();
void	CompProc(NKREF refComplete, NKERROR nResult);
BOOL	SetBoolCapability( ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL    SetStringCapability( ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	SetAcceptDiskAcquisition();
BOOL	SetPointCapability(ULONG ulCapID);
BOOL	SetIntegerCapability( ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	SetUnsignedIntCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	GetUnsignedIntCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	SetEnumCapability( ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	SetFloatCapability( ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	GetIntegerCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL	GetUnsignedIntCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType);
BOOL    CheckCapability(ULONG ulCapID, eNkMAIDCapOperations operationDesc);
BOOL	SetRangeCapability(ULONG ulCapID);
char*	GetUnsignedString(ULONG ulCapID, ULONG ulValue, char *psString);
void    SetUnsignedString(ULONG ulCapID);
BOOL	CaptureAsync();
BOOL	CaptureSync();
BOOL	CaptureAFAsync();
BOOL	CaptureAFSync();
bool	printEnumCapArrayValues(ULONG ulCapID, NkMAIDEnum stEnum);
BOOL	AFSettings();
BOOL	GetCapabilityType(ULONG ulCapID, ULONG &pCapType);
#ifdef PERFORMANCECHECK
BOOL testMultipleSingleShooting(ULONG ulCount,int choice = 2);
#endif
BOOL    IsCapabilityAvailable(ULONG ulCapID);
BOOL	GetSetPortraitImpressionBalanceDataSet();
BOOL	GetSetPowerZoomDrive();
BOOL	GetSetSpecialShootingSettingInfo();
BOOL	GetSetStorageIDS(LPNkMAIDStorageIDSList	pStorageIds);
BOOL	GetSetStorageInfoDataSet();
BOOL	InitialRegistrationPictureControlData();
BOOL	GetPictureControlData();

void	CALLPASCAL CALLBACK SrcEventProc(NKREF refProc, ULONG ulEvent, NKPARAM data);
ULONG	CALLPASCAL CALLBACK UIRequestProc(NKREF ref, LPNkMAIDUIRequestInfo pUIRequest);
void	CALLPASCAL CALLBACK ProgressProc(ULONG ulCommand, ULONG ulParam, NKREF refProc, ULONG ulDone, ULONG ulTotal);
NKERROR CALLPASCAL CALLBACK DataProc(NKREF ref, LPVOID pInfo, LPVOID pData);
NKERROR CALLPASCAL CALLBACK LVDataProc(NKREF refProc, LPNkMAIDLiveViewData pstLiveViewData);
void*	CALLPASCAL CALLBACK AllocateMemory(size_t len);
void	CALLPASCAL CALLBACK FreeMemory(void* pMem);
void	freeByDataType(void*, eNkMAIDDataType type);
void	PERROR(NKERROR lerror);

BOOL	GetSBAttrDesc();
BOOL	GetSBAttrValue();
BOOL	GetSBGroupAttrDesc();
BOOL	GetSBGroupAttrValue();
BOOL	StartTestFlash();
#endif
